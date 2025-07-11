# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **CV/Resume Generator v2.0** web application built with FastAPI that creates professional PDF and HTML resumes using clean architecture principles. The application features Pydantic models for data validation, a service layer for business logic, and conditional rendering to show only sections with actual content.

## Architecture

### Core Components

**FastAPI Application** (`main.py`):
- Clean architecture with Pydantic models and service layer
- Structured logging and proper error handling
- API versioning with `/api/v1/` endpoints
- Health check and monitoring endpoints

**Models Layer** (`app/models/cv_data.py`):
- Pydantic models for data validation and serialization
- Structured data types replacing flat field names
- Automatic validation for emails, required fields, and data types
- Conversion utilities for legacy format compatibility

**Service Layer** (`app/services/cv_service.py`):
- Business logic separated from API endpoints
- CV generation, retrieval, update, and deletion operations
- Data conversion between legacy and structured formats
- File management and storage operations

**Core Infrastructure** (`app/core/`):
- Custom exception classes with proper error handling
- Structured logging configuration
- Utility functions and helpers

**Template System** (`templates/`):
- `cv_template.html` - HTML template for web display
- `cv_template_pdf.html` - PDF-specific HTML template for WeasyPrint
- `form.html` - Web form for data entry

**Data Flow**:
1. User fills form → validated through Pydantic models
2. Service layer processes and stores structured data
3. Templates rendered with validated data
4. HTML files generated and saved to `generated/`
5. PDF created on-demand via WeasyPrint from HTML template

## Key Features

- **Clean Architecture**: Pydantic models, service layer, and proper separation of concerns
- **Data Validation**: Automatic validation with meaningful error messages
- **Structured Logging**: Comprehensive logging with different levels and contexts
- **API Endpoints**: RESTful API with versioning for programmatic access
- **Dynamic Content Rendering**: Only shows sections with actual content
- **Dual Output**: Generates both PDF and HTML versions
- **Structured Data Storage**: Complete CV data saved as JSON with metadata
- **Professional Formatting**: Clean, professional HTML output
- **Conditional Templates**: Smart Jinja2 templates that adapt based on data
- **Error Handling**: Proper exception handling with recovery mechanisms

## Development Commands

### Setup and Installation
```bash
# Setup virtual environment
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Dependencies include:
# - FastAPI & Uvicorn for web framework
# - Pydantic for data validation
# - WeasyPrint for PDF generation from HTML
# - Jinja2 for template rendering
```

### Running the Application
```bash
# Development mode with auto-reload (recommended)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
python main.py

# Access at http://localhost:8000
```

### Testing
```bash
# Run comprehensive test with sample data
python test_template.py

# Test with pre-filled form
# Access http://localhost:8000/test
```

## Technical Implementation

### Template Rendering Architecture
The application uses a sophisticated template system:

**Data Transformation** (`main.py:31-148`):
- `create_structured_data()` - Converts form data to structured JSON
- `filter_empty_sections()` - Removes empty optional sections
- `render_template()` - Handles HTML template rendering

**Conditional Rendering**:
- Education entries: Only shows rows with qualifications
- Optional sections: Hidden if no content (achievements, internships, projects, etc.)
- Technical skills: Only shows filled skill entries
- Smart spacing: Adjusts layout when sections are removed

### File Generation Process
1. **Form Submission** → `/generate` endpoint
2. **Data Structuring** → JSON format with metadata
3. **Template Rendering** → HTML files for display and PDF
4. **File Storage** → `generated/{cv_id}.*` files
5. **PDF Generation** → On-demand via WeasyPrint from HTML template

### API Endpoints
- `GET /` - CV form page
- `GET /test` - Pre-filled test form
- `POST /generate` - Generate CV from form data
- `GET /cv/{cv_id}` - View CV with download button
- `GET /cv/{cv_id}/html` - Raw HTML download
- `GET /cv/{cv_id}/pdf` - PDF download with proper filename

## Working with Templates

### HTML Templates
- `cv_template.html` - For web display with embedded CSS
- `cv_template_pdf.html` - PDF-specific template optimized for WeasyPrint
- Standard Jinja2 syntax with conditional blocks
- Conditional blocks: `{% if section %}...{% endif %}`
- Loops: `{% for item in items %}...{% endfor %}`
- Filters: `{% set valid_items = items|selectattr('field')|list %}`

### Adding New Sections
1. Update `create_structured_data()` in `main.py`
2. Add filtering logic in `filter_empty_sections()`
3. Update both HTML templates (`cv_template.html` and `cv_template_pdf.html`)
4. Add form fields in `form.html`
5. Update test data in `test_data.json`

## Data Structure

The application uses structured JSON for CV data:
```json
{
  "metadata": {
    "cv_id": "uuid",
    "created_at": "ISO timestamp",
    "version": "1.0"
  },
  "personal_info": { "full_name": "...", "email": "..." },
  "education": [{"qualification": "...", "institute": "..."}],
  "achievements": [{"description": "...", "year": "..."}],
  "internships": [{"company": "...", "role": "...", "points": [...]}],
  "projects": [{"title": "...", "type": "...", "points": [...]}],
  "positions_of_responsibility": [...],
  "extracurricular": [...],
  "technical_skills": [...]
}
```

## Common Tasks

### Testing Template Changes
```bash
# Always test templates after changes
python test_template.py

# Check for Jinja2 syntax errors
# Look for unreplaced variables ({{ }} in output)
```

### Debugging PDF Generation
- Check `generated/` directory for LaTeX files
- LaTeX compilation errors logged in `.log` files
- Use `--reload` flag for automatic template reloading

### Adding New Fields
1. Update form in `templates/form.html`
2. Add field handling in `generate_cv()` endpoint
3. Update `create_structured_data()` function
4. Add template logic in both `.tex` and `.html` templates
5. Update test data and run tests

## Dependencies

### Core Dependencies
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `jinja2` - Template engine
- `weasyprint` - PDF generation from HTML
- `python-multipart` - Form handling

### System Dependencies
- **Python 3.7+** - Runtime environment
- **WeasyPrint dependencies** - May require system libraries for PDF generation

## File Structure

```
cv-generator/
├── main.py                 # FastAPI application
├── test_template.py        # Test script
├── requirements.txt        # Python dependencies
├── test_data.json         # Sample data for testing
├── templates/
│   ├── form.html          # Web form
│   ├── cv_template.html   # HTML template for display
│   └── cv_template_pdf.html # PDF-specific HTML template
├── generated/             # Generated files (CV outputs)
├── static/               # Static assets
└── env/                  # Virtual environment
```

## Troubleshooting

### Common Issues

**Template Rendering Issues**:
- Test with `python test_template.py`
- Check data structure matches template expectations
- Verify conditional logic in templates
- Check for unreplaced Jinja2 variables (`{{ }}`)

**PDF Generation Problems**:
- Check WeasyPrint dependencies and system libraries
- Verify HTML template is valid and CSS is compatible with WeasyPrint
- Ensure no complex CSS that WeasyPrint doesn't support

### Development Tips
- Use `--reload` flag for automatic server restart
- Test template changes with `test_template.py`
- Check `generated/` directory for debug files
- Use `/test` endpoint for quick testing with sample data
- When modifying templates, test both web display and PDF generation

## Future Enhancements

Planned features (see `TODOs.md`):
- AWS S3 integration for persistent storage
- Search functionality for generated CVs
- Resume editing capabilities
- Enhanced security and validation
- User authentication system