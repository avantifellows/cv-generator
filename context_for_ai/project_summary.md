# CV Generator v2.0 - Complete Project Summary

## **Project Overview**

This is a **professional CV/Resume Generator web application** built with FastAPI that creates PDF and HTML resumes from user input. It features clean architecture, modern web technologies, and cloud deployment capabilities.

## **Core Architecture & Technology Stack**

### **Backend Framework**

- **FastAPI** - Modern Python web framework with automatic API documentation
- **Pydantic** - Data validation and serialization models
- **Jinja2** - Template rendering engine
- **Playwright** - High-quality PDF generation from HTML (recently migrated from xhtml2pdf)

### **Dependencies**

```text
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
jinja2==3.1.2
aiofiles==23.2.1
python-dotenv==1.0.0
playwright>=1.40.0
pydantic>=2.11.0
cryptography>=42.0.0
boto3>=1.34.0
```

Notes:
- Playwright requires a Chromium browser installation. For local dev run `playwright install chromium`; on servers, the provisioning script installs both browser and OS deps.

### **Frontend Libraries (CDN)**

- **Toastify.js** - Lightweight toast notifications for client-side validation feedback

## **Project Structure**

```text
cv-generator/
├── app/
│   ├── models/cv_data.py                   # Pydantic data models
│   ├── services/cv_service.py              # Business logic layer
│   ├── services/resume_storage_service.py  # Resume draft persistence service
│   └── core/                               # Exceptions, logging
├── static/                                  # Static assets (mounted at /static)
├── templates/
│   ├── root_choice.html                    # Root landing UI (continue or start new)
│   ├── form.html                           # Dynamic web form (UUID-aware)
│   ├── cv_template.html                    # Web display template (view and view-only modes)
│   └── cv_template_pdf.html                # PDF-optimized template
├── terraform/                              # AWS deployment infrastructure
├── main.py                                 # FastAPI application entry point
├── generated/                              # Output directory for CVs
└── test_data_structured.json               # Sample data
```

## **Key Features & Capabilities**

### **1. Clean Architecture Design**

- **Service Layer**: Business logic separated from API endpoints
- **Data Models**: Structured Pydantic models with validation
- **Error Handling**: Custom exceptions with proper logging
- **API Versioning**: RESTful endpoints with `/api/v1/` structure

### **2. Dynamic Form System**

- **Interactive Web Form**: Streamlined interface showing only Personal Info initially; all sections (including Professional Summary, Education, and Custom) added via unified "Add Section" button with section picker modal
- **Real-time Preview**: Live CV preview as you type
- **Auto-save Status Indicator**: Small banner under "Live Preview" that toggles between saved and unsaved states:
  - Saved: “Changes saved last at HH:MM:SS” with a green checkmark
  - Unsaved: “Unsaved changes present ... auto saving” with a subtle spinner
  - Hidden until the user makes their first change
- **Data Validation**: Client and server-side validation
- **Test Data Integration**: Pre-filled form for testing
- **Subtle Loading UX**:
  - Thin top-edge progress bar during async actions (autosave, copy/share, PDF download, homepage resume validation)
  - Buttons show tiny inline spinners and disable state to prevent spamming during operations
  - Minimal, non-blocking visuals that do not interrupt editing
  - Homepage continue flow validates a locally stored resume ID against the server before enabling the button
  - Local resume ID expires after ~7 days (time-based TTL in `localStorage`)

### **3. Professional CV Output**

- **Dual Formats**: HTML for web viewing + PDF for download
- **Smart Rendering**: Conditional sections (only shows filled content)
- **Professional Styling**: Clean, academic resume format
- **Optimized PDF**: A4 format with proper margins using Playwright
- **Font Customization**: End-user controls for heading/body font sizes, colors, and line-height

### **4. Data Management**

- **Structured Storage**: JSON format with metadata
- **UUID-based IDs**: Unique identifiers for each CV
- **Resume Storage Service**: S3-backed drafts in production; local JSON files in `resume_data/` for development. Metadata tracked via `metadata/resume_metadata.json` object in S3 (best-effort cache)
- **Generated CV assets**: HTML, display HTML, and JSON saved under `generated/` on the local filesystem
- **Client-side Persistence (localStorage)**: Stores the most recent `resume_id` to let users continue where they left off; cookies removed for simplicity
- **Legacy Support**: Backward compatibility with old data formats
- **Complete Workflow**: Form → Validation → Storage → Rendering → PDF
- **No Placeholder Defaults**: Empty fields remain empty across parsing, models, and templates (no auto-inserted dashes or dummy emails)
  
Storage separation:
- Resume drafts (in-progress data) live in the Resume Storage backend (S3 in production or local files in development).
- Generated CVs (finalized outputs) live under `generated/` as `{cv_id}.html`, `{cv_id}_display.html`, and `{cv_id}_data.json`.
  - The PDF is rendered on demand from the stored JSON each time, not persisted.

## **Core Workflow**

1. **User Input** → Dynamic web form with sections for:
   - Personal Information
   - Professional Summary (optional)
   - Education (multiple entries)
   - Work Experience
   - Achievements
   - Certifications
   - Publications
   - Internships
   - Projects
   - Positions of Responsibility
   - Extracurricular Activities
   - Languages (simple list)
   - Technical Skills (categorized)

2. **Data Processing** → Pydantic validation and structured storage
3. **Template Rendering** → Jinja2 templates for HTML output
4. **PDF Generation** → Playwright converts HTML to high-quality PDF
5. **File Management** → Organized storage with unique identifiers

## **API Endpoints**

### **Web Interface**

- `GET /` - Root landing UI that lets users continue the last resume (via localStorage) or start a new one; supports `?new=1` to force a fresh resume and `?resume_id={id}` to open a specific resume
- `GET /resume/` - Redirects to `/` to avoid 404 when missing an ID
- `GET /resume/{resume_id}` - Edit form for that resume (draft-aware)
- `POST /resume/{resume_id}/save` - Save draft data
- `GET /api/v1/resume/{resume_id}/exists` - Validate draft existence (used by homepage and form to resume safely)
- `GET /v/{token}` - View-only mode via tokenized link (no raw UUID in URL)
- `GET /resume/{resume_id}/view` - Legacy view URL (still supported)
- `GET /resume/test` - Loads the form with bundled `test_data_structured.json` (read-only save; behaves like S3-loaded data for UI)
- `GET /resume/test-minimal` - Loads the form with bundled `test_data_minimal.json` (read-only; minimal dataset to test sparse CV layout and section spacing)
- `GET /test` - Redirects to `/resume/test` (for backward compatibility)
- `GET /test/minimal` - Redirects to `/resume/test-minimal`
- `GET /test/pdf` - Generate a PDF for the bundled test data (direct download)
- `GET /test/minimal/pdf` - Generate a PDF for the bundled minimal test data (direct download)
- `POST /generate` - Generate CV from form data (supports legacy and dynamic formats; can direct-download PDF)
- `GET /cv/{cv_id}` - View generated CV with download button
- `GET /cv/{cv_id}/html` - Raw HTML CV
- `GET /cv/{cv_id}/pdf` - On-demand PDF generation via Playwright

  Notes:
  - The UI “Copy Share URL” action uses the server-provided tokenized link (`/v/{token}`).
  - The legacy `/resume/{resume_id}/share` endpoint has been removed; the server injects a `share_url` directly into `form.html`.
  - Direct PDF download is supported by including `download_pdf=true` in the form submission to `/generate`.
  - The tokenized view URL is deterministic and depends on the server key; rotating the key invalidates old share links.

### **REST API**

- `GET /api/v1/cvs` - List all CVs
- `GET /api/v1/cv/{cv_id}` - Get CV data
- `DELETE /api/v1/cv/{cv_id}` - Delete CV
- `GET /api/v1/resume/{resume_id}/exists` - Returns `{"exists": true}` for `'test'` and `'test-minimal'` to enable seamless demo/QA flows
- `GET /health` - Health check

## **Deployment Infrastructure**

### **AWS EC2 Deployment**

- **Terraform Configuration**: Infrastructure as Code with remote backend (S3 + DynamoDB locking)
- **EC2 Instance**: t3.small Ubuntu 22.04 LTS
- **Nginx Reverse Proxy**: HTTPS termination and HTTP→HTTPS redirect; reverse proxy to 127.0.0.1:8000
- **SystemD Service**: Application lifecycle management
- **Cloudflare DNS**: Custom domain management
- **SSL/TLS**: Let's Encrypt certificates with automatic renewal (certbot.timer)
- **Automated Setup**: Complete deployment with idempotent user data scripts

### **Key Infrastructure Components**

- **Security Group**: SSH (22), HTTP (80), HTTPS (443), FastAPI (8000)
- **Elastic IP**: Static IP address for the instance
- **IAM Role**: EC2 instance profile used by the app to access the S3 bucket for resume drafts (and available for future AWS services)
- **Remote Backend**: S3 state bucket with versioning + DynamoDB lock table
- **User Data Script**: Idempotent application setup on instance launch
- **SSL Certificate**: Automated Let's Encrypt certificate management
- **Security Headers**: HSTS, X-Frame-Options, X-Content-Type-Options, XSS protection
- **Conditional Nginx**: Starts in HTTP-only mode if no cert exists; Certbot then provisions a cert and updates Nginx to HTTPS with HTTP→HTTPS redirect
  
Provisioning highlights (user data):
- Installs Python 3.11, Node.js, Nginx, AWS CLI, and Playwright dependencies
- Creates a dedicated `cvapp` user and `venv`
- Configures a systemd service setting environment variables (`RESUME_STORAGE_TYPE`, `S3_BUCKET_NAME`, `S3_PREFIX`, `AWS_REGION`, `SHARE_TOKEN_KEY`)
- Configures Nginx with strict security headers and static asset caching
- Obtains and renews TLS certificates via Certbot

### **CI/CD (GitHub Actions)**

- Workflow path: `.github/workflows/terraform.yml`
- Triggers on pushes to `new-feature-branch` and manual runs (`workflow_dispatch`)
- Executes: checkout → setup Terraform (v1.10.5) → configure AWS → `terraform init` with S3 + DynamoDB backend from secrets → validate → fmt check → plan → apply
- If no infra changes are applied, the job reboots the EC2 instance to refresh the app; otherwise it waits for the instance to be healthy
- Required secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BACKEND_BUCKET`, `DYNAMODB_LOCK_TABLE`, `CLOUDFLARE_EMAIL`, `CLOUDFLARE_API_KEY`, `APP_S3_BUCKET_NAME`, `APP_S3_PREFIX`, `SHARE_TOKEN_KEY`
- Environment overrides: `TF_VAR_repo_url` (repo to deploy), `AWS_REGION` (defaults to `ap-south-1`)

## **Recent Technical Improvements**

- ✅ **UUID-based Resume Flow**: Create/edit/view via `/resume/{resume_id}` with shareable view-only link
- ✅ **Resume Storage Service**: Draft persistence in `resume_data/` with metadata tracking
- ✅ **PDF Library Migration**: Playwright for better quality (from xhtml2pdf)
- ✅ **Unified Test Data Flow**: Added `/resume/test` to load bundled structured data; `/test` now redirects; save is read-only; exists API returns true for `'test'`
- ✅ **Professional Summary**: Added optional summary section
- ✅ **Template Optimization**: Improved formatting and spacing
- ✅ **Dynamic Content**: Smart conditional rendering
- ✅ **Font Customization**: Title/body font sizes/colors and line-height
- ✅ **Clean Architecture**: Service layer and Pydantic models
- ✅ **SSL/HTTPS Implementation**: Let's Encrypt certificates with automatic renewal
- ✅ **Idempotent Deployment**: Safe multi-run user data scripts
- ✅ **Security Headers**: HSTS, X-Frame-Options, X-Content-Type-Options, XSS protection
- ✅ **Save-status UI**: Added saved/unsaved banner with timestamp, checkmark, and spinner under “Live Preview”
- ✅ **Removed Placeholder Dashes**: Eliminated auto-insertion of “—”/dummy email; models now default to empty strings and parsers preserve empties
- ✅ **S3-backed Resume Storage**: Draft persistence moved to S3 in production with environment-based switching; Terraform-managed bucket, encryption, and IAM
- ✅ **Subtle Loading UX**: Global top progress bar on form and landing pages; buttons show inline spinners and disable during autosave/copy/share/PDF generation; non-intrusive visuals
- ✅ **Tokenized Share Links**: Share URLs use `/v/{token}` derived from a server-side secret; raw UUIDs are never exposed in shared links
- ✅ **External Link Normalization**: Fixed GitHub/LinkedIn/project repo links to always open correctly (auto-prepend `https://`) across templates and live preview
- ✅ **Work Experience in Web View**: Restored the Work Experience section in `cv_template.html` so it appears in both web and PDF views
- ✅ **Test-mode Prepopulation**: `/resume/test` now pre-populates the form's Professional Summary and Work Experience sections in addition to other sections
- ✅ **Languages Section**: Added simple languages list section; users can add multiple languages they know without proficiency levels (displayed as bullet points)
 - ✅ **Section Spacing Control**: Added `section_spacing_multiplier` with UI in `form.html`, live preview support, and dynamic spacing in both web and PDF templates; added minimal dataset and routes to demo sparse CVs.
- ✅ **Section Entry Limits**: Increased max entries from 3 to 5 for Work Experience, Internships, Projects, and Positions of Responsibility. Added client-side validation using Toastify.js to show friendly toast notifications when users try to exceed section limits (5 entries for most sections, 10 for Languages).
- ✅ **Points Per Entry Limits**: Added validation to limit key points/responsibilities to 5 per entry in Work Experience, Internships, Projects, and Positions of Responsibility sections. Uses Toastify.js toast notifications.
- ✅ **Custom Sections**: Users can add custom sections via "Add Custom Section" button with two types:
  - **Default**: Like Work Experience/Projects - entries with title, subtitle, duration, and bullet points
  - **Tabular**: Like Education - a table format with user-defined column headers, ideal for Languages, Soft Skills, or simple lists
  - Custom sections are persisted and restored on page reload
  - Rendered in both live preview and PDF output using Jinja2 macros
- ✅ **Page Break Indicators**: Live preview now shows dotted red lines indicating where page breaks will occur in the PDF, empirically calibrated to 1300px usable height per page
- ✅ **Section Reordering**: Drag-and-drop UI above Personal Information allows users to reorder sections in the CV
  - Includes all built-in sections plus any custom sections added by the user
  - Section order is persisted and restored on page reload
  - PDF template uses Jinja2 macros to render sections in the user-specified order

## **Current Development Status**

### **Completed Features**

- Clean architecture with service layer
- Dynamic form with real-time preview
- High-quality PDF generation with Playwright
- Professional template design
- Languages section (simple list)
- AWS deployment infrastructure
- Comprehensive error handling and logging
- UUID-based resume creation/editing and view-only sharing
- Resume drafts persisted via `ResumeStorageService` (S3 in production; local in development)

### **Planned Enhancements** (from TODOs)

- AWS S3 integration for persistent storage of generated CVs
- Search functionality for generated CVs
- Enhanced user management

## **Data Structure Example**

The application uses structured JSON format:

```json
{
  "personal_info": {
    "full_name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "+1-555-0123"
  },
  "education": [{"qualification": "M.Tech", "institute": "Stanford"}],
  "achievements": [{"description": "Dean's List", "year": "2023"}],
  "internships": [{"company": "Google", "role": "SWE Intern"}],
  "languages": ["English", "Spanish"]
}
```

## **Template System**

### **Template Files**

- `root_choice.html` - Minimal root landing UI to continue or start new using localStorage
- `cv_template.html` - Web display with embedded CSS; supports view-only mode and font settings
- `cv_template_pdf.html` - PDF-optimized with specific styling for print and font settings
- `form.html` - Dynamic, UUID-aware form with JavaScript for adding/removing sections and draft-saving
  - Work Experience is shown in both `cv_template.html` and `cv_template_pdf.html`.
  - `root_redirect.html` - Simple JS-based redirect helper (retained for fallback; not used by current routes)

### **Template Features**

- **Conditional Rendering**: Only shows sections with actual content
- **Jinja2 Filters**: Smart filtering of empty entries
- **Responsive Design**: Works on desktop and mobile
- **Professional Styling**: Academic resume format with proper typography
- **Subtle Global Progress Bar**: 2px top-edge bar during async actions (enabled in `form.html` and `root_choice.html`)
- **Action Button Feedback**: Buttons disable and show tiny spinners during operations (copy, share, PDF)
- **Tokenized Share URL**: Form receives a precomputed `share_url` from the server; frontend never handles keys or encryption. Graceful fallback in the client uses the current URL when `share_url` is absent.
- **View-only Toast**: Minimal top-right toast on shared views linking back to the homepage; no resume ID is displayed
- **External Link Normalization**: GitHub, LinkedIn, and project repo links are automatically converted to absolute URLs with `https://` when missing, in both web/PDF templates and the live preview.
- **Section Spacing Control**: "Section Spacing" setting (in the "Edit Font and Spacing" panel) applies a multiplier to the base spacing (web: 30px, PDF: 8px) to make shorter CVs look fuller. Options: 1.0x to 3.0x at 0.25x intervals (default: 2.0x).
- **Section Limit Toasts**: Toastify.js-powered toast notifications appear when users try to add more entries than allowed (5 for most sections, 10 for Languages).
- **Custom Sections**: "Add Custom Section" button allows creating new sections of type Default (with title/subtitle/duration/points) or Tabular (with user-defined column headers). Both types render in live preview and PDF, with full persistence and restoration on page reload.
- **Page Break Indicators**: Live preview displays dashed red lines showing approximate page break positions, calibrated to 1300px usable height per page.
- **Section Reordering UI**: Drag-and-drop interface above Personal Information enables reordering all CV sections (built-in and custom). Order is persisted and reflected in both live preview and PDF output.

## **Service Layer Architecture**

### **CVService Class** (`app/services/cv_service.py`)

- `generate_cv(cv_data)` - Create new CV with UUID
- `get_cv_data(cv_id)` - Retrieve CV by ID
- `update_cv_data(cv_id, cv_data)` - Update existing CV
- `delete_cv(cv_id)` - Remove CV and files
- `list_cvs()` - Get all CVs with metadata
- `convert_legacy_data(form_data)` - Backward compatibility
  
Implementation notes:
- Data is saved as `{cv_id}_data.json`; HTML and a display-HTML variant (with a fixed-top download button) are written per CV.
- Delete removes the JSON and both HTML files for that `cv_id`.

### **ResumeStorageService** (`app/services/resume_storage_service.py`)

- `create_new_resume(initial_data=None, resume_id=None)` - Returns a new `resume_id`; optionally accepts a pre-defined `resume_id`
- `get_resume_data(resume_id)` - Retrieve draft data and status
- `update_resume_data(resume_id, data, is_completed=False)` - Save draft or mark completed
- `resume_exists(resume_id)` - Check for existence
- `list_resumes()` - List metadata from `resume_metadata.json`
- `delete_resume(resume_id)` - Remove draft and clean metadata
  
S3 backend specifics:
- Draft JSON objects are stored at `${S3_PREFIX}resumes/{resume_id}.json`.
- Metadata lives at `${S3_PREFIX}metadata/resume_metadata.json` with fields: `created_at`, `last_modified`, `is_completed`.
- Adaptive retries and timeouts are configured on the S3 client.
- A utility exists to clean up old, incomplete resumes (default 30 days) — not automatically invoked.

### **Data Models** (`app/models/cv_data.py`)

- `PersonalInfo` - Name, contact details, education
- `EducationEntry` - Qualification, institute, year, CGPA
- `AchievementEntry` - Description and year
- `CertificationEntry` - Description and year
- `PublicationEntry` - Description and year
- `InternshipEntry` - Company, role, duration, points
- `WorkExperienceEntry` - Company, position, duration, points
- `ProjectEntry` - Title, type, duration, points
- `PositionEntry` - Club, role, duration, points
- `TechnicalSkillsCategory` - Categorized skills (languages, web, DB, tools)
- `FontSettings` - Title/body sizes, colors, line-height
- `CustomSectionDefaultEntry` - Entry data for default-type custom sections (title, subtitle, duration, points)
- `CustomSection` - Custom section supporting both "default" and "tabular" types
- `CVData` - Complete CV structure with validation, including `section_order` and `custom_sections` fields
- `CVDocument` - CV data with metadata

  Model defaults and validation:
  - Fields default to empty strings instead of placeholder symbols
  - Validators trim whitespace but do not force placeholder values
  - Rendering logic only displays fields with actual content
  - Section caps: Education ≤5, Work Experience ≤5, Internships ≤5, Projects ≤5, Positions of Responsibility ≤5, Achievements/Certifications/Publications ≤5, Extracurricular ≤5, Languages ≤10, skills per category are bounded.
  - Points per entry caps: Key points/responsibilities limited to ≤5 per entry in Work Experience, Internships, Projects, and Positions of Responsibility.
  - Client-side validation enforces these limits with Toastify.js toast notifications when users try to exceed them.

### **ID Codec Utilities** (`app/core/id_codec.py`)

- `encode_share_token(resume_id)` - Deterministically maps UUID → short token (AES-128 ECB over a single 16-byte block, base64url without padding)
- `decode_share_token(token)` - Reverses token → UUID using server-side key
- Key via `SHARE_TOKEN_KEY` environment variable; no DB mapping needed
  - Development fallback uses a built-in key if `SHARE_TOKEN_KEY` (or `SECRET_KEY`) is not set. Set a strong, stable key in production.

## **Error Handling & Logging**

### **Custom Exceptions** (`app/core/exceptions.py`)

- `CVGenerationError` - PDF/HTML generation failures
- `CVNotFoundError` - CV retrieval failures
- `TemplateError` - Template rendering issues
- `PDFGenerationError` - Playwright PDF generation errors

### **Logging Configuration** (`app/core/logging.py`)

- Structured logging with different levels
- Comprehensive error tracking
- Debug information for development
- Production-ready logging format

## **Development Commands**

### **Setup and Installation**

```bash
# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### **Running the Application**

```bash
# Development mode with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
python main.py

# Access at http://localhost:8000
```

### **Testing**

```bash
# Test with pre-filled form (unified test route)
# Access http://localhost:8000/resume/test
# Note: Saving on /resume/test is read-only and will be acknowledged but not persisted

# Generate test PDF
# Access http://localhost:8000/test/pdf

# Health check
curl http://localhost:8000/health
```

## **Deployment Process**

### **Terraform Deployment**

```bash
# Configure variables
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit terraform.tfvars with your values

# Deploy infrastructure with SSL
cd terraform
terraform init
terraform plan
terraform apply
```

### **SSL Configuration**

- **Automatic Certificate Generation**: Let's Encrypt integration
- **HTTPS Enforcement**: All HTTP traffic redirects to HTTPS
- **Security Headers**: HSTS, X-Frame-Options, X-Content-Type-Options, XSS protection
- **Certificate Renewal**: Automated with systemd timers
- **Modern TLS**: TLS 1.2/1.3 with secure cipher suites

### **Manual Updates**

```bash
# SSH into instance
ssh -i ~/.ssh/AvantiFellows.pem ubuntu@<ELASTIC_IP>

# Update application (idempotent user data can also be re-run)
sudo su - cvapp
cd /home/cvapp/app
git pull origin new-feature-branch
./venv/bin/pip install -r requirements.txt
sudo systemctl restart cv-generator
```

## **File Organization**

### **Main Application Files**

- `main.py` - FastAPI application with all endpoints
- `requirements.txt` - Python dependencies
- `test_data_structured.json` - Sample CV data for testing

### **Configuration Files**

- `terraform/` - Complete AWS infrastructure setup
- `Dockerfile.backup` - Docker configuration (backup)
- Various TODO and documentation files

### **Generated Files**

- `generated/{cv_id}.html` - Web display version
- `generated/{cv_id}_display.html` - Version with download button
- `generated/{cv_id}_data.json` - Structured CV data with metadata

## **Configuration & Environment Variables**

- `RESUME_STORAGE_TYPE`: `local` (default) or `s3` to select resume draft storage backend
- `S3_BUCKET_NAME`: Required when `RESUME_STORAGE_TYPE=s3` (bucket for drafts/metadata)
- `S3_PREFIX`: Optional key prefix (e.g., `prod/`)
- `AWS_REGION`: AWS region for S3 operations
- `SHARE_TOKEN_KEY`: Secret used to derive the AES key for tokenized share links
- Local development loads `.env` automatically if present; on servers, variables are injected via systemd (see Terraform `user_data.sh`)
  - If `SHARE_TOKEN_KEY` is absent, a development fallback is used (do not rely on this in production)

## **Technical Notes**

### **PDF Generation**

- Uses Playwright with Chromium for high-quality output
- A4 format with optimized margins
- Handles complex CSS layouts correctly
- Supports background colors and modern styling
- Honors user font settings (sizes, colors, line-height)

### **Form Handling**

- Dynamic JavaScript for adding/removing sections
- Real-time preview with live updates
- Auto-save with visual status (saved/unsaved) and last-saved timestamp
- UUID-based routing and draft save via `/resume/{resume_id}/save`
- Resume existence pre-check via `GET /api/v1/resume/{resume_id}/exists` when continuing from localStorage
- Supports both legacy flat format and new structured format
- Comprehensive client-side validation
- Section entry limits enforced client-side with Toastify.js toast notifications (max 5 entries for most sections, 10 for Languages)
- Subtle loading indicators (top progress bar + button spinners/disable) to avoid spamming actions and provide feedback
  - Share button copies the tokenized URL immediately for snappy UX, then autosaves in the background
  - Resume continuation flow: localStorage TTL ~7 days, server existence pre-check before enabling "Continue"

### **Security Considerations**

- ✅ **Input validation**: Pydantic models with comprehensive validation
- ✅ **Error handling**: Proper error messages without internal exposure
- ✅ **File security**: File I/O is confined to app-controlled paths; no user-supplied filenames
- ✅ **SSL/TLS encryption**: HTTPS with Let's Encrypt certificates
- ✅ **Security headers**: HSTS, X-Frame-Options, XSS protection
- ✅ **HTTPS enforcement**: All traffic encrypted with automatic redirects

## **Legacy and Miscellaneous Artifacts**

- `html_template.html`: Older, unused HTML template retained for reference.
- `templates/root_redirect.html`: Legacy redirect helper (not referenced by current routes).
- `Dockerfile.backup`: Backup Docker configuration.
- `aws-lambda-rie`, `cv-generator-lambda.zip`, `source.zip`: Artifacts from prior Lambda experimentation; not part of the current EC2 deployment path.

This is a **well-architected, production-ready application** that demonstrates modern Python web development practices with clean code, proper separation of concerns, comprehensive deployment automation, and enterprise-grade security. The project successfully generates professional academic resumes with a focus on user experience, code quality, and security best practices. 

## **Update Log**

- 2025-11-09 00:00 UTC: Synced with repo; added CI/CD section; verified Terraform, user data, endpoints, and dependencies.
- 2025-11-09: Updated docs to reflect fixes — external link normalization across templates and live preview; Work Experience now included in `cv_template.html`; `/resume/test` pre-populates Summary and Work Experience.
- 2025-11-09: Added Languages section as a simple list (like extracurricular activities); users can enter multiple languages they know; displayed as bullet points between Extracurricular Activities and Technical Skills sections.
- 2025-11-09: Introduced Section Spacing control (multiplier) and added minimal test dataset with routes: `/resume/test-minimal`, `/test/minimal`, `/test/minimal/pdf`. `exists` API recognizes `'test-minimal'`.
- 2025-11-28: Increased section entry limits from 3 to 5 for Work Experience, Internships, Projects, and Positions of Responsibility. Added client-side validation with Toastify.js toast notifications to all sections (Education, Work Experience, Internships, Projects, Positions, Achievements, Certifications, Publications, Extracurricular Activities, Languages) to prevent exceeding limits with user-friendly error messages.
- 2025-11-29: Added points-per-entry validation (max 5 key points/responsibilities) in Work Experience, Internships, Projects, and Positions of Responsibility sections with Toastify.js toast notifications.
- 2025-05-23: Implemented full Custom Sections and Section Reordering support:
  - Custom sections (Default and Tabular types) now persist and restore on page reload
  - Section order persists and restores on page reload
  - PDF template uses Jinja2 macros to render sections in user-specified order
  - Added `CustomSectionDefaultEntry` and `CustomSection` Pydantic models
  - Added `section_order` and `custom_sections` fields to CVData model
  - Updated form parsing to handle `section_order` and `custom_sections_json` fields
  - Page break indicators calibrated to 1300px usable height per page
- 2026-05-23: Form interface and UX improvements:
  - Streamlined form interface: Only Personal Information section shown initially
  - Unified section management: Removed separate "Add Custom Section" button; all sections (including custom) are now added via single "Add Section" button
  - Section picker modal includes (in order): Professional Summary, Education, Custom Section, Work Experience, Internships, Key Projects, Positions of Responsibility, Extracurricular Activities, Achievements, Certifications, Publications, Languages, Technical Skills
  - Section reorder list now only shows visible/active sections
  - Updated defaults: Font size 14px (title and body), line height 1.5, section spacing 2.0x
  - Section spacing options now range from 1.0x to 3.0x at 0.25x intervals without descriptive text
  - Fixed Remove button: All remove functions (removeEntry, removePoint, removeActivity, removeLanguage, removeSkill, removeSection) now properly clear data and refresh the live preview