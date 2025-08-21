# S3-backed Resume Storage Design & Implementation Plan

## Overview

This document proposes migrating resume draft persistence from local JSON files in `resume_data/` to Amazon S3. S3 will act as the source of truth (“database”) for all resume drafts keyed by UUID. We will keep the current web/API behaviors unchanged by introducing an S3-backed implementation of the existing `ResumeStorageService` interface.

## Goals

- Use S3 to store and retrieve resume drafts by UUID.
- Maintain the same user flows and endpoints; no API changes required.
- Keep local mode for development; enable S3 mode in production via configuration.
- Manage the S3 bucket and IAM through the existing Terraform setup.

## Non-Goals

- Moving generated CV HTML/PDF to S3 (can be a future enhancement).
- Adding user accounts or auth. The change is storage-only.

## Current State (Relevant Pieces)

- `ResumeStorageService` (local): stores drafts as `resume_data/{resume_id}.json` and tracks metadata in `resume_data/resume_metadata.json`.
- Endpoints using it:
  - `GET /resume/{resume_id}` (exists, load or create shell)
  - `POST /resume/{resume_id}/save` (update draft)
  - `GET /resume/{resume_id}/view` (view-only mode)
- Factory function `create_resume_storage_service(base_path, storage_type)` exists; `"s3"` branch is unimplemented.

## Proposed Architecture

- Implement `S3ResumeStorageService` with the same public methods as the local service.
- Switch via environment config (default `local`, prod uses `s3`).
- Store one JSON object per resume in S3; optionally maintain a compact metadata index for faster listing (best-effort cache).

### S3 Object Layout

- Bucket: managed by Terraform (private, versioned, encrypted, public access blocked).
- Optional prefix (environmental): e.g., `prod/`.
- Keys:
  - `resumes/{resume_id}.json` — full resume JSON: `{ resume_id, created_at, last_modified, data, is_completed }`.
  - `metadata/resume_metadata.json` — optional aggregate index for faster `list_resumes` (best effort; rebuildable).

### Service Behavior Mapping

- `create_new_resume(initial_data, resume_id)`: Generate or use provided UUID, write JSON to `resumes/{resume_id}.json`, update metadata index (if used).
- `resume_exists(resume_id)`: S3 `HEAD` on `resumes/{resume_id}.json`.
- `get_resume_data(resume_id)`: `GET` object and `json.loads`.
- `update_resume_data(resume_id, data, is_completed)`: `GET` -> mutate `last_modified`/`is_completed` -> `PUT` back; update index (if used).
- `delete_resume(resume_id)`: `DELETE` object; remove from index.
- `list_resumes()`: Prefer `ListObjectsV2` on `resumes/` and build a list (accurate, O(n)); fallback/use index if present for faster results.
- `cleanup_old_resumes(days_old)`: Use S3 `LastModified` as a quick filter; optionally `GET` JSON to confirm `is_completed` before deletion.

### Robustness

- Retries/Timeouts: `botocore.config.Config(retries={'max_attempts': 10, 'mode': 'adaptive'}, connect_timeout=5, read_timeout=20)`.
- Concurrency: Low contention; index updates are best-effort; source of truth is per-resume objects.
- Observability: Log bucket/key and request IDs where possible.

### Security

- Bucket private with block public access; TLS in transit; SSE-S3 (or SSE-KMS) at rest.
- IAM scoped to the application EC2 role:
  - `s3:ListBucket` on the bucket
  - `s3:GetObject|PutObject|DeleteObject` on `resumes/*` and `metadata/*`

## Configuration

Environment variables (read in `main.py`):

- `RESUME_STORAGE_TYPE` — `local` (default) or `s3`.
- `S3_BUCKET_NAME` — required in `s3` mode.
- `S3_PREFIX` — optional (e.g., `prod/`).
- `AWS_REGION` — optional; otherwise rely on instance metadata/role.

## Terraform Changes

Add a dedicated bucket and IAM permissions in `terraform/`:

1) Variables (in `variables.tf`):

```hcl
variable "app_s3_bucket_name" { type = string }
variable "app_s3_prefix" { type = string, default = "" }
```

2) Bucket (in `main.tf`):

```hcl
resource "aws_s3_bucket" "app_bucket" {
  bucket = var.app_s3_bucket_name
}

resource "aws_s3_bucket_versioning" "app_bucket" {
  bucket = aws_s3_bucket.app_bucket.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "app_bucket" {
  bucket = aws_s3_bucket.app_bucket.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_s3_bucket_public_access_block" "app_bucket" {
  bucket                  = aws_s3_bucket.app_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

3) IAM policy attachment (scope to bucket and prefixes) for existing EC2 role:

```hcl
data "aws_iam_policy_document" "app_s3_access" {
  statement {
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.app_bucket.arn]
  }

  statement {
    actions = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = [
      "${aws_s3_bucket.app_bucket.arn}/${var.app_s3_prefix}resumes/*",
      "${aws_s3_bucket.app_bucket.arn}/${var.app_s3_prefix}metadata/*"
    ]
  }
}

resource "aws_iam_policy" "app_s3_policy" {
  name   = "cv-generator-app-s3"
  policy = data.aws_iam_policy_document.app_s3_access.json
}

resource "aws_iam_role_policy_attachment" "ec2_app_s3" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.app_s3_policy.arn
}
```

4) Outputs (optional):

```hcl
output "app_s3_bucket_name" { value = aws_s3_bucket.app_bucket.bucket }
output "app_s3_bucket_arn"  { value = aws_s3_bucket.app_bucket.arn }
```

## Application Code Changes

1) Dependencies

Add to `requirements.txt`:

```
boto3>=1.34.0
```

2) Implement `S3ResumeStorageService` in `app/services/resume_storage_service.py`

- Mirror the local service’s public API: `create_new_resume`, `get_resume_data`, `update_resume_data`, `resume_exists`, `delete_resume`, `list_resumes`, `cleanup_old_resumes`.
- Helper methods to build keys: `_resume_key(resume_id)`, `_metadata_key()`.
- Initialize a boto3 S3 client with retry config and optional region.

3) Factory update

- Update `create_resume_storage_service(base_path, storage_type)` to return an instance of the S3 implementation when `storage_type == "s3"` using environment variables for bucket/prefix.

4) Initialization in `main.py`

- Read env vars and create the appropriate service:

```python
import os
from app.services.resume_storage_service import create_resume_storage_service

storage_type = os.getenv("RESUME_STORAGE_TYPE", "local")
resume_storage_service = create_resume_storage_service(
    BASE_PATH,
    storage_type,
)
```

If the S3 implementation needs bucket/prefix/region, wire them in the factory via env reads (to avoid touching `main.py` signature).

5) README update

- Document environment variables and Terraform steps for enabling S3 mode.

## Migration & Rollout

1) Deploy Terraform to create bucket and attach IAM policy.

2) One-time data push (optional, to keep existing drafts):

```bash
# Upload each local draft to S3 resumes prefix
aws s3 sync resume_data/ s3://$APP_S3_BUCKET/$APP_S3_PREFIX/resumes/ \
  --exclude "*" --include "*.json" --no-progress

# If keeping the metadata index
aws s3 cp resume_data/resume_metadata.json \
  s3://$APP_S3_BUCKET/$APP_S3_PREFIX/metadata/resume_metadata.json
```

3) Configure environment for the app (systemd or .env):

```bash
export RESUME_STORAGE_TYPE=s3
export S3_BUCKET_NAME=<your-bucket>
export S3_PREFIX=prod/
export AWS_REGION=ap-south-1
```

4) Restart the service and verify flows:

- Create a new resume, save, view, share.
- Confirm objects appear in S3 and are readable via the app.

## Testing Strategy

- Unit tests with `moto` to mock S3 covering: create, exists, get, update, delete, list, cleanup.
- Integration smoke tests running the app in S3 mode (with real or mocked credentials).
- Edge cases: non-existent IDs, large payloads, transient S3 errors (retry logic).

## Security & Compliance

- Encrypted at rest (SSE), TLS enforced in transit, public access blocked.
- Least-privilege IAM scoped to exact prefixes.
- Optionally enable S3 server access logs to a separate logging bucket.

## Future Enhancements

- Store generated CV HTML/PDF in S3 and serve via signed URLs or proxy.
- Replace metadata JSON with DynamoDB for scalable listings while continuing to store per-resume JSON in S3.
- Async S3 client (`aioboto3`) for non-blocking I/O under higher load.

## Implementation Checklist

- Terraform
  - [ ] Add bucket with versioning, SSE, public access block
  - [ ] Add IAM policy and attach to EC2 role
  - [ ] Add variables and outputs
- App
  - [ ] Add `boto3` to `requirements.txt`
  - [ ] Implement `S3ResumeStorageService`
  - [ ] Update factory to return local or S3 implementation
  - [ ] Read env vars in `main.py` (via factory) and initialize
  - [ ] Update README with configuration instructions
- Data (optional)
  - [ ] Sync existing local drafts to S3
- Tests
  - [ ] Unit tests for S3 implementation using `moto`
  - [ ] Integration smoke tests in S3 mode

## Acceptance Criteria

- With `RESUME_STORAGE_TYPE=s3`:
  - Creating, saving, viewing, deleting resumes works as before but persists in S3.
  - `list_resumes()` returns correct data via S3 listing or index.
  - Terraform provisions the bucket and IAM; the instance can access S3 via its role.
- With `RESUME_STORAGE_TYPE=local`:
  - Existing local behavior remains unchanged.


