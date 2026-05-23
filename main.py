"""
CV Generator Application - Refactored Version 2.0
Clean architecture with Pydantic models and service layer
"""
from fastapi import FastAPI, Request, HTTPException, Depends, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from typing import List, Optional
import json
import os
import re
from pathlib import Path
from io import BytesIO
import pprint
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Load .env file if it exists (for local development only)
# On server, environment variables are set via systemd service
env_file_loaded = False
if os.path.exists(".env"):
    load_dotenv()
    env_file_loaded = True

# Import our new models and services
from app.models.cv_data import CVData, CVGenerateRequest, CVGenerateResponse
from app.services.cv_service import CVService
from app.services.resume_storage_service import create_resume_storage_service
from app.core.exceptions import CVGenerationError, CVNotFoundError, TemplateError, PDFGenerationError
from app.core.logging import setup_logging, get_logger
from app.core.id_codec import encode_share_token, decode_share_token

# Setup logging
setup_logging(level="INFO")
logger = get_logger(__name__)

# Log environment setup
if env_file_loaded:
    logger.info("Loaded .env file for local development")
else:
    logger.info("No .env file found, using system environment variables")

# Define base path for application files
BASE_PATH = Path(".")

# Create FastAPI app
app = FastAPI(
    title="CV Generator v2.0",
    description="Generate professional PDF resumes with clean architecture",
    version="2.0.0"
)

# Create directories
(BASE_PATH / "static").mkdir(exist_ok=True)
(BASE_PATH / "templates").mkdir(exist_ok=True)
(BASE_PATH / "generated").mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_PATH / "static")), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Initialize services
cv_service = CVService(base_path=BASE_PATH)
# Select storage type via environment (default local)
storage_type = os.getenv("RESUME_STORAGE_TYPE", "local")
resume_storage_service = create_resume_storage_service(BASE_PATH, storage_type)

async def generate_pdf_with_playwright(html_content: str) -> bytes:
    """Generate PDF from HTML using Playwright"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Set the HTML content
        await page.set_content(html_content, wait_until='networkidle')
        
        # Generate PDF with A4 format and proper margins
        pdf_bytes = await page.pdf(
            format='A4',
            margin={
                'top': '0.2in',
                'bottom': '0.2in', 
                'left': '0.7in',
                'right': '0.4in'
            },
            print_background=True,
            prefer_css_page_size=True
        )
        
        await browser.close()
        return pdf_bytes

def create_filename(name: str) -> str:
    """Create a clean filename from the user's name"""
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    return clean_name.replace(' ', '_').lower()


def render_template(template_name: str, data: dict) -> str:
    """Render Jinja2 template with data"""
    try:
        template = templates.env.get_template(template_name)
        return template.render(**data)
    except Exception as e:
        logger.error(f"Template rendering error: {str(e)}")
        raise TemplateError(f"Failed to render template {template_name}: {str(e)}")


# Exception handlers
@app.exception_handler(CVNotFoundError)
async def cv_not_found_handler(request: Request, exc: CVNotFoundError):
    logger.warning(f"CV not found: {str(exc)}")
    raise HTTPException(status_code=404, detail=str(exc))


@app.exception_handler(CVGenerationError)
async def cv_generation_error_handler(request: Request, exc: CVGenerationError):
    logger.error(f"CV generation error: {str(exc)}")
    raise HTTPException(status_code=500, detail=str(exc))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {str(exc)}")
    return HTTPException(status_code=422, detail=f"Validation error: {str(exc)}")


# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the dynamic CV form - continue last resume or create new"""
    try:
        # Explicit request to start a new resume ignores cookies/local state
        new_param = request.query_params.get('new')
        if new_param and new_param.lower() in ('1', 'true', 'yes'):
            new_resume_id = resume_storage_service.create_new_resume()
            return RedirectResponse(url=f"/resume/{new_resume_id}", status_code=302)

        # Allow resume continuation via query param
        resume_id_param = request.query_params.get('resume_id')
        if resume_id_param and resume_storage_service.resume_exists(resume_id_param):
            return RedirectResponse(url=f"/resume/{resume_id_param}", status_code=302)

        # Otherwise, render a tiny bootstrap page to let the browser check localStorage
        # and redirect accordingly (continue last resume or start new)
        return templates.TemplateResponse("root_choice.html", {"request": request})
        
    except Exception as e:
        logger.error(f"Error creating or continuing resume: {str(e)}")
        # Fall back to empty form
        return templates.TemplateResponse("form.html", {"request": request})


@app.get("/resume/{resume_id}", response_class=HTMLResponse)
async def resume_form(request: Request, resume_id: str):
    """Serve the CV form with existing data or create new if not exists
    
    Special case: if resume_id is 'test', load data from test_data_structured.json
    """
    try:
        # Special handling for test data
        if resume_id.lower() in ("test", "test-minimal"):
            try:
                # Load structured test data
                test_file = "test_data_structured.json" if resume_id.lower() == "test" else "test_data_minimal.json"
                with open(test_file, "r") as f:
                    test_data = json.load(f)
                
                base_url = str(request.base_url).rstrip('/')
                # For test, use a simple share URL (no tokenization needed)
                simple_id = "test" if resume_id.lower() == "test" else "test-minimal"
                share_url = f"{base_url}/resume/{simple_id}/view"
                
                logger.info("Loaded test data for /resume/test endpoint")
                return templates.TemplateResponse("form.html", {
                    "request": request,
                    "form_data": test_data,
                    "resume_id": resume_id,
                    "is_edit_mode": True,  # Allow editing
                    "is_completed": False,
                    "share_url": share_url
                })
            except Exception as e:
                logger.error(f"Error loading test data: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error loading test data: {str(e)}")
        
        # Check if resume exists
        if resume_storage_service.resume_exists(resume_id):
            # Load existing resume data
            resume_data = resume_storage_service.get_resume_data(resume_id)
            if resume_data and resume_data.get("data"):
                # Resume exists with data - show in edit mode
                base_url = str(request.base_url).rstrip('/')
                share_token = encode_share_token(resume_id)
                share_url = f"{base_url}/v/{share_token}"
                response = templates.TemplateResponse("form.html", {
                    "request": request, 
                    "form_data": resume_data["data"],
                    "resume_id": resume_id,
                    "is_edit_mode": True,
                    "is_completed": resume_data.get("is_completed", False),
                    "share_url": share_url
                })
            else:
                # Resume exists but no data - show empty form
                base_url = str(request.base_url).rstrip('/')
                share_token = encode_share_token(resume_id)
                share_url = f"{base_url}/v/{share_token}"
                response = templates.TemplateResponse("form.html", {
                    "request": request,
                    "resume_id": resume_id,
                    "is_edit_mode": False,
                    "is_completed": False,
                    "share_url": share_url
                })
        else:
            # Resume doesn't exist - create new shell and show empty form
            resume_storage_service.create_new_resume(resume_id=resume_id)
            base_url = str(request.base_url).rstrip('/')
            share_token = encode_share_token(resume_id)
            share_url = f"{base_url}/v/{share_token}"
            response = templates.TemplateResponse("form.html", {
                "request": request,
                "resume_id": resume_id,
                "is_edit_mode": False,
                "is_completed": False,
                "share_url": share_url
            })

        return response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving resume form for ID {resume_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving resume form: {str(e)}")


@app.get("/resume/", response_class=HTMLResponse)
async def resume_form_trailing_slash():
    """Redirect /resume/ to / to avoid 404 when missing an ID."""
    return RedirectResponse(url="/", status_code=302)


@app.get("/resume/{resume_id}/view", response_class=HTMLResponse)
async def view_resume(request: Request, resume_id: str):
    """View-only mode for shared resumes
    
    Special case: if resume_id is 'test', load data from test_data_structured.json
    """
    try:
        # Special handling for test data
        if resume_id.lower() in ("test", "test-minimal"):
            try:
                # Load structured test data
                test_file = "test_data_structured.json" if resume_id.lower() == "test" else "test_data_minimal.json"
                with open(test_file, "r") as f:
                    test_data = json.load(f)
                
                cv_data = CVData(**test_data)
                base_url = str(request.base_url).rstrip('/')
                return templates.TemplateResponse("cv_template.html", {
                    "request": request,
                    "cv_data": cv_data,
                    **cv_data.dict(),
                    "is_view_only": True,
                    "resume_id": resume_id,
                    "base_url": base_url
                })
            except Exception as e:
                logger.error(f"Error loading test data for view: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error loading test data: {str(e)}")
        
        if not resume_storage_service.resume_exists(resume_id):
            raise HTTPException(status_code=404, detail="Resume not found")
        
        resume_data = resume_storage_service.get_resume_data(resume_id)
        if not resume_data or not resume_data.get("data"):
            raise HTTPException(status_code=404, detail="Resume data not found")
        
        # Allow viewing even if resume is not completed (for sharing drafts)
        # No completion check needed
        
        # Render the resume in view-only mode
        cv_data = CVData(**resume_data["data"])
        
        # Get base URL for toast link
        base_url = str(request.base_url).rstrip('/')
        return templates.TemplateResponse("cv_template.html", {
            "request": request,
            "cv_data": cv_data,
            **cv_data.dict(),
            "is_view_only": True,
            "resume_id": resume_id,
            "base_url": base_url
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing resume {resume_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error viewing resume: {str(e)}")


@app.get("/v/{token}", response_class=HTMLResponse)
async def view_resume_token(request: Request, token: str):
    try:
        resume_id = decode_share_token(token)
        if not resume_storage_service.resume_exists(resume_id):
            raise HTTPException(status_code=404, detail="Resume not found")

        resume_data = resume_storage_service.get_resume_data(resume_id)
        if not resume_data or not resume_data.get("data"):
            raise HTTPException(status_code=404, detail="Resume data not found")

        cv_data = CVData(**resume_data["data"])
        base_url = str(request.base_url).rstrip('/')
        return templates.TemplateResponse("cv_template.html", {
            "request": request,
            "cv_data": cv_data,
            **cv_data.dict(),
            "is_view_only": True,
            "resume_id": resume_id,
            "base_url": base_url
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing resume via token {token}: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid or expired share link")


@app.get("/api/v1/resume/{resume_id}/exists")
async def resume_exists_api(resume_id: str):
    """Lightweight existence check for a resume UUID (used by homepage to validate localStorage).
    
    Special case: 'test' always returns True
    """
    try:
        # Special handling for test data - always exists
        if resume_id.lower() in ("test", "test-minimal"):
            return {"resume_id": resume_id, "exists": True}
        
        exists = resume_storage_service.resume_exists(resume_id)
        return {"resume_id": resume_id, "exists": bool(exists)}
    except Exception as e:
        logger.error(f"Error checking existence for resume {resume_id}: {str(e)}")
        # On error, be safe and report non-existence to trigger a fresh flow
        return {"resume_id": resume_id, "exists": False}


@app.post("/resume/{resume_id}/save")
async def save_resume_draft(request: Request, resume_id: str):
    """Save resume draft data
    
    Special case: if resume_id is 'test', skip saving (test data is read-only)
    """
    try:
        # Special handling for test data - don't save
        if resume_id.lower() == "test":
            logger.info("Skipping save for test resume (read-only)")
            return {"status": "success", "message": "Test data is read-only (not saved)"}
        
        # Get form data
        form_data = await request.form()
        
        # Parse the form data into structured format
        structured_data = parse_dynamic_form_data(form_data)
        
        # Save to resume storage service
        success = resume_storage_service.update_resume_data(
            resume_id, 
            structured_data, 
            is_completed=False
        )
        
        if success:
            return {"status": "success", "message": "Draft saved successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save draft")
            
    except Exception as e:
        logger.error(f"Error saving resume draft for ID {resume_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving draft: {str(e)}")


## Removed: /resume/{resume_id}/share endpoint (unused)




@app.get("/test", response_class=HTMLResponse)
async def test_form_redirect():
    """Redirect to /resume/test for unified test data handling"""
    return RedirectResponse(url="/resume/test", status_code=302)


@app.get("/test/pdf")
async def download_test_cv_pdf():
    """Generate and download PDF of the test CV data"""
    try:
        # Load structured test data
        with open("test_data_structured.json", "r") as f:
            structured_data = json.load(f)
        
        # Create CV data object
        cv_data = CVData(**structured_data)
        
        # Render PDF-specific HTML template
        html_content = render_template('cv_template_pdf.html', {
            "cv_data": cv_data,
            **cv_data.dict()
        })
        
        # Generate PDF using Playwright
        try:
            logger.info("Starting PDF generation with Playwright")
            pdf_bytes = await generate_pdf_with_playwright(html_content)
            logger.info(f"PDF generated successfully, size: {len(pdf_bytes)} bytes")
        except Exception as e:
            logger.error(f"Exception during PDF generation: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        
        # Create filename from user's name
        pdf_filename = f"{create_filename(cv_data.personal_info.full_name)}_test.pdf"
        
        logger.info(f"Test PDF generated successfully: {pdf_filename}")
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={pdf_filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error generating test PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate test PDF: {str(e)}")


@app.get("/test/minimal", response_class=HTMLResponse)
async def test_minimal_form_redirect():
    """Redirect to /resume/test-minimal for minimal test data handling"""
    return RedirectResponse(url="/resume/test-minimal", status_code=302)


@app.get("/test/minimal/pdf")
async def download_test_minimal_cv_pdf():
    """Generate and download PDF of the minimal test CV data"""
    try:
        # Load minimal structured test data
        with open("test_data_minimal.json", "r") as f:
            structured_data = json.load(f)
        
        # Create CV data object
        cv_data = CVData(**structured_data)
        
        # Render PDF-specific HTML template
        html_content = render_template('cv_template_pdf.html', {
            "cv_data": cv_data,
            **cv_data.dict()
        })
        
        # Generate PDF using Playwright
        try:
            logger.info("Starting PDF generation with Playwright (minimal test)")
            pdf_bytes = await generate_pdf_with_playwright(html_content)
            logger.info(f"PDF generated successfully, size: {len(pdf_bytes)} bytes")
        except Exception as e:
            logger.error(f"Exception during PDF generation (minimal): {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        
        # Create filename from user's name
        pdf_filename = f"{create_filename(cv_data.personal_info.full_name)}_test_minimal.pdf"
        
        logger.info(f"Minimal Test PDF generated successfully: {pdf_filename}")
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={pdf_filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error generating minimal test PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate minimal test PDF: {str(e)}")



def convert_structured_to_form_data(structured_data: dict) -> dict:
    """Convert structured data to legacy form format for template compatibility"""
    form_data = {}
    
    # Personal info
    personal_info = structured_data.get("personal_info", {})
    form_data.update({
        "full_name": personal_info.get("full_name", ""),
        "highest_education": personal_info.get("highest_education", ""),
        "city": personal_info.get("city", ""),
        "phone": personal_info.get("phone", ""),
        "email": personal_info.get("email", "")
    })
    
    # Education
    education = structured_data.get("education", [])
    for i, edu in enumerate(education[:5], 1):
        form_data.update({
            f"edu_{i}_qual": edu.get("qualification", ""),
            f"edu_{i}_stream": edu.get("stream", ""),
            f"edu_{i}_institute": edu.get("institute", ""),
            f"edu_{i}_year": edu.get("year", ""),
            f"edu_{i}_cgpa": edu.get("cgpa", "")
        })
    
    # Achievements
    achievements = structured_data.get("achievements", [])
    for i, ach in enumerate(achievements[:5], 1):
        form_data.update({
            f"ach_{i}_desc": ach.get("description", ""),
            f"ach_{i}_year": ach.get("year", "")
        })
    
    # Internships
    internships = structured_data.get("internships", [])
    for i, intern in enumerate(internships[:3], 1):
        form_data.update({
            f"intern_{i}_company": intern.get("company", ""),
            f"intern_{i}_role": intern.get("role", ""),
            f"intern_{i}_duration": intern.get("duration", "")
        })
        points = intern.get("points", [])
        for j, point in enumerate(points[:5], 1):
            form_data[f"intern_{i}_point_{j}"] = point
    
    # Projects
    projects = structured_data.get("projects", [])
    for i, proj in enumerate(projects[:3], 1):
        form_data.update({
            f"proj_{i}_title": proj.get("title", ""),
            f"proj_{i}_type": proj.get("type", ""),
            f"proj_{i}_duration": proj.get("duration", "")
        })
        points = proj.get("points", [])
        for j, point in enumerate(points[:5], 1):
            form_data[f"proj_{i}_point_{j}"] = point
    
    # Positions of responsibility
    positions = structured_data.get("positions_of_responsibility", [])
    for i, pos in enumerate(positions[:3], 1):
        form_data.update({
            f"por_{i}_club": pos.get("club", ""),
            f"por_{i}_role": pos.get("role", ""),
            f"por_{i}_duration": pos.get("duration", "")
        })
        points = pos.get("points", [])
        for j, point in enumerate(points[:5], 1):
            form_data[f"por_{i}_point_{j}"] = point
    
    # Extracurricular activities
    extracurricular = structured_data.get("extracurricular", [])
    for i, activity in enumerate(extracurricular[:5], 1):
        form_data[f"extracur_{i}_desc"] = activity
    
    # Technical skills
    technical_skills = structured_data.get("technical_skills", [])
    for i, skill in enumerate(technical_skills[:10], 1):
        form_data[f"techskill_{i}"] = skill
    
    return form_data


@app.post("/generate")
async def generate_cv(request: Request):
    """Generate CV from form data - supports both legacy and dynamic formats"""
    try:
        # Get form data
        form_data = await request.form()
        logger.info(f"[DEBUG] Raw form_data keys: {list(form_data.keys())}")
        
        # Get resume_id if present
        resume_id = form_data.get('resume_id')
        
        # Check if this is a direct PDF download request
        is_pdf_download = form_data.get('download_pdf') == 'true'
        
        # Check if this is dynamic form data (has array fields)
        is_dynamic = any(key.startswith(('education[', 'work_experience[', 'achievements[', 'internships[', 'projects[', 'positions[', 'extracurricular[]', 'languages[]')) 
                        for key in form_data.keys())
        logger.info(f"[DEBUG] is_dynamic: {is_dynamic}")
        if is_dynamic:
            # Handle dynamic form data
            structured_data = parse_dynamic_form_data(form_data)
            logger.info(f"[DEBUG] structured_data: {structured_data}")
            cv_data = CVData(**structured_data)
        else:
            # Handle legacy form data
            form_variables = dict(form_data)
            logger.info(f"[DEBUG] form_variables: {form_variables}")
            cv_data = cv_service.convert_legacy_data(form_variables)
        
        # If PDF download requested, generate and return PDF directly
        if is_pdf_download:
            # Render PDF-specific HTML template
            cv_data_dict = cv_data.dict()
            logger.info(f"[DEBUG] Direct PDF download - cv_data_dict keys: {list(cv_data_dict.keys())}")
            logger.info(f"[DEBUG] Direct PDF download - font_settings: {cv_data_dict.get('font_settings', 'NOT FOUND')}")
            html_content = render_template('cv_template_pdf.html', {
                "cv_data": cv_data,
                **cv_data_dict
            })
            
            # Generate PDF using Playwright
            try:
                logger.info("Starting PDF generation with Playwright for direct download")
                pdf_bytes = await generate_pdf_with_playwright(html_content)
                logger.info(f"PDF generated successfully, size: {len(pdf_bytes)} bytes")
            except Exception as e:
                logger.error(f"Exception during PDF generation: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise
            
            # Create filename from user's name
            pdf_filename = f"{create_filename(cv_data.personal_info.full_name)}.pdf"
            
            logger.info(f"PDF generated successfully for direct download: {pdf_filename}")
            
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={pdf_filename}"}
            )
        
        # Otherwise, generate CV using service for regular flow
        logger.info(f"[DEBUG] cv_data.dict(): {cv_data.dict()}")
        cv_id = cv_service.generate_cv(cv_data)
        
        # Generate HTML file for display
        html_content = render_template('cv_template.html', {
            "cv_data": cv_data,
            **cv_data.dict()
        })
        
        # Save HTML file
        html_file = BASE_PATH / f"generated/{cv_id}.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Create display HTML with download button
        pdf_filename = f"{create_filename(cv_data.personal_info.full_name)}.pdf"
        download_button = f"""
        <div style="position: fixed; top: 20px; right: 20px; z-index: 1000;">
            <a href="/cv/{cv_id}/pdf" download="{pdf_filename}" 
               style="background-color: #4C5196; color: white; padding: 10px 20px; 
                      text-decoration: none; border-radius: 5px; font-weight: bold;
                      box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                📄 Download PDF
            </a>
        </div>
        """
        
        html_with_button = html_content.replace('<body>', f'<body>{download_button}')
        
        # Save display HTML
        display_html_file = BASE_PATH / f"generated/{cv_id}_display.html"
        with open(display_html_file, "w", encoding="utf-8") as f:
            f.write(html_with_button)
        
        logger.info(f"CV generated successfully: {cv_id}")
        
        # Save data to resume storage service if resume_id is provided
        if resume_id:
            try:
                # Mark resume as completed
                resume_storage_service.update_resume_data(
                    resume_id, 
                    cv_data.dict(), 
                    is_completed=True
                )
                logger.info(f"Resume data saved for ID: {resume_id}")
            except Exception as e:
                logger.error(f"Error saving resume data for ID {resume_id}: {str(e)}")
                # Continue with CV generation even if storage fails
        
        # Return redirect response
        return RedirectResponse(url=f"/cv/{cv_id}", status_code=302)
        
    except Exception as e:
        logger.error(f"Error in generate_cv endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating CV: {str(e)}")




def parse_dynamic_form_data(form_data) -> dict:
    """Parse dynamic form data into structured format"""
    # Initialize structured data
    structured_data = {
        "personal_info": {},
        "education": [],
        "work_experience": [],
        "achievements": [],
        "certifications": [],
        "publications": [],
        "internships": [],
        "projects": [],
        "positions_of_responsibility": [],
        "extracurricular": [],
        "languages": [],
        "technical_skills": []
    }
    # Parse personal info
    structured_data["personal_info"] = {
        "full_name": form_data.get("full_name", ""),
        "highest_education": form_data.get("highest_education", ""),
        "city": form_data.get("city", ""),
        "phone": form_data.get("phone", ""),
        "email": form_data.get("email", ""),
        "github": form_data.get("github", ""),
        "linkedin": form_data.get("linkedin", "")
    }
    
    # Parse summary
    structured_data["summary"] = form_data.get("summary", "")
    

    # Parse education entries
    education_data = {}
    for key, value in form_data.items():
        if key.startswith("education["):
            parts = key.split('][')
            index = int(parts[0].split('[')[1])
            field = parts[1].rstrip(']')
            if index not in education_data:
                education_data[index] = {}
            education_data[index][field] = value
    for i in sorted(education_data.keys()):
        # Only add if at least one field is filled and not just default values
        entry = education_data[i]
        filled_fields = [field for field in ['qualification', 'stream', 'institute', 'year', 'cgpa'] 
                        if entry.get(field, '').strip() and entry.get(field, '').strip() not in ['', '—', 'notfilled@email.com']]
        if filled_fields:
            # Keep actual values without forcing dashes for empty fields
            entry = {
                'qualification': entry.get('qualification', '').strip(),
                'stream': entry.get('stream', '').strip(),
                'institute': entry.get('institute', '').strip(),
                'year': entry.get('year', '').strip(),
                'cgpa': entry.get('cgpa', '').strip()
            }
            structured_data["education"].append(entry)
    
    # Parse achievements
    achievement_data = {}
    for key, value in form_data.items():
        if key.startswith("achievements["):
            parts = key.split('][')
            index = int(parts[0].split('[')[1])
            field = parts[1].rstrip(']')
            if index not in achievement_data:
                achievement_data[index] = {}
            achievement_data[index][field] = value
    for i in sorted(achievement_data.keys()):
        # Only add if description is filled and not just default values
        entry = achievement_data[i]
        if entry.get('description', '').strip() and entry.get('description', '').strip() not in ['', '—', 'notfilled@email.com']:
            # Keep actual values without forcing dashes for empty fields
            entry = {
                'description': entry.get('description', '').strip(),
                'year': entry.get('year', '').strip()
            }
            structured_data["achievements"].append(entry)
    
    # Parse certifications
    certification_data = {}
    for key, value in form_data.items():
        if key.startswith("certifications["):
            parts = key.split('][')
            index = int(parts[0].split('[')[1])
            field = parts[1].rstrip(']')
            if index not in certification_data:
                certification_data[index] = {}
            certification_data[index][field] = value
    for i in sorted(certification_data.keys()):
        # Only add if description is filled and not just default values
        entry = certification_data[i]
        if entry.get('description', '').strip() and entry.get('description', '').strip() not in ['', '—', 'notfilled@email.com']:
            # Keep actual values without forcing dashes for empty fields
            entry = {
                'description': entry.get('description', '').strip(),
                'year': entry.get('year', '').strip()
            }
            structured_data["certifications"].append(entry)
    
    # Parse publications
    publication_data = {}
    for key, value in form_data.items():
        if key.startswith("publications["):
            parts = key.split('][')
            index = int(parts[0].split('[')[1])
            field = parts[1].rstrip(']')
            if index not in publication_data:
                publication_data[index] = {}
            publication_data[index][field] = value
    for i in sorted(publication_data.keys()):
        # Only add if description is filled and not just default values
        entry = publication_data[i]
        if entry.get('description', '').strip() and entry.get('description', '').strip() not in ['', '—', 'notfilled@email.com']:
            # Keep actual values without forcing dashes for empty fields
            entry = {
                'description': entry.get('description', '').strip(),
                'year': entry.get('year', '').strip()
            }
            structured_data["publications"].append(entry)
    
    # Parse internships
    internship_data = {}
    for key in form_data.keys():
        if key.startswith("internships["):
            parts = key.split('][')
            index = int(parts[0].split('[')[1])
            if index not in internship_data:
                internship_data[index] = {"points": []}
            if key.endswith("[points][]"):
                values = form_data.getlist(key)
                internship_data[index]["points"].extend(values)
            else:
                field = parts[1].rstrip(']')
                internship_data[index][field] = form_data[key]
    for i in sorted(internship_data.keys()):
        # Only add if at least one field is filled and not just default values
        entry = internship_data[i]
        filled_fields = [field for field in ['company', 'role', 'duration'] 
                        if entry.get(field, '').strip() and entry.get(field, '').strip() not in ['', '—', 'notfilled@email.com']]
        valid_points = [p for p in entry.get('points', []) if p.strip() and p.strip() not in ['', '—', 'notfilled@email.com']]
        if filled_fields or valid_points:
            # Keep actual values without forcing dashes for empty fields
            entry = {
                'company': entry.get('company', '').strip(),
                'role': entry.get('role', '').strip(),
                'duration': entry.get('duration', '').strip(),
                'points': entry.get('points', [])
            }
            structured_data["internships"].append(entry)
    
    # Parse work experience
    work_experience_data = {}
    for key in form_data.keys():
        if key.startswith("work_experience["):
            parts = key.split('][')
            index = int(parts[0].split('[')[1])
            if index not in work_experience_data:
                work_experience_data[index] = {"points": []}
            if key.endswith("[points][]"):
                values = form_data.getlist(key)
                work_experience_data[index]["points"].extend(values)
            else:
                field = parts[1].rstrip(']')
                work_experience_data[index][field] = form_data[key]
    for i in sorted(work_experience_data.keys()):
        # Only add if at least one field is filled and not just default values
        entry = work_experience_data[i]
        filled_fields = [field for field in ['company', 'position', 'duration'] 
                        if entry.get(field, '').strip() and entry.get(field, '').strip() not in ['', '—', 'notfilled@email.com']]
        if filled_fields:
            # Filter out empty points
            valid_points = [point.strip() for point in entry.get("points", []) 
                          if point.strip() and point.strip() not in ['', '—']]
            entry = {
                'company': entry.get('company', '').strip(),
                'position': entry.get('position', '').strip(),
                'duration': entry.get('duration', '').strip(),
                'points': valid_points
            }
            structured_data["work_experience"].append(entry)
    
    # Parse projects
    project_data = {}
    for key in form_data.keys():
        if key.startswith("projects["):
            parts = key.split('][')
            index = int(parts[0].split('[')[1])
            if index not in project_data:
                project_data[index] = {"points": []}
            if key.endswith("[points][]"):
                values = form_data.getlist(key)
                project_data[index]["points"].extend(values)
            else:
                field = parts[1].rstrip(']')
                project_data[index][field] = form_data[key]
    for i in sorted(project_data.keys()):
        # Only add if at least one field is filled and not just default values
        entry = project_data[i]
        filled_fields = [field for field in ['title', 'type', 'duration'] 
                        if entry.get(field, '').strip() and entry.get(field, '').strip() not in ['', '—', 'notfilled@email.com']]
        valid_points = [p for p in entry.get('points', []) if p.strip() and p.strip() not in ['', '—', 'notfilled@email.com']]
        if filled_fields or valid_points:
            # Keep actual values without forcing dashes for empty fields
            entry = {
                'title': entry.get('title', '').strip(),
                'type': entry.get('type', '').strip(),
                'duration': entry.get('duration', '').strip(),
                'repo_link': entry.get('repo_link', ''),
                'points': entry.get('points', [])
            }
            structured_data["projects"].append(entry)
    # Parse positions
    position_data = {}
    for key in form_data.keys():
        if key.startswith("positions["):
            parts = key.split('][')
            index = int(parts[0].split('[')[1])
            if index not in position_data:
                position_data[index] = {"points": []}
            if key.endswith("[points][]"):
                values = form_data.getlist(key)
                position_data[index]["points"].extend(values)
            else:
                field = parts[1].rstrip(']')
                position_data[index][field] = form_data[key]
    for i in sorted(position_data.keys()):
        # Only add if at least one field is filled and not just default values
        entry = position_data[i]
        filled_fields = [field for field in ['club', 'role', 'duration'] 
                        if entry.get(field, '').strip() and entry.get(field, '').strip() not in ['', '—', 'notfilled@email.com']]
        valid_points = [p for p in entry.get('points', []) if p.strip() and p.strip() not in ['', '—', 'notfilled@email.com']]
        if filled_fields or valid_points:
            # Keep actual values without forcing dashes for empty fields
            entry = {
                'club': entry.get('club', '').strip(),
                'role': entry.get('role', '').strip(),
                'duration': entry.get('duration', '').strip(),
                'points': entry.get('points', [])
            }
            structured_data["positions_of_responsibility"].append(entry)
    
    # Parse extracurricular activities
    extracurricular = form_data.getlist("extracurricular[]")
    structured_data["extracurricular"] = [activity.strip() for activity in extracurricular 
                                         if activity.strip() and activity.strip() not in ['', '—', 'notfilled@email.com']]
    
    # Parse languages
    languages = form_data.getlist("languages[]")
    structured_data["languages"] = [lang.strip() for lang in languages 
                                   if lang.strip() and lang.strip() not in ['', '—', 'notfilled@email.com']]
    
    # Parse technical skills
    technical_skills = form_data.getlist("technical_skills[]")
    structured_data["technical_skills"] = [skill.strip() for skill in technical_skills 
                                         if skill.strip() and skill.strip() not in ['', '—', 'notfilled@email.com']]
    
    # Parse categorized technical skills
    categorized_skills = {
        "programming_languages": [],
        "web_technologies": [],
        "database_management": [],
        "tools_and_technologies": []
    }
    
    # Extract skills by category (only one field per category)
    # Programming Languages
    skill = form_data.get("tech_prog_1", "")
    if skill and skill.strip() and skill.strip() not in ['', '—', 'notfilled@email.com']:
        # Split by comma and clean up each skill
        skills = [s.strip() for s in skill.split(',') if s.strip()]
        categorized_skills["programming_languages"].extend(skills)
    
    # Web Technologies
    skill = form_data.get("tech_web_1", "")
    if skill and skill.strip() and skill.strip() not in ['', '—', 'notfilled@email.com']:
        # Split by comma and clean up each skill
        skills = [s.strip() for s in skill.split(',') if s.strip()]
        categorized_skills["web_technologies"].extend(skills)
    
    # Database Management
    skill = form_data.get("tech_db_1", "")
    if skill and skill.strip() and skill.strip() not in ['', '—', 'notfilled@email.com']:
        # Split by comma and clean up each skill
        skills = [s.strip() for s in skill.split(',') if s.strip()]
        categorized_skills["database_management"].extend(skills)
    
    # Tools and Technologies
    skill = form_data.get("tech_tools_1", "")
    if skill and skill.strip() and skill.strip() not in ['', '—', 'notfilled@email.com']:
        # Split by comma and clean up each skill
        skills = [s.strip() for s in skill.split(',') if s.strip()]
        categorized_skills["tools_and_technologies"].extend(skills)
    
    # If we have categorized skills, use them; otherwise, create empty TechnicalSkillsCategory
    if any(categorized_skills.values()):
        structured_data["technical_skills"] = categorized_skills
    else:
        # Create empty TechnicalSkillsCategory object when no skills are provided
        structured_data["technical_skills"] = {
            "programming_languages": [],
            "web_technologies": [],
            "database_management": [],
            "tools_and_technologies": []
        }
    
    # Parse font settings
    logger.info(f"[DEBUG] Font settings from form_data:")
    logger.info(f"  - title_font_size: {form_data.get('title_font_size', 'NOT FOUND')}")
    logger.info(f"  - title_font_color: {form_data.get('title_font_color', 'NOT FOUND')}")
    logger.info(f"  - body_font_size: {form_data.get('body_font_size', 'NOT FOUND')}")
    logger.info(f"  - body_font_color: {form_data.get('body_font_color', 'NOT FOUND')}")
    logger.info(f"  - line_height: {form_data.get('line_height', 'NOT FOUND')}")
    logger.info(f"  - section_spacing_multiplier: {form_data.get('section_spacing_multiplier', 'NOT FOUND')}")
    
    structured_data["font_settings"] = {
        "title_font_size": form_data.get("title_font_size", "12px"),
        "title_font_color": form_data.get("title_font_color", "#4C5196"),
        "body_font_size": form_data.get("body_font_size", "12px"),
        "body_font_color": form_data.get("body_font_color", "#000000"),
        "line_height": form_data.get("line_height", "1.1"),
        "section_spacing_multiplier": form_data.get("section_spacing_multiplier", "1.0")
    }
    
    # Parse section_order (JSON string from hidden field)
    section_order_str = form_data.get("section_order", "")
    if section_order_str and section_order_str.strip():
        try:
            structured_data["section_order"] = json.loads(section_order_str)
            logger.info(f"[DEBUG] Parsed section_order: {structured_data['section_order']}")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse section_order JSON: {e}")
            structured_data["section_order"] = []
    else:
        structured_data["section_order"] = []

    # Parse custom_sections (JSON string from hidden field)
    custom_sections_str = form_data.get("custom_sections_json", "")
    if custom_sections_str and custom_sections_str.strip():
        try:
            structured_data["custom_sections"] = json.loads(custom_sections_str)
            logger.info(f"[DEBUG] Parsed custom_sections: {structured_data['custom_sections']}")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse custom_sections JSON: {e}")
            structured_data["custom_sections"] = []
    else:
        structured_data["custom_sections"] = []

    # After parsing all data
    logger.info("[DEBUG] Structured data after parsing dynamic form:")
    logger.info(pprint.pformat(structured_data))
    return structured_data


@app.get("/cv/{cv_id}")
async def get_cv_display(cv_id: str):
    """Serve the CV display page with download button"""
    try:
        display_file = BASE_PATH / f"generated/{cv_id}_display.html"
        if os.path.exists(display_file):
            with open(display_file, "r", encoding="utf-8") as f:
                content = f.read()
            return HTMLResponse(content=content)
        else:
            raise CVNotFoundError(f"CV display file not found for ID: {cv_id}")
    except CVNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error serving CV display: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving CV display")


@app.get("/cv/{cv_id}/html")
async def get_cv_html(cv_id: str):
    """Serve generated HTML CV"""
    try:
        html_file = BASE_PATH / f"generated/{cv_id}.html"
        if os.path.exists(html_file):
            return FileResponse(html_file, media_type="text/html")
        else:
            raise CVNotFoundError(f"CV HTML file not found for ID: {cv_id}")
    except CVNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error serving CV HTML: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving CV HTML")


@app.get("/cv/{cv_id}/pdf")
async def get_cv_pdf(cv_id: str):
    """Generate and serve PDF CV on-demand from HTML"""
    try:
        # Get CV data using service
        cv_document = cv_service.get_cv_data(cv_id)
        
        # Render PDF-specific HTML template
        cv_data_dict = cv_document.data.dict()
        logger.info(f"[DEBUG] PDF generation - cv_data_dict keys: {list(cv_data_dict.keys())}")
        logger.info(f"[DEBUG] PDF generation - font_settings: {cv_data_dict.get('font_settings', 'NOT FOUND')}")
        html_content = render_template('cv_template_pdf.html', {
            "cv_data": cv_document.data,
            **cv_data_dict
        })
        
        # Generate PDF using Playwright
        try:
            logger.info("Starting PDF generation with Playwright")
            pdf_bytes = await generate_pdf_with_playwright(html_content)
            logger.info(f"PDF generated successfully, size: {len(pdf_bytes)} bytes")
        except Exception as e:
            logger.error(f"Exception during PDF generation: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        
        # Create filename from user's name
        pdf_filename = f"{create_filename(cv_document.data.personal_info.full_name)}.pdf"
        
        logger.info(f"PDF generated successfully for CV: {cv_id}")
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={pdf_filename}"}
        )
        
    except CVNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        raise PDFGenerationError(f"Failed to generate PDF: {str(e)}")


@app.get("/api/v1/cvs")
async def list_cvs():
    """List all CVs with metadata"""
    try:
        cvs = cv_service.list_cvs()
        return {"cvs": cvs, "total": len(cvs)}
    except Exception as e:
        logger.error(f"Error listing CVs: {str(e)}")
        raise HTTPException(status_code=500, detail="Error listing CVs")


@app.get("/api/v1/cv/{cv_id}")
async def get_cv_data_api(cv_id: str):
    """Get CV data via API"""
    try:
        cv_document = cv_service.get_cv_data(cv_id)
        return cv_document.dict()
    except CVNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting CV data: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting CV data")


@app.delete("/api/v1/cv/{cv_id}")
async def delete_cv_api(cv_id: str):
    """Delete CV via API"""
    try:
        cv_service.delete_cv(cv_id)
        return {"message": f"CV {cv_id} deleted successfully"}
    except CVNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error deleting CV: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting CV")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)