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
```
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
jinja2==3.1.2
aiofiles==23.2.1
python-dotenv==1.0.0
playwright>=1.40.0
pydantic>=2.11.0
cryptography>=42.0.0
```

Additional production dependency:
```
boto3>=1.34.0
```

## **Project Structure**

```
cv-generator/
├── app/
│   ├── models/cv_data.py                   # Pydantic data models
│   ├── services/cv_service.py              # Business logic layer
│   ├── services/resume_storage_service.py  # Resume draft persistence service
│   └── core/                               # Exceptions, logging
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
- **Interactive Web Form**: Add/remove sections dynamically
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
- **Client-side Persistence (localStorage)**: Stores the most recent `resume_id` to let users continue where they left off; cookies removed for simplicity
- **Legacy Support**: Backward compatibility with old data formats
- **Complete Workflow**: Form → Validation → Storage → Rendering → PDF
- **No Placeholder Defaults**: Empty fields remain empty across parsing, models, and templates (no auto-inserted dashes or dummy emails)

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
- `GET /v/{token}` - View-only mode via tokenized link (no raw UUID in URL)
- `GET /resume/{resume_id}/view` - Legacy view URL (still supported)
- `GET /resume/{resume_id}/share` - Returns shareable link JSON (points to `/v/{token}`)
- `GET /test` - Pre-filled test form
- `POST /generate` - Generate CV from form data (supports legacy and dynamic formats; can direct-download PDF)
- `GET /cv/{cv_id}` - View generated CV with download button
- `GET /cv/{cv_id}/html` - Raw HTML CV
- `GET /cv/{cv_id}/pdf` - On-demand PDF generation via Playwright

  Notes:
  - The UI “Copy Share URL” action uses the server-provided tokenized link (`/v/{token}`). The `/share` JSON endpoint is provided for API integrations.

### **API Endpoints**
- `GET /api/v1/cvs` - List all CVs
- `GET /api/v1/cv/{cv_id}` - Get CV data
- `DELETE /api/v1/cv/{cv_id}` - Delete CV

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
- **IAM Role**: EC2 instance profile for future AWS services
- **Remote Backend**: S3 state bucket with versioning + DynamoDB lock table
- **User Data Script**: Idempotent application setup on instance launch
- **SSL Certificate**: Automated Let's Encrypt certificate management
- **Security Headers**: HSTS, X-Frame-Options, XSS protection

## **Recent Technical Improvements**

- ✅ **UUID-based Resume Flow**: Create/edit/view via `/resume/{resume_id}` with shareable view-only link
- ✅ **Resume Storage Service**: Draft persistence in `resume_data/` with metadata tracking
- ✅ **PDF Library Migration**: Playwright for better quality (from xhtml2pdf)
- ✅ **Professional Summary**: Added optional summary section
- ✅ **Template Optimization**: Improved formatting and spacing
- ✅ **Dynamic Content**: Smart conditional rendering
- ✅ **Font Customization**: Title/body font sizes/colors and line-height
- ✅ **Clean Architecture**: Service layer and Pydantic models
- ✅ **SSL/HTTPS Implementation**: Let's Encrypt certificates with automatic renewal
- ✅ **Idempotent Deployment**: Safe multi-run user data scripts
- ✅ **Security Headers**: HSTS, XSS protection, content security policies
- ✅ **Save-status UI**: Added saved/unsaved banner with timestamp, checkmark, and spinner under “Live Preview”
- ✅ **Removed Placeholder Dashes**: Eliminated auto-insertion of “—”/dummy email; models now default to empty strings and parsers preserve empties
- ✅ **S3-backed Resume Storage**: Draft persistence moved to S3 in production with environment-based switching; Terraform-managed bucket, encryption, and IAM
- ✅ **Subtle Loading UX**: Global top progress bar on form and landing pages; buttons show inline spinners and disable during autosave/copy/share/PDF generation; non-intrusive visuals
- ✅ **Tokenized Share Links**: Share URLs use `/v/{token}` derived from a server-side secret; raw UUIDs are never exposed in shared links

## **Current Development Status**

### **Completed Features**
- Clean architecture with service layer
- Dynamic form with real-time preview
- High-quality PDF generation with Playwright
- Professional template design
- AWS deployment infrastructure
- Comprehensive error handling and logging
- UUID-based resume creation/editing and view-only sharing
- Resume drafts persisted via `ResumeStorageService` (S3 in production; local in development)

### **Planned Enhancements** (from TODOs)
- AWS S3 integration for persistent storage of generated CVs and drafts
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
  "internships": [{"company": "Google", "role": "SWE Intern"}]
}
```

## **Template System**

### **Template Files**
- `root_choice.html` - Minimal root landing UI to continue or start new using localStorage
- `cv_template.html` - Web display with embedded CSS; supports view-only mode and font settings
- `cv_template_pdf.html` - PDF-optimized with specific styling for print and font settings
- `form.html` - Dynamic, UUID-aware form with JavaScript for adding/removing sections and draft-saving

### **Template Features**
- **Conditional Rendering**: Only shows sections with actual content
- **Jinja2 Filters**: Smart filtering of empty entries
- **Responsive Design**: Works on desktop and mobile
- **Professional Styling**: Academic resume format with proper typography
- **Subtle Global Progress Bar**: 2px top-edge bar during async actions (enabled in `form.html` and `root_choice.html`)
- **Action Button Feedback**: Buttons disable and show tiny spinners during operations (copy, share, PDF)
 - **Tokenized Share URL**: Form receives a precomputed `share_url` from the server; frontend never handles keys or encryption
 - **View-only Toast**: Minimal top-right toast on shared views linking back to the homepage; no resume ID is displayed

## **Service Layer Architecture**

### **CVService Class** (`app/services/cv_service.py`)
- `generate_cv(cv_data)` - Create new CV with UUID
- `get_cv_data(cv_id)` - Retrieve CV by ID
- `update_cv_data(cv_id, cv_data)` - Update existing CV
- `delete_cv(cv_id)` - Remove CV and files
- `list_cvs()` - Get all CVs with metadata
- `convert_legacy_data(form_data)` - Backward compatibility

### **ResumeStorageService** (`app/services/resume_storage_service.py`)
- `create_new_resume(initial_data=None, resume_id=None)` - Returns a new `resume_id`; optionally accepts a pre-defined `resume_id`
- `get_resume_data(resume_id)` - Retrieve draft data and status
- `update_resume_data(resume_id, data, is_completed=False)` - Save draft or mark completed
- `resume_exists(resume_id)` - Check for existence
- `list_resumes()` - List metadata from `resume_metadata.json`
- `delete_resume(resume_id)` - Remove draft and clean metadata

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
- `CVData` - Complete CV structure with validation
- `CVDocument` - CV data with metadata
  
  Model defaults and validation:
  - Fields default to empty strings instead of placeholder symbols
  - Validators trim whitespace but do not force placeholder values
  - Rendering logic only displays fields with actual content

### **ID Codec Utilities** (`app/core/id_codec.py`)
- `encode_share_token(resume_id)` - Deterministically maps UUID → short token (AES-128 ECB over a single 16-byte block, base64url without padding)
- `decode_share_token(token)` - Reverses token → UUID using server-side key
- Key via `SHARE_TOKEN_KEY` environment variable; no DB mapping needed

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
# Test with pre-filled form
# Access http://localhost:8000/test

# Generate test PDF
# Access http://localhost:8000/test/pdf
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
- **Security Headers**: HSTS, X-Frame-Options, XSS protection
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
- Supports both legacy flat format and new structured format
- Comprehensive client-side validation
- Subtle loading indicators (top progress bar + button spinners/disable) to avoid spamming actions and provide feedback

### **Security Considerations**
- ✅ **Input validation**: Pydantic models with comprehensive validation
- ✅ **Error handling**: Proper error messages without internal exposure
- ✅ **File security**: Path validation prevents directory traversal
- ✅ **Content validation**: Content-type validation for uploads
- ✅ **SSL/TLS encryption**: HTTPS with Let's Encrypt certificates
- ✅ **Security headers**: HSTS, X-Frame-Options, XSS protection
- ✅ **HTTPS enforcement**: All traffic encrypted with automatic redirects

This is a **well-architected, production-ready application** that demonstrates modern Python web development practices with clean code, proper separation of concerns, comprehensive deployment automation, and enterprise-grade security. The project successfully generates professional academic resumes with a focus on user experience, code quality, and security best practices. 