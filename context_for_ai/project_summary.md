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
playwright>=1.40.0
pydantic>=2.11.0
jinja2==3.1.2
python-multipart==0.0.6
aiofiles==23.2.1
```

## **Project Structure**

```
cv-generator/
├── app/
│   ├── models/cv_data.py         # Pydantic data models
│   ├── services/cv_service.py    # Business logic layer
│   └── core/                     # Exceptions, logging
├── templates/
│   ├── form.html                 # Dynamic web form
│   ├── cv_template.html          # Web display template
│   └── cv_template_pdf.html      # PDF-optimized template
├── terraform/                    # AWS deployment infrastructure
├── main.py                       # FastAPI application entry point
├── generated/                    # Output directory for CVs
└── test_data_structured.json     # Sample data
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
- **Data Validation**: Client and server-side validation
- **Test Data Integration**: Pre-filled form for testing

### **3. Professional CV Output**
- **Dual Formats**: HTML for web viewing + PDF for download
- **Smart Rendering**: Conditional sections (only shows filled content)
- **Professional Styling**: Clean, academic resume format
- **Optimized PDF**: A4 format with proper margins using Playwright

### **4. Data Management**
- **Structured Storage**: JSON format with metadata
- **UUID-based IDs**: Unique identifiers for each CV
- **Legacy Support**: Backward compatibility with old data formats
- **Complete Workflow**: Form → Validation → Storage → Rendering → PDF

## **Core Workflow**

1. **User Input** → Dynamic web form with sections for:
   - Personal Information
   - Professional Summary (optional)
   - Education (multiple entries)
   - Achievements
   - Internships
   - Projects
   - Positions of Responsibility
   - Extracurricular Activities
   - Technical Skills

2. **Data Processing** → Pydantic validation and structured storage
3. **Template Rendering** → Jinja2 templates for HTML output
4. **PDF Generation** → Playwright converts HTML to high-quality PDF
5. **File Management** → Organized storage with unique identifiers

## **API Endpoints**

### **Web Interface**
- `GET /` - Main CV form
- `GET /test` - Pre-filled test form
- `POST /generate` - Generate CV from form data
- `GET /cv/{cv_id}` - View CV with download button
- `GET /cv/{cv_id}/pdf` - Download PDF

### **API Endpoints**
- `GET /api/v1/cvs` - List all CVs
- `GET /api/v1/cv/{cv_id}` - Get CV data
- `DELETE /api/v1/cv/{cv_id}` - Delete CV
- `GET /health` - Health check

## **Deployment Infrastructure**

### **AWS EC2 Deployment**
- **Terraform Configuration**: Infrastructure as Code
- **EC2 Instance**: t3.small Ubuntu 22.04 LTS
- **Nginx Reverse Proxy**: HTTP traffic routing
- **SystemD Service**: Application lifecycle management
- **Cloudflare DNS**: Custom domain management
- **Automated Setup**: Complete deployment with user data scripts

### **Key Infrastructure Components**
- **Security Group**: SSH (22), HTTP (80), HTTPS (443), FastAPI (8000)
- **Elastic IP**: Static IP address for the instance
- **IAM Role**: EC2 instance profile for future AWS services
- **User Data Script**: Automated application setup on instance launch

## **Recent Technical Improvements**

- ✅ **PDF Library Migration**: Playwright for better quality (from xhtml2pdf)
- ✅ **Professional Summary**: Added optional summary section
- ✅ **Template Optimization**: Improved formatting and spacing
- ✅ **Dynamic Content**: Smart conditional rendering
- ✅ **Clean Architecture**: Service layer and Pydantic models

## **Current Development Status**

### **Completed Features**
- Clean architecture with service layer
- Dynamic form with real-time preview
- High-quality PDF generation with Playwright
- Professional template design
- AWS deployment infrastructure
- Comprehensive error handling and logging

### **Planned Enhancements** (from TODOs)
- AWS S3 integration for persistent storage
- Search functionality for generated CVs
- Resume editing capabilities
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
- `cv_template.html` - Web display with embedded CSS and interactive features
- `cv_template_pdf.html` - PDF-optimized with specific styling for print
- `form.html` - Dynamic form with JavaScript for adding/removing sections

### **Template Features**
- **Conditional Rendering**: Only shows sections with actual content
- **Jinja2 Filters**: Smart filtering of empty entries
- **Responsive Design**: Works on desktop and mobile
- **Professional Styling**: Academic resume format with proper typography

## **Service Layer Architecture**

### **CVService Class** (`app/services/cv_service.py`)
- `generate_cv(cv_data)` - Create new CV with UUID
- `get_cv_data(cv_id)` - Retrieve CV by ID
- `update_cv_data(cv_id, cv_data)` - Update existing CV
- `delete_cv(cv_id)` - Remove CV and files
- `list_cvs()` - Get all CVs with metadata
- `convert_legacy_data(form_data)` - Backward compatibility

### **Data Models** (`app/models/cv_data.py`)
- `PersonalInfo` - Name, contact details, education
- `EducationEntry` - Qualification, institute, year, CGPA
- `AchievementEntry` - Description and year
- `InternshipEntry` - Company, role, duration, points
- `ProjectEntry` - Title, type, duration, points
- `PositionEntry` - Club, role, duration, points
- `CVData` - Complete CV structure with validation
- `CVDocument` - CV data with metadata

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

# Deploy infrastructure
cd terraform
terraform init
terraform plan
terraform apply
```

### **Manual Updates**
```bash
# SSH into instance
ssh -i ~/.ssh/AvantiFellows.pem ubuntu@<ELASTIC_IP>

# Update application
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

### **Form Handling**
- Dynamic JavaScript for adding/removing sections
- Real-time preview with live updates
- Supports both legacy flat format and new structured format
- Comprehensive client-side validation

### **Security Considerations**
- Input validation with Pydantic models
- Proper error messages without internal exposure
- File path validation prevents directory traversal
- Content-type validation for uploads

This is a **well-architected, production-ready application** that demonstrates modern Python web development practices with clean code, proper separation of concerns, and comprehensive deployment automation. The project successfully generates professional academic resumes with a focus on user experience and code quality. 