# CV Generator

A FastAPI application for creating professional CVs/resumes with HTML and high-quality PDF output. Built with Pydantic models, a clean service layer, and Jinja2 templates. Local-first by default, with optional S3-backed draft storage in production.

## What you can do

- Edit resumes in a dynamic web form with autosave
- View generated CVs in the browser (HTML)
- Download high-quality PDFs (Playwright + Chromium)
- Share view-only links using short, tokenized URLs

## Quick start (local)

### Prerequisites

- Python 3.11
- macOS/Linux (Windows via WSL recommended)
- No Node.js required; Playwright Python will download Chromium

### Setup

```bash
# Clone
git clone <your-fork-or-repo-url>
cd cv-generator

# Create and activate a virtualenv
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser (required for PDF)
playwright install chromium

# (Optional) Configure environment
cp env.example .env
# Then edit .env as needed (see Configuration below)
```

### Run

```bash
# Development mode (auto-reload)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# or
python main.py
```

Open [http://localhost:8000](http://localhost:8000)

### Try it out

```bash
# Health check
curl http://localhost:8000/health

# Prefilled form + sample PDF
# Visit in the browser:
#  - http://localhost:8000/test
#  - http://localhost:8000/test/pdf (downloads a PDF)
```

## Configuration

The app reads environment variables (from your shell or a `.env` file).

- `RESUME_STORAGE_TYPE`: `local` (default) or `s3`
- `S3_BUCKET_NAME`: Required if `RESUME_STORAGE_TYPE=s3`
- `S3_PREFIX`: Optional S3 key prefix (e.g., `dev/`)
- `AWS_REGION`: AWS region for S3 operations
- `SHARE_TOKEN_KEY`: Secret used to derive tokenized share links (set a stable key for consistent links)

Example `.env` for local development:

```env
RESUME_STORAGE_TYPE=local
# Optional but recommended for stable share links in dev
SHARE_TOKEN_KEY=change-me-dev-secret

# Only needed if using S3
# S3_BUCKET_NAME=your-bucket
# S3_PREFIX=dev/
# AWS_REGION=ap-south-1
```

## Common workflows

- Start new or continue a resume at `/` or `/resume/{resume_id}` (autosave enabled)
- Copy a shareable, view-only link (tokenized; no raw UUID in URL)
- Generate and download PDFs from the CV page or via `/cv/{cv_id}/pdf`

Generated assets are written under `generated/`:

- `{cv_id}.html`
- `{cv_id}_display.html` (web view with a download button)
- `{cv_id}_data.json` (rendered data snapshot)

Draft resumes (in-progress data):

- Local: JSON files in `resume_data/` with simple metadata
- S3 (when enabled): `${S3_PREFIX}resumes/{resume_id}.json` and `${S3_PREFIX}metadata/resume_metadata.json`

## Minimal API map

- Web UI
  - `GET /` (root landing; continue or start new)
  - `GET /resume/{resume_id}` (edit form)
  - `POST /resume/{resume_id}/save` (save draft)
  - `GET /v/{token}` (view-only via tokenized link)
  - `GET /test`, `GET /test/pdf` (sample data + PDF)
- CV outputs
  - `GET /cv/{cv_id}` (view CV)
  - `GET /cv/{cv_id}/html` (raw HTML)
  - `GET /cv/{cv_id}/pdf` (on-demand PDF)
- REST
  - `GET /api/v1/cvs`, `GET /api/v1/cv/{cv_id}`, `DELETE /api/v1/cv/{cv_id}`
- Health
  - `GET /health`

## Project layout

```text
app/
  models/cv_data.py                 # Pydantic models
  services/cv_service.py            # CV business logic
  services/resume_storage_service.py# Draft persistence (local/S3)
  core/                             # Exceptions, logging, id codec
templates/                          # Jinja2 templates (web + PDF)
static/                             # Static assets
generated/                          # Output files (HTML + data)
main.py                             # FastAPI app entrypoint
```

## PDF generation notes

- Uses Playwright (Python) with Chromium for high-quality PDFs
- No Node.js required; the `playwright` CLI inside your venv installs browsers

If generating PDFs on Linux servers, install system deps first:

```bash
python -m playwright install-deps chromium
```

## Troubleshooting

- Playwright/Chromium not found:
  - Run `playwright install chromium` inside the active venv
- PDF output is blank or errors:
  - Reinstall browsers: `playwright install chromium`
  - On Linux, also run: `python -m playwright install-deps chromium`
- Port already in use:
  - Change `--port` or stop the conflicting process
- Share links change across restarts:
  - Set a stable `SHARE_TOKEN_KEY` in `.env`

## Deployment

Infrastructure-as-Code (Terraform) to AWS EC2 with Nginx and HTTPS is available under `terraform/`.

- See `terraform/README.md` for production deployment guidance.

## Contributing

1. Fork and create a feature branch
2. Follow the existing patterns (Pydantic models + service layer)
3. Add validation and error handling for new fields/endpoints
4. Update templates if you add new renderable fields
5. Open a PR with a clear description and testing notes

## License

This project is licensed under the MIT License. See `LICENSE` for details.
