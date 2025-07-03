from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import uuid
import subprocess
from pathlib import Path
from typing import Optional

app = FastAPI(title="CV Generator", description="Generate PDF resumes from LaTeX templates")

# Create directories
Path("static").mkdir(exist_ok=True)
Path("templates").mkdir(exist_ok=True)
Path("generated").mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the CV form"""
    return templates.TemplateResponse("form.html", {"request": request})

@app.post("/generate")
async def generate_cv(
    request: Request,
    # Personal Information
    full_name: str = Form(...),
    highest_education: str = Form(...),
    city: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    
    # Education (3 entries)
    edu_1_qual: str = Form(...),
    edu_1_stream: str = Form(...),
    edu_1_institute: str = Form(...),
    edu_1_year: str = Form(...),
    edu_1_cgpa: str = Form(...),
    
    edu_2_qual: str = Form(default=""),
    edu_2_stream: str = Form(default=""),
    edu_2_institute: str = Form(default=""),
    edu_2_year: str = Form(default=""),
    edu_2_cgpa: str = Form(default=""),
    
    edu_3_qual: str = Form(default=""),
    edu_3_stream: str = Form(default=""),
    edu_3_institute: str = Form(default=""),
    edu_3_year: str = Form(default=""),
    edu_3_cgpa: str = Form(default=""),
    
    # Achievements (2 entries)
    ach_1_desc: str = Form(...),
    ach_1_year: str = Form(...),
    ach_2_desc: str = Form(default=""),
    ach_2_year: str = Form(default=""),
    
    # Internships (2 entries)
    intern_1_company: str = Form(...),
    intern_1_role: str = Form(...),
    intern_1_duration: str = Form(...),
    intern_1_point_1: str = Form(...),
    intern_1_point_2: str = Form(...),
    
    intern_2_company: str = Form(default=""),
    intern_2_role: str = Form(default=""),
    intern_2_duration: str = Form(default=""),
    intern_2_point_1: str = Form(default=""),
    intern_2_point_2: str = Form(default=""),
    
    # Projects (2 entries)
    proj_1_title: str = Form(...),
    proj_1_type: str = Form(...),
    proj_1_duration: str = Form(...),
    proj_1_point_1: str = Form(...),
    proj_1_point_2: str = Form(...),
    
    proj_2_title: str = Form(default=""),
    proj_2_type: str = Form(default=""),
    proj_2_duration: str = Form(default=""),
    proj_2_point_1: str = Form(default=""),
    proj_2_point_2: str = Form(default=""),
    
    # Positions of Responsibility (2 entries)
    por_1_club: str = Form(...),
    por_1_role: str = Form(...),
    por_1_duration: str = Form(...),
    por_1_point_1: str = Form(...),
    por_1_point_2: str = Form(...),
    
    por_2_club: str = Form(default=""),
    por_2_role: str = Form(default=""),
    por_2_duration: str = Form(default=""),
    por_2_point_1: str = Form(default=""),
    por_2_point_2: str = Form(default=""),
    
    # Extra Curricular Activities (5 entries)
    extracur_1_desc: str = Form(...),
    extracur_2_desc: str = Form(default=""),
    extracur_3_desc: str = Form(default=""),
    extracur_4_desc: str = Form(default=""),
    extracur_5_desc: str = Form(default=""),
    
    # Technical Skills (5 entries)
    techskill_1: str = Form(...),
    techskill_2: str = Form(default=""),
    techskill_3: str = Form(default=""),
    techskill_4: str = Form(default=""),
    techskill_5: str = Form(default=""),
):
    """Generate CV from form data"""
    try:
        # Generate unique ID for this CV
        cv_id = str(uuid.uuid4())
        
        # Read the LaTeX template
        with open("1pg_CV.tex", "r") as f:
            template_content = f.read()
        
        # Create variables dictionary
        variables = {
            "full-name": full_name,
            "highest-education": highest_education,
            "city": city,
            "phone": phone,
            "email": email,
            "edu-1-qual": edu_1_qual,
            "edu-1-stream": edu_1_stream,
            "edu-1-institute": edu_1_institute,
            "edu-1-year": edu_1_year,
            "edu-1-cgpa": edu_1_cgpa,
            "edu-2-qual": edu_2_qual,
            "edu-2-stream": edu_2_stream,
            "edu-2-institute": edu_2_institute,
            "edu-2-year": edu_2_year,
            "edu-2-cgpa": edu_2_cgpa,
            "edu-3-qual": edu_3_qual,
            "edu-3-stream": edu_3_stream,
            "edu-3-institute": edu_3_institute,
            "edu-3-year": edu_3_year,
            "edu-3-cgpa": edu_3_cgpa,
            "ach-1-desc": ach_1_desc,
            "ach-1-year": ach_1_year,
            "ach-2-desc": ach_2_desc,
            "ach-2-year": ach_2_year,
            "intern-1-company": intern_1_company,
            "intern-1-role": intern_1_role,
            "intern-1-duration": intern_1_duration,
            "intern-1-point-1": intern_1_point_1,
            "intern-1-point-2": intern_1_point_2,
            "intern-2-company": intern_2_company,
            "intern-2-role": intern_2_role,
            "intern-2-duration": intern_2_duration,
            "intern-2-point-1": intern_2_point_1,
            "intern-2-point-2": intern_2_point_2,
            "proj-1-title": proj_1_title,
            "proj-1-type": proj_1_type,
            "proj-1-duration": proj_1_duration,
            "proj-1-point-1": proj_1_point_1,
            "proj-1-point-2": proj_1_point_2,
            "proj-2-title": proj_2_title,
            "proj-2-type": proj_2_type,
            "proj-2-duration": proj_2_duration,
            "proj-2-point-1": proj_2_point_1,
            "proj-2-point-2": proj_2_point_2,
            "por-1-club": por_1_club,
            "por-1-role": por_1_role,
            "por-1-duration": por_1_duration,
            "por-1-point-1": por_1_point_1,
            "por-1-point-2": por_1_point_2,
            "por-2-club": por_2_club,
            "por-2-role": por_2_role,
            "por-2-duration": por_2_duration,
            "por-2-point-1": por_2_point_1,
            "por-2-point-2": por_2_point_2,
            "extracur-1-desc": extracur_1_desc,
            "extracur-2-desc": extracur_2_desc,
            "extracur-3-desc": extracur_3_desc,
            "extracur-4-desc": extracur_4_desc,
            "extracur-5-desc": extracur_5_desc,
            "techskill-1": techskill_1,
            "techskill-2": techskill_2,
            "techskill-3": techskill_3,
            "techskill-4": techskill_4,
            "techskill-5": techskill_5,
        }
        
        # Fill template with variables
        filled_template = template_content
        for key, value in variables.items():
            filled_template = filled_template.replace(f"{{{{{{{key}}}}}}}", str(value) if value else "")
        
        # Save filled LaTeX file for later PDF generation
        latex_file = f"generated/{cv_id}.tex"
        with open(latex_file, "w") as f:
            f.write(filled_template)
        
        # Save user's name for PDF filename
        import json
        user_data = {"full_name": full_name}
        data_file_path = f"generated/{cv_id}_data.json"
        with open(data_file_path, "w") as f:
            json.dump(user_data, f)
        print(f"Saved user data to: {data_file_path}")  # Debug line
        
        # Read HTML template and fill with variables
        html_template_path = "html_template.html"
        if not os.path.exists(html_template_path):
            raise HTTPException(status_code=500, detail=f"HTML template not found: {html_template_path}")
        
        with open(html_template_path, "r") as f:
            html_template_content = f.read()
        
        # Fill HTML template with variables (escape HTML for safety)
        import html
        filled_html_template = html_template_content
        for key, value in variables.items():
            escaped_html_value = html.escape(str(value)) if value else ""
            filled_html_template = filled_html_template.replace(f"{{{{{{{key}}}}}}}", escaped_html_value)
        
        # Generate HTML file
        html_file = f"generated/{cv_id}.html"
        with open(html_file, "w") as f:
            f.write(filled_html_template)
        
        # Create a clean filename from the user's name
        def create_filename(name):
            # Remove special characters and replace spaces with underscores
            import re
            clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
            return clean_name.replace(' ', '_').lower()
        
        pdf_filename = f"{create_filename(full_name)}.pdf"
        
        # Return the generated HTML with a download button
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
        
        # Insert the download button into the HTML
        html_with_button = filled_html_template.replace(
            '<body>', 
            f'<body>{download_button}'
        )
        
        # Save the HTML content to serve at the CV-specific URL
        with open(f"generated/{cv_id}_display.html", "w") as f:
            f.write(html_with_button)
        
        # Redirect to the CV-specific URL
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/cv/{cv_id}", status_code=302)
        
    except Exception as e:
        import traceback
        error_details = f"Error generating CV: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(error_details)  # Log to console for debugging
        raise HTTPException(status_code=500, detail=f"Error generating CV: {str(e)}")

@app.get("/cv/{cv_id}")
async def get_cv_display(cv_id: str):
    """Serve the CV display page with download button"""
    display_file = f"generated/{cv_id}_display.html"
    if os.path.exists(display_file):
        with open(display_file, "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    raise HTTPException(status_code=404, detail="CV not found")

@app.get("/cv/{cv_id}/html")
async def get_cv_html(cv_id: str):
    """Serve generated HTML CV"""
    html_file = f"generated/{cv_id}.html"
    if os.path.exists(html_file):
        return FileResponse(html_file, media_type="text/html")
    raise HTTPException(status_code=404, detail="CV not found")

@app.get("/cv/{cv_id}/pdf")
async def get_cv_pdf(cv_id: str):
    """Generate and serve PDF CV on-demand"""
    latex_file = f"generated/{cv_id}.tex"
    pdf_file = f"generated/{cv_id}.pdf"
    data_file = f"generated/{cv_id}_data.json"
    
    # Check if LaTeX file exists
    if not os.path.exists(latex_file):
        raise HTTPException(status_code=404, detail="CV not found")
    
    # Generate PDF using pdflatex
    try:
        subprocess.run([
            "pdflatex", "-output-directory=generated", latex_file
        ], check=True, cwd=".")
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail="Error generating PDF")
    
    # Get the user's name for filename
    def create_filename(name):
        import re
        clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
        return clean_name.replace(' ', '_').lower()
    
    pdf_filename = f"cv_{cv_id}.pdf"  # Default filename
    print(f"Looking for data file: {data_file}")  # Debug
    print(f"Data file exists: {os.path.exists(data_file)}")  # Debug
    
    if os.path.exists(data_file):
        try:
            import json
            with open(data_file, "r") as f:
                user_data = json.load(f)
            print(f"Loaded user data: {user_data}")  # Debug
            pdf_filename = f"{create_filename(user_data['full_name'])}.pdf"
            print(f"Generated filename: {pdf_filename}")  # Debug
        except Exception as e:
            print(f"Error reading user data: {e}")  # Debug
            pass  # Use default filename if there's an error
    
    # Serve the generated PDF
    if os.path.exists(pdf_file):
        return FileResponse(pdf_file, media_type="application/pdf", filename=pdf_filename)
    else:
        raise HTTPException(status_code=500, detail="PDF generation failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)