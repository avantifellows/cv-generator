# from fastapi import FastAPI, Request, Form, HTTPException
# from fastapi.responses import HTMLResponse, FileResponse
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates
# from jinja2 import Environment, FileSystemLoader
# import os
# import uuid
# from pathlib import Path
# from typing import Optional
# import json
# import html
# import re
# from datetime import datetime
# import weasyprint
# from io import BytesIO

# app = FastAPI(title="CV Generator", description="Generate PDF resumes from HTML templates")

# # Create directories
# Path("static").mkdir(exist_ok=True)
# Path("templates").mkdir(exist_ok=True)
# Path("generated").mkdir(exist_ok=True)

# app.mount("/static", StaticFiles(directory="static"), name="static")
# templates = Jinja2Templates(directory="templates")


# def create_structured_data(form_variables: dict) -> dict:
#     """Convert form variables to structured data for templates"""
#     return {
#         "personal_info": {
#             "full_name": form_variables.get("full_name", ""),
#             "highest_education": form_variables.get("highest_education", ""),
#             "city": form_variables.get("city", ""),
#             "phone": form_variables.get("phone", ""),
#             "email": form_variables.get("email", "")
#         },
#         "education": [
#             {
#                 "qualification": form_variables.get("edu_1_qual", ""),
#                 "stream": form_variables.get("edu_1_stream", ""),
#                 "institute": form_variables.get("edu_1_institute", ""),
#                 "year": form_variables.get("edu_1_year", ""),
#                 "cgpa": form_variables.get("edu_1_cgpa", "")
#             },
#             {
#                 "qualification": form_variables.get("edu_2_qual", ""),
#                 "stream": form_variables.get("edu_2_stream", ""),
#                 "institute": form_variables.get("edu_2_institute", ""),
#                 "year": form_variables.get("edu_2_year", ""),
#                 "cgpa": form_variables.get("edu_2_cgpa", "")
#             },
#             {
#                 "qualification": form_variables.get("edu_3_qual", ""),
#                 "stream": form_variables.get("edu_3_stream", ""),
#                 "institute": form_variables.get("edu_3_institute", ""),
#                 "year": form_variables.get("edu_3_year", ""),
#                 "cgpa": form_variables.get("edu_3_cgpa", "")
#             }
#         ],
#         "achievements": [
#             {
#                 "description": form_variables.get("ach_1_desc", ""),
#                 "year": form_variables.get("ach_1_year", "")
#             },
#             {
#                 "description": form_variables.get("ach_2_desc", ""),
#                 "year": form_variables.get("ach_2_year", "")
#             }
#         ],
#         "internships": [
#             {
#                 "company": form_variables.get("intern_1_company", ""),
#                 "role": form_variables.get("intern_1_role", ""),
#                 "duration": form_variables.get("intern_1_duration", ""),
#                 "points": [
#                     form_variables.get("intern_1_point_1", ""),
#                     form_variables.get("intern_1_point_2", "")
#                 ]
#             },
#             {
#                 "company": form_variables.get("intern_2_company", ""),
#                 "role": form_variables.get("intern_2_role", ""),
#                 "duration": form_variables.get("intern_2_duration", ""),
#                 "points": [
#                     form_variables.get("intern_2_point_1", ""),
#                     form_variables.get("intern_2_point_2", "")
#                 ]
#             }
#         ],
#         "projects": [
#             {
#                 "title": form_variables.get("proj_1_title", ""),
#                 "type": form_variables.get("proj_1_type", ""),
#                 "duration": form_variables.get("proj_1_duration", ""),
#                 "points": [
#                     form_variables.get("proj_1_point_1", ""),
#                     form_variables.get("proj_1_point_2", "")
#                 ]
#             },
#             {
#                 "title": form_variables.get("proj_2_title", ""),
#                 "type": form_variables.get("proj_2_type", ""),
#                 "duration": form_variables.get("proj_2_duration", ""),
#                 "points": [
#                     form_variables.get("proj_2_point_1", ""),
#                     form_variables.get("proj_2_point_2", "")
#                 ]
#             }
#         ],
#         "positions_of_responsibility": [
#             {
#                 "club": form_variables.get("por_1_club", ""),
#                 "role": form_variables.get("por_1_role", ""),
#                 "duration": form_variables.get("por_1_duration", ""),
#                 "points": [
#                     form_variables.get("por_1_point_1", ""),
#                     form_variables.get("por_1_point_2", "")
#                 ]
#             },
#             {
#                 "club": form_variables.get("por_2_club", ""),
#                 "role": form_variables.get("por_2_role", ""),
#                 "duration": form_variables.get("por_2_duration", ""),
#                 "points": [
#                     form_variables.get("por_2_point_1", ""),
#                     form_variables.get("por_2_point_2", "")
#                 ]
#             }
#         ],
#         "extracurricular": [
#             form_variables.get("extracur_1_desc", ""),
#             form_variables.get("extracur_2_desc", ""),
#             form_variables.get("extracur_3_desc", ""),
#             form_variables.get("extracur_4_desc", ""),
#             form_variables.get("extracur_5_desc", "")
#         ],
#         "technical_skills": [
#             form_variables.get("techskill_1", ""),
#             form_variables.get("techskill_2", ""),
#             form_variables.get("techskill_3", ""),
#             form_variables.get("techskill_4", ""),
#             form_variables.get("techskill_5", "")
#         ]
#     }

# def filter_empty_sections(data: dict) -> dict:
#     """Remove empty optional sections from data"""
#     filtered_data = data.copy()
    
#     # Filter education entries (keep only non-empty qualifications)
#     filtered_data['education'] = [edu for edu in data['education'] if edu.get('qualification', '').strip()]
    
#     # Filter achievements (keep only non-empty descriptions)
#     filtered_data['achievements'] = [ach for ach in data['achievements'] if ach.get('description', '').strip()]
    
#     # Filter internships (keep only non-empty companies)
#     filtered_data['internships'] = [intern for intern in data['internships'] if intern.get('company', '').strip()]
    
#     # Filter projects (keep only non-empty titles)
#     filtered_data['projects'] = [proj for proj in data['projects'] if proj.get('title', '').strip()]
    
#     # Filter positions (keep only non-empty clubs)
#     filtered_data['positions_of_responsibility'] = [pos for pos in data['positions_of_responsibility'] if pos.get('club', '').strip()]
    
#     # Filter extracurricular (remove empty strings)
#     filtered_data['extracurricular'] = [activity for activity in data['extracurricular'] if activity and activity.strip()]
    
#     # Filter technical skills (remove empty strings)
#     filtered_data['technical_skills'] = [skill for skill in data['technical_skills'] if skill and skill.strip()]
    
#     return filtered_data

# def render_template(template_name: str, data: dict) -> str:
#     """Render Jinja2 template with data"""
#     template = templates.env.get_template(template_name)
#     return template.render(**data)

# def create_filename(name: str) -> str:
#     """Create a clean filename from the user's name"""
#     clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
#     return clean_name.replace(' ', '_').lower()

# @app.get("/", response_class=HTMLResponse)
# async def home(request: Request):
#     """Serve the CV form"""
#     return templates.TemplateResponse("form.html", {"request": request})

# @app.get("/test", response_class=HTMLResponse)
# async def test_form(request: Request):
#     """Serve the CV form pre-filled with test data"""
#     try:
#         # Load test data (now in form field format)
#         with open("test_data.json", "r") as f:
#             form_data = json.load(f)
        
#         return templates.TemplateResponse("form.html", {"request": request, "form_data": form_data})
        
#     except Exception as e:
#         import traceback
#         error_details = f"Error loading test data: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
#         print(error_details)
#         # Fall back to empty form
#         return templates.TemplateResponse("form.html", {"request": request})

# @app.post("/generate")
# async def generate_cv(
#     request: Request,
#     # Personal Information
#     full_name: str = Form(...),
#     highest_education: str = Form(...),
#     city: str = Form(...),
#     phone: str = Form(...),
#     email: str = Form(...),
    
#     # Education (3 entries)
#     edu_1_qual: str = Form(...),
#     edu_1_stream: str = Form(...),
#     edu_1_institute: str = Form(...),
#     edu_1_year: str = Form(...),
#     edu_1_cgpa: str = Form(...),
    
#     edu_2_qual: str = Form(default=""),
#     edu_2_stream: str = Form(default=""),
#     edu_2_institute: str = Form(default=""),
#     edu_2_year: str = Form(default=""),
#     edu_2_cgpa: str = Form(default=""),
    
#     edu_3_qual: str = Form(default=""),
#     edu_3_stream: str = Form(default=""),
#     edu_3_institute: str = Form(default=""),
#     edu_3_year: str = Form(default=""),
#     edu_3_cgpa: str = Form(default=""),
    
#     # Achievements (2 entries)
#     ach_1_desc: str = Form(...),
#     ach_1_year: str = Form(...),
#     ach_2_desc: str = Form(default=""),
#     ach_2_year: str = Form(default=""),
    
#     # Internships (2 entries)
#     intern_1_company: str = Form(...),
#     intern_1_role: str = Form(...),
#     intern_1_duration: str = Form(...),
#     intern_1_point_1: str = Form(...),
#     intern_1_point_2: str = Form(...),
    
#     intern_2_company: str = Form(default=""),
#     intern_2_role: str = Form(default=""),
#     intern_2_duration: str = Form(default=""),
#     intern_2_point_1: str = Form(default=""),
#     intern_2_point_2: str = Form(default=""),
    
#     # Projects (2 entries)
#     proj_1_title: str = Form(...),
#     proj_1_type: str = Form(...),
#     proj_1_duration: str = Form(...),
#     proj_1_point_1: str = Form(...),
#     proj_1_point_2: str = Form(...),
    
#     proj_2_title: str = Form(default=""),
#     proj_2_type: str = Form(default=""),
#     proj_2_duration: str = Form(default=""),
#     proj_2_point_1: str = Form(default=""),
#     proj_2_point_2: str = Form(default=""),
    
#     # Positions of Responsibility (2 entries)
#     por_1_club: str = Form(...),
#     por_1_role: str = Form(...),
#     por_1_duration: str = Form(...),
#     por_1_point_1: str = Form(...),
#     por_1_point_2: str = Form(...),
    
#     por_2_club: str = Form(default=""),
#     por_2_role: str = Form(default=""),
#     por_2_duration: str = Form(default=""),
#     por_2_point_1: str = Form(default=""),
#     por_2_point_2: str = Form(default=""),
    
#     # Extra Curricular Activities (5 entries)
#     extracur_1_desc: str = Form(...),
#     extracur_2_desc: str = Form(default=""),
#     extracur_3_desc: str = Form(default=""),
#     extracur_4_desc: str = Form(default=""),
#     extracur_5_desc: str = Form(default=""),
    
#     # Technical Skills (5 entries)
#     techskill_1: str = Form(...),
#     techskill_2: str = Form(default=""),
#     techskill_3: str = Form(default=""),
#     techskill_4: str = Form(default=""),
#     techskill_5: str = Form(default=""),
# ):
#     """Generate CV from form data"""
#     try:
#         # Generate unique ID for this CV
#         cv_id = str(uuid.uuid4())
        
#         # Create form variables dictionary
#         form_variables = {
#             "full_name": full_name,
#             "highest_education": highest_education,
#             "city": city,
#             "phone": phone,
#             "email": email,
#             "edu_1_qual": edu_1_qual,
#             "edu_1_stream": edu_1_stream,
#             "edu_1_institute": edu_1_institute,
#             "edu_1_year": edu_1_year,
#             "edu_1_cgpa": edu_1_cgpa,
#             "edu_2_qual": edu_2_qual,
#             "edu_2_stream": edu_2_stream,
#             "edu_2_institute": edu_2_institute,
#             "edu_2_year": edu_2_year,
#             "edu_2_cgpa": edu_2_cgpa,
#             "edu_3_qual": edu_3_qual,
#             "edu_3_stream": edu_3_stream,
#             "edu_3_institute": edu_3_institute,
#             "edu_3_year": edu_3_year,
#             "edu_3_cgpa": edu_3_cgpa,
#             "ach_1_desc": ach_1_desc,
#             "ach_1_year": ach_1_year,
#             "ach_2_desc": ach_2_desc,
#             "ach_2_year": ach_2_year,
#             "intern_1_company": intern_1_company,
#             "intern_1_role": intern_1_role,
#             "intern_1_duration": intern_1_duration,
#             "intern_1_point_1": intern_1_point_1,
#             "intern_1_point_2": intern_1_point_2,
#             "intern_2_company": intern_2_company,
#             "intern_2_role": intern_2_role,
#             "intern_2_duration": intern_2_duration,
#             "intern_2_point_1": intern_2_point_1,
#             "intern_2_point_2": intern_2_point_2,
#             "proj_1_title": proj_1_title,
#             "proj_1_type": proj_1_type,
#             "proj_1_duration": proj_1_duration,
#             "proj_1_point_1": proj_1_point_1,
#             "proj_1_point_2": proj_1_point_2,
#             "proj_2_title": proj_2_title,
#             "proj_2_type": proj_2_type,
#             "proj_2_duration": proj_2_duration,
#             "proj_2_point_1": proj_2_point_1,
#             "proj_2_point_2": proj_2_point_2,
#             "por_1_club": por_1_club,
#             "por_1_role": por_1_role,
#             "por_1_duration": por_1_duration,
#             "por_1_point_1": por_1_point_1,
#             "por_1_point_2": por_1_point_2,
#             "por_2_club": por_2_club,
#             "por_2_role": por_2_role,
#             "por_2_duration": por_2_duration,
#             "por_2_point_1": por_2_point_1,
#             "por_2_point_2": por_2_point_2,
#             "extracur_1_desc": extracur_1_desc,
#             "extracur_2_desc": extracur_2_desc,
#             "extracur_3_desc": extracur_3_desc,
#             "extracur_4_desc": extracur_4_desc,
#             "extracur_5_desc": extracur_5_desc,
#             "techskill_1": techskill_1,
#             "techskill_2": techskill_2,
#             "techskill_3": techskill_3,
#             "techskill_4": techskill_4,
#             "techskill_5": techskill_5,
#         }
        
#         # Convert form data to structured format
#         user_data = create_structured_data(form_variables)
        
#         # Filter out empty optional sections
#         filtered_data = filter_empty_sections(user_data)
        
        
#         # Save complete user data for PDF filename and future editing
#         complete_user_data = {
#             "metadata": {
#                 "cv_id": cv_id,
#                 "created_at": datetime.utcnow().isoformat(),
#                 "last_modified": datetime.utcnow().isoformat(),
#                 "version": "1.0"
#             },
#             **filtered_data
#         }
        
#         data_file_path = f"generated/{cv_id}_data.json"
#         with open(data_file_path, "w") as f:
#             json.dump(complete_user_data, f, indent=2)
#         print(f"Saved user data to: {data_file_path}")  # Debug line
        
#         # Render HTML template
#         filled_html_template = render_template('cv_template.html', filtered_data)
        
#         # Generate HTML file
#         html_file = f"generated/{cv_id}.html"
#         with open(html_file, "w") as f:
#             f.write(filled_html_template)
        
#         # Create a clean filename from the user's name
        
#         pdf_filename = f"{create_filename(full_name)}.pdf"
        
#         # Return the generated HTML with a download button
#         download_button = f"""
#         <div style="position: fixed; top: 20px; right: 20px; z-index: 1000;">
#             <a href="/cv/{cv_id}/pdf" download="{pdf_filename}" 
#                style="background-color: #4C5196; color: white; padding: 10px 20px; 
#                       text-decoration: none; border-radius: 5px; font-weight: bold;
#                       box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
#                 📄 Download PDF
#             </a>
#         </div>
#         """
        
#         # Insert the download button into the HTML
#         html_with_button = filled_html_template.replace(
#             '<body>', 
#             f'<body>{download_button}'
#         )
        
#         # Save the HTML content to serve at the CV-specific URL
#         with open(f"generated/{cv_id}_display.html", "w") as f:
#             f.write(html_with_button)
        
#         # Redirect to the CV-specific URL
#         from fastapi.responses import RedirectResponse
#         return RedirectResponse(url=f"/cv/{cv_id}", status_code=302)
        
#     except Exception as e:
#         import traceback
#         error_details = f"Error generating CV: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
#         print(error_details)  # Log to console for debugging
#         raise HTTPException(status_code=500, detail=f"Error generating CV: {str(e)}")

# @app.get("/cv/{cv_id}")
# async def get_cv_display(cv_id: str):
#     """Serve the CV display page with download button"""
#     display_file = f"generated/{cv_id}_display.html"
#     if os.path.exists(display_file):
#         with open(display_file, "r") as f:
#             content = f.read()
#         return HTMLResponse(content=content)
#     raise HTTPException(status_code=404, detail="CV not found")

# @app.get("/cv/{cv_id}/html")
# async def get_cv_html(cv_id: str):
#     """Serve generated HTML CV"""
#     html_file = f"generated/{cv_id}.html"
#     if os.path.exists(html_file):
#         return FileResponse(html_file, media_type="text/html")
#     raise HTTPException(status_code=404, detail="CV not found")

# @app.get("/cv/{cv_id}/pdf")
# async def get_cv_pdf(cv_id: str):
#     """Generate and serve PDF CV on-demand from HTML"""
#     data_file = f"generated/{cv_id}_data.json"
    
#     # Check if data file exists
#     if not os.path.exists(data_file):
#         raise HTTPException(status_code=404, detail="CV not found")
    
#     # Read the user data
#     try:
#         with open(data_file, "r") as f:
#             user_data = json.load(f)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="Error reading CV data")
    
#     # Render the PDF-specific HTML template
#     try:
#         html_content = render_template('cv_template_pdf.html', user_data)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error rendering template: {str(e)}")
    
#     # Generate PDF using weasyprint
#     try:
#         pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")
    
#     # Get the user's name for filename
#     pdf_filename = f"cv_{cv_id}.pdf"  # Default filename
    
#     try:
#         if 'personal_info' in user_data and 'full_name' in user_data['personal_info']:
#             pdf_filename = f"{create_filename(user_data['personal_info']['full_name'])}.pdf"
#         elif 'full_name' in user_data:  # Fallback for old format
#             pdf_filename = f"{create_filename(user_data['full_name'])}.pdf"
#     except Exception as e:
#         pass  # Use default filename if there's an error
    
#     # Return the PDF as a response
#     from fastapi.responses import Response
#     return Response(
#         content=pdf_bytes,
#         media_type="application/pdf",
#         headers={"Content-Disposition": f"attachment; filename={pdf_filename}"}
#     )

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)