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
from mangum import Mangum
from playwright.async_api import async_playwright

# Clean imports for Playwright-based PDF generation

# Import our new models and services
from app.models.cv_data import CVData, CVGenerateRequest, CVGenerateResponse
from app.services.cv_service import CVService
from app.core.exceptions import CVGenerationError, CVNotFoundError, TemplateError, PDFGenerationError
from app.core.logging import setup_logging, get_logger

# Setup logging
setup_logging(level="INFO")
logger = get_logger(__name__)

# Define base path for Lambda's writable directory
BASE_PATH = Path("/tmp") if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") else Path(".")

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
    """Serve the dynamic CV form"""
    return templates.TemplateResponse("form.html", {"request": request})




@app.get("/test", response_class=HTMLResponse)
async def test_form(request: Request):
    """Serve the CV form pre-filled with test data"""
    try:
        # Load structured test data directly (form now supports this format)
        with open("test_data_structured.json", "r") as f:
            structured_data = json.load(f)
        
        return templates.TemplateResponse("form.html", {"request": request, "form_data": structured_data})
        
    except Exception as e:
        logger.error(f"Error loading test data: {str(e)}")
        # Fall back to empty form
        return templates.TemplateResponse("form.html", {"request": request})


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
        html_content = render_template('cv_template_pdf.html', cv_data.dict())
        
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
        # Check if this is dynamic form data (has array fields)
        is_dynamic = any(key.startswith(('education[', 'achievements[', 'internships[', 'projects[', 'positions[')) 
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
        
        # Generate CV using service
        logger.info(f"[DEBUG] cv_data.dict(): {cv_data.dict()}")
        cv_id = cv_service.generate_cv(cv_data)
        
        # Generate HTML file for display
        html_content = render_template('cv_template.html', cv_data.dict())
        
        # Save HTML file
        html_file = BASE_PATH / f"generated/{cv_id}.html"
        with open(html_file, "w") as f:
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
        with open(display_html_file, "w") as f:
            f.write(html_with_button)
        
        logger.info(f"CV generated successfully: {cv_id}")
        
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
        "achievements": [],
        "internships": [],
        "projects": [],
        "positions_of_responsibility": [],
        "extracurricular": [],
        "technical_skills": []
    }
    # Parse personal info
    structured_data["personal_info"] = {
        "full_name": form_data.get("full_name", ""),
        "highest_education": form_data.get("highest_education", ""),
        "city": form_data.get("city", ""),
        "phone": form_data.get("phone", ""),
        "email": form_data.get("email", "")
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
        structured_data["education"].append(education_data[i])
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
        structured_data["achievements"].append(achievement_data[i])
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
        structured_data["internships"].append(internship_data[i])
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
        structured_data["projects"].append(project_data[i])
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
        structured_data["positions_of_responsibility"].append(position_data[i])
    # Parse extracurricular activities
    extracurricular = form_data.getlist("extracurricular[]")
    structured_data["extracurricular"] = [activity for activity in extracurricular if activity.strip()]
    # Parse technical skills
    technical_skills = form_data.getlist("technical_skills[]")
    structured_data["technical_skills"] = [skill for skill in technical_skills if skill.strip()]
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
            with open(display_file, "r") as f:
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
        html_content = render_template('cv_template_pdf.html', cv_document.data.dict())
        
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


#if __name__ == "__main__":
#    import uvicorn
#    uvicorn.run(app, host="0.0.0.0", port=8000)

logger.info("Creating Mangum handler")
handler = Mangum(app)
logger.info("Mangum handler created successfully")

# import os

# def handler(event, context):
#     print("DEBUG: Handler was called")
#     return {"status": "ok"}