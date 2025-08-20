# S3-Backed Resume Storage Deployment Guide

## What We've Implemented

✅ **Code Changes Complete:**
- Added `boto3>=1.34.0` to requirements.txt
- Implemented `S3ResumeStorageService` in `app/services/resume_storage_service.py`
- Updated factory to read environment variables and switch between local/S3 storage
- Modified `main.py` to use `RESUME_STORAGE_TYPE` environment variable
- Added Terraform resources for S3 bucket, IAM policy, and environment variables
- Updated user data script to set S3 environment variables in production

## What You Need to Do Now

### Step 1: Configure Terraform Variables

Update your `terraform/terraform.tfvars` file with the new S3 bucket name:

```hcl
# Existing variables...
aws_region = "ap-south-1"
project_name = "cv-generator"
cloudflare_email = "your-email@example.com"
cloudflare_api_key = "your-api-key"
cloudflare_zone_name = "avantifellows.org"
domain = "cv-generator"
repo_url = "https://github.com/your-username/cv-generator.git"

# NEW: S3 Configuration
app_s3_bucket_name = "cv-generator-app-storage-unique-suffix"  # Must be globally unique
app_s3_prefix = "prod/"  # Optional: use "" for no prefix
```

**Important:** The S3 bucket name must be globally unique across all AWS accounts. Consider using a suffix like your organization name or random string.

### Step 2: Deploy Terraform Infrastructure

```bash
cd terraform

# Initialize (if not already done)
terraform init

# Plan the changes - you should see new S3 resources
terraform plan

# Apply the changes
terraform apply
```

**What this creates:**
- S3 bucket with versioning, encryption, and public access blocked
- IAM policy granting the EC2 instance access to the bucket
- Updates the systemd service with S3 environment variables

### Step 3: Deploy Application Code

Since you're on the `feature/edit-view-by-uuid` branch, you need to merge/push your S3 changes:

```bash
# Commit your S3 implementation
git add .
git commit -m "Implement S3-backed resume storage"

# Push to your branch (update the terraform repo_url to point to your branch)
git push origin feature/edit-view-by-uuid
```

**OR** merge to main and update `repo_url` in terraform.tfvars to point to main branch.

### Step 4: Update the EC2 Instance

After Terraform applies successfully:

```bash
# SSH into your instance
ssh -i ~/.ssh/AvantiFellows.pem ubuntu@<ELASTIC_IP>

# Switch to app user
sudo su - cvapp
cd /home/cvapp/app

# Pull latest changes
git pull origin feature/edit-view-by-uuid  # or main

# Install new dependencies
./venv/bin/pip install -r requirements.txt

# Exit back to ubuntu user
exit

# Restart the service to pick up new environment variables
sudo systemctl restart cv-generator

# Check service status
sudo systemctl status cv-generator
```

### Step 5: Verify S3 Storage is Working

1. **Check application logs:**
```bash
sudo journalctl -u cv-generator -f
```

2. **Test the application:**
- Visit your app: `https://cv-generator.avantifellows.org`
- Create a new resume (should see S3 logs)
- Save a draft (should see S3 PUT operations)

3. **Check S3 bucket:**
```bash
# List objects in your bucket
aws s3 ls s3://your-bucket-name/prod/resumes/
aws s3 ls s3://your-bucket-name/prod/metadata/
```

You should see JSON files with UUID names appearing in the `resumes/` prefix.

## Environment Variables Reference

### Production (automatically set by Terraform):
```bash
RESUME_STORAGE_TYPE=s3
S3_BUCKET_NAME=your-bucket-name
S3_PREFIX=prod/
AWS_REGION=ap-south-1
```

### Local Development Options:

**Option 1: Default (recommended for most development)**
```bash
# No environment variables needed - uses local files
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Option 2: Test S3 locally**
```bash
# Copy the example file
cp env.example .env

# Edit .env with your test bucket details:
RESUME_STORAGE_TYPE=s3
S3_BUCKET_NAME=your-test-bucket-name
S3_PREFIX=dev/
AWS_REGION=ap-south-1

# Ensure AWS credentials are configured
aws configure  # or set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

# Run the app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Note:** The app automatically detects if a `.env` file exists and loads it for local development. On the server, no `.env` file exists, so it uses the environment variables set by systemd.

## Troubleshooting

### Issue: App fails to start with S3 errors

**Check:**
1. Verify IAM role is attached: `aws sts get-caller-identity`
2. Test S3 access: `aws s3 ls s3://your-bucket-name/`
3. Check environment variables: `sudo systemctl show cv-generator | grep Environment`

**Common fixes:**
- Ensure bucket name in terraform.tfvars matches exactly
- Verify IAM policy was attached to EC2 role
- Check bucket exists in correct region

### Issue: "Bucket does not exist" error

**Fix:** Ensure `terraform apply` completed successfully and created the bucket.

### Issue: Access denied errors

**Fix:** Verify the IAM policy allows access to the correct bucket and prefixes.

### Issue: App still using local storage

**Fix:** Verify environment variables are set in systemd service:
```bash
sudo systemctl show cv-generator | grep Environment
```

## Migration from Local to S3 (Optional)

If you have existing local resume drafts you want to keep:

```bash
# On the EC2 instance
sudo su - cvapp
cd /home/cvapp/app

# Sync existing local drafts to S3
aws s3 sync resume_data/ s3://your-bucket-name/prod/resumes/ \
  --exclude "resume_metadata.json"

# Copy metadata file
aws s3 cp resume_data/resume_metadata.json \
  s3://your-bucket-name/prod/metadata/resume_metadata.json
```

## Testing Checklist

- [ ] Terraform apply successful
- [ ] S3 bucket created with correct permissions
- [ ] EC2 instance can access S3 bucket
- [ ] Application starts without errors
- [ ] Can create new resume (creates S3 object)
- [ ] Can save draft (updates S3 object)  
- [ ] Can view/edit existing resume (reads from S3)
- [ ] Can delete resume (removes S3 object)
- [ ] Local development still works with `RESUME_STORAGE_TYPE=local`

## What Happens Next

After successful deployment:
1. **All new resume drafts** will be stored in S3
2. **Local files in `resume_data/`** will no longer be used (but won't be deleted)
3. **The app will work identically** from user perspective
4. **Drafts persist** even if EC2 instance is replaced
5. **You can access drafts** directly via AWS CLI/Console if needed

## Rollback Plan

If issues occur, you can quickly rollback:

```bash
# SSH to instance
sudo su - cvapp

# Edit the systemd service to use local storage
sudo sed -i 's/RESUME_STORAGE_TYPE=s3/RESUME_STORAGE_TYPE=local/' /etc/systemd/system/cv-generator.service

# Restart service
sudo systemctl daemon-reload
sudo systemctl restart cv-generator
```

This switches back to local file storage immediately.
