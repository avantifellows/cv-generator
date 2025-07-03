# CV Generator - S3 Integration TODOs

## 📋 Progress Summary

**Overall Progress**: 🟢 Task 1 Complete | 🔄 9 Tasks Remaining

| Task | Status | Description |
|------|--------|-------------|
| ✅ **Task 1** | **COMPLETED** | Dynamic Content Rendering (Optional Fields) |
| ⏳ Task 2 | Pending | Enhanced JSON Data Storage |
| ⏳ Task 2 | Pending | AWS S3 Integration Setup |
| ⏳ Task 3 | Pending | S3 Upload Integration |
| ⏳ Task 4 | Pending | Search Functionality |
| ⏳ Task 5 | Pending | Resume Editing Functionality |
| ⏳ Task 6 | Pending | Enhanced Search Interface |
| ⏳ Task 7 | Pending | Environment Configuration |
| ⏳ Task 8 | Pending | Error Handling and Logging |
| ⏳ Task 9 | Pending | Security Enhancements |

**Latest Update**: Task 1 completed with dynamic content rendering, conditional templates, and comprehensive testing framework.

---

## Overview
This document outlines the tasks needed to enhance the CV Generator with S3 storage for persistent data management, search capabilities, and resume editing functionality.

## Current Architecture
- **Local storage**: Generated files stored in `generated/` directory
- **Temporary**: Files exist only on the server instance
- **Limited**: No search, edit, or persistence capabilities

## Target Architecture
- **S3 storage**: All user data and generated files stored in AWS S3
- **Persistent**: Data survives server restarts and deployments
- **Searchable**: Find resumes by various criteria
- **Editable**: Reload and modify existing resumes

---

## ✅ Task 1: Dynamic Content Rendering (Optional Fields) - COMPLETED

**Status**: ✅ **COMPLETED** (July 3, 2025)

### Description
Modify the template system to conditionally render sections based on whether optional fields contain data. This ensures that empty sections (like unused internships, projects, or extracurricular activities) don't appear in the final output.

### ✅ Implementation Summary
- **Jinja2 Templates**: Successfully replaced static templates with conditional Jinja2 templates
- **Smart Filtering**: Implemented `filter_empty_sections()` function to remove empty data
- **Conditional Rendering**: All sections now only appear when they contain actual content
- **Clean LaTeX Output**: Fixed syntax errors and brace mismatches
- **Enhanced Data Structure**: Converted flat form data to structured JSON format
- **Comprehensive Testing**: Added `test_template.py` with realistic sample data

### ✅ Completed Features
- ✅ **Jinja2 LaTeX Template** (`templates/cv_template.tex`) with conditional blocks
- ✅ **Jinja2 HTML Template** (`templates/cv_template.html`) with conditional rendering
- ✅ **Smart Data Filtering** automatically removes empty sections
- ✅ **Enhanced JSON Storage** with complete metadata and structured format
- ✅ **Template Rendering Engine** supporting both LaTeX and HTML
- ✅ **Comprehensive Test Suite** with sample data and validation
- ✅ **Professional Output** with no empty bullet points or sections

### ✅ Benefits Achieved
- **Clean Professional Output**: No more empty sections or bullet points
- **Flexible Data Entry**: Users can fill as much or as little as desired
- **Better Maintainability**: Template logic is easier to understand and modify
- **Improved User Experience**: Only relevant information displayed
- **Robust Testing**: Automated validation ensures quality

### Original Problem Solved ✅
- ~~Empty optional fields still render as blank sections in both HTML and PDF~~
- ~~Creates unprofessional appearance with empty bullet points and sections~~
- ~~LaTeX templates are static and don't easily support conditional rendering~~

### Proposed Solutions

#### Solution 1: Template Engine Approach (Recommended)
Replace static templates with Jinja2 templating for both HTML and LaTeX generation.

#### Solution 2: Post-Processing Approach
Generate full templates then remove empty sections programmatically.

#### Solution 3: Multiple Template Variants
Create different template files for different field combinations (not scalable).

### Implementation Steps

#### 1.1 Install Template Engine
- **File**: `requirements.txt`
- **Add**: `Jinja2>=3.1.0`

#### 1.2 Create Jinja2 LaTeX Template
- **File**: `templates/cv_template.tex` (new file)
- **Action**: Convert current `1pg_CV.tex` to Jinja2 template with conditional blocks
- **Key Changes**:

```latex
% Personal Information (always shown)
\LARGE\textbf{ {{personal_info.full_name}} }\\
\vspace{10pt}
\Large {{personal_info.highest_education}}, {{personal_info.education[0].institute}} \\
\textbf{ {{personal_info.city}} } | \textbf{Phone} - {{personal_info.phone}} | \textbf{Email} - {{personal_info.email}}\\

% Education Table (always shown, but rows conditional)
\begin{tabularx}{\textwidth}{l@{\hspace{7mm}}l@{\hspace{7mm}}X@{\hspace{7mm}}l@{\hspace{5mm}}l}
\hline
\rule{0pt}{2.5ex}\textbf{Qualification} & \textbf{Stream} & \textbf{Institute} & \textbf{Year} & \textbf{CGPA/\%} \\[0.5ex]
\hline
{% for edu in education %}
{% if edu.qualification %}
\rule{0pt}{2.5ex}{{edu.qualification}} & {{edu.stream}} & {{edu.institute}} & {{edu.year}} & {{edu.cgpa}} \\
{% endif %}
{% endfor %}
\hline
\end{tabularx}

% Achievements Section (conditional)
{% set valid_achievements = achievements|selectattr('description')|list %}
{% if valid_achievements %}
\section*{{\large \textrm{\textbf{\color{myblue}SCHOLASTIC ACHIEVEMENTS\xfilll[0pt]{0.1pt}}}}}
\vspace{-3pt}
\begin{itemize}[label=\textcolor{myblue}{\textbullet},itemsep = -1.15 mm, leftmargin=6mm]
{% for ach in valid_achievements %}
\item {{ach.description}} \hfill {\em({{ach.year}})}
{% endfor %}
\end{itemize}
\vspace{-10pt}
{% endif %}

% Internships Section (conditional)
{% set valid_internships = internships|selectattr('company')|list %}
{% if valid_internships %}
\section*{\large \textrm{\textbf{\color{myblue}INTERNSHIPS\xfilll[0pt]{0.1pt}}}}
\vspace{-3pt}
{% for intern in valid_internships %}
\flushleft{\textbf{ {{intern.company}} } | {{intern.role}} \hfill \em({{intern.duration}})}\\
\vspace{-3pt}
\begin{itemize}[label=\textcolor{myblue}{\textbullet},itemsep = -1.15 mm, leftmargin=6mm]
{% for point in intern.points %}
{% if point %}
\item {{point}}
{% endif %}
{% endfor %}
\end{itemize}
{% if not loop.last %}\vspace{5pt}{% endif %}
{% endfor %}
\vspace{-10pt}
{% endif %}

% Projects Section (conditional)
{% set valid_projects = projects|selectattr('title')|list %}
{% if valid_projects %}
\section*{\large \textrm{\textbf{\color{myblue}KEY PROJECTS\xfilll[0pt]{0.1pt}}}}
\vspace{-3pt}
{% for proj in valid_projects %}
{\flushleft{\textbf{ {{proj.title}} } | {{proj.type}} \hfill \em({{proj.duration}})}\\
\vspace{-3pt}
\begin{itemize}[label=\textcolor{myblue}{\textbullet},itemsep = -1.15 mm, leftmargin=6mm]
{% for point in proj.points %}
{% if point %}
\item {{point}}
{% endif %}
{% endfor %}
\end{itemize}
{% if not loop.last %}\vspace{5pt}{% endif %}
{% endfor %}
\vspace{-10pt}
{% endif %}

% Positions of Responsibility (conditional)
{% set valid_positions = positions_of_responsibility|selectattr('club')|list %}
{% if valid_positions %}
\section*{\large \textrm{\textbf{\color{myblue}POSITIONS OF RESPONSIBILITY\xfilll[0pt]{0.5pt}}}}
\vspace{-3pt}
{% for pos in valid_positions %}
{\flushleft \bf \large {{pos.club}} | {{pos.role}} \hfill{{\em({{pos.duration}})}}\\
\vspace{-3pt}
\begin{itemize}[label=\textcolor{myblue}{\textbullet},itemsep = -1.15 mm, leftmargin=6mm]
{% for point in pos.points %}
{% if point %}
\item {{point}}
{% endif %}
{% endfor %}
\end{itemize}
{% if not loop.last %}\vspace{5pt}{% endif %}
{% endfor %}
\vspace{-10pt}
{% endif %}

% Extra Curricular Activities (conditional)
{% set valid_extracurricular = extracurricular|select|list %}
{% if valid_extracurricular %}
\section*{\large \textrm{\textbf{\color{myblue}EXTRA CURRICULAR ACTIVITIES\xfilll[0pt]{0.5pt}}}}
\vspace{-3pt}
\begin{itemize}[label=\textcolor{myblue}{\textbullet},itemsep = -1 mm, leftmargin=6mm]
{% for activity in valid_extracurricular %}
\item {{activity}}
{% endfor %}
\end{itemize}
\vspace{5pt}
{% endif %}

% Technical Skills (conditional)
{% set valid_skills = technical_skills|select|list %}
{% if valid_skills %}
\large \textrm{\textbf{\color{myblue}TECHNICAL SKILLS}} : {% for skill in valid_skills %}{{skill}}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}
```

#### 1.3 Create Jinja2 HTML Template
- **File**: `templates/cv_template.html` (new file)
- **Action**: Convert current `html_template.html` to use Jinja2 conditionals
- **Key Changes**:

```html
<!-- Education Table - only show rows with data -->
<table class="education-table">
    <thead>
        <tr>
            <th>Qualification</th>
            <th>Stream</th>
            <th>Institute</th>
            <th>Year</th>
            <th>CGPA/%</th>
        </tr>
    </thead>
    <tbody>
        {% for edu in education %}
        {% if edu.qualification %}
        <tr>
            <td>{{edu.qualification}}</td>
            <td>{{edu.stream}}</td>
            <td>{{edu.institute}}</td>
            <td>{{edu.year}}</td>
            <td>{{edu.cgpa}}</td>
        </tr>
        {% endif %}
        {% endfor %}
    </tbody>
</table>

<!-- Achievements Section - only show if there are achievements -->
{% set valid_achievements = achievements|selectattr('description')|list %}
{% if valid_achievements %}
<div class="section">
    <div class="section-title">Scholastic Achievements</div>
    <ul>
        {% for ach in valid_achievements %}
        <li>{{ach.description}} <span class="experience-duration">({{ach.year}})</span></li>
        {% endfor %}
    </ul>
</div>
{% endif %}

<!-- Internships Section - only show if there are internships -->
{% set valid_internships = internships|selectattr('company')|list %}
{% if valid_internships %}
<div class="section">
    <div class="section-title">Internships</div>
    {% for intern in valid_internships %}
    <div class="experience-item">
        <div class="experience-header">
            {{intern.company}} | {{intern.role}}
            <span class="experience-duration">({{intern.duration}})</span>
        </div>
        <div class="clear"></div>
        {% set valid_points = intern.points|select|list %}
        {% if valid_points %}
        <ul class="experience-points">
            {% for point in valid_points %}
            <li>{{point}}</li>
            {% endfor %}
        </ul>
        {% endif %}
    </div>
    {% endfor %}
</div>
{% endif %}

<!-- Similar conditional blocks for Projects, PORs, etc. -->
```

#### 1.4 Update Template Rendering Logic
- **File**: `main.py`
- **Action**: Replace string replacement with Jinja2 rendering
- **New imports**:
```python
from jinja2 import Environment, FileSystemLoader
```

- **New template rendering function**:
```python
def render_template(template_name: str, data: dict) -> str:
    """Render Jinja2 template with data"""
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template(template_name)
    return template.render(**data)

def filter_empty_sections(data: dict) -> dict:
    """Remove empty optional sections from data"""
    # Filter education entries
    data['education'] = [edu for edu in data['education'] if edu.get('qualification')]
    
    # Filter achievements
    data['achievements'] = [ach for ach in data['achievements'] if ach.get('description')]
    
    # Filter internships
    data['internships'] = [intern for intern in data['internships'] if intern.get('company')]
    
    # Filter projects
    data['projects'] = [proj for proj in data['projects'] if proj.get('title')]
    
    # Filter positions
    data['positions_of_responsibility'] = [pos for pos in data['positions_of_responsibility'] if pos.get('club')]
    
    # Filter extracurricular (remove empty strings)
    data['extracurricular'] = [activity for activity in data['extracurricular'] if activity and activity.strip()]
    
    # Filter technical skills (remove empty strings)
    data['technical_skills'] = [skill for skill in data['technical_skills'] if skill and skill.strip()]
    
    return data
```

#### 1.5 Update CV Generation Process
- **File**: `main.py` (in `generate_cv` function)
- **Replace current template filling with**:
```python
# Convert form data to structured format (from Task 1.1)
user_data = create_structured_data(form_variables)

# Filter out empty optional sections
filtered_data = filter_empty_sections(user_data)

# Render LaTeX template
filled_latex_template = render_template('cv_template.tex', filtered_data)

# Render HTML template
filled_html_template = render_template('cv_template.html', filtered_data)
```

#### 1.6 Handle Edge Cases
- **Completely empty sections**: Don't render the section at all
- **Partially filled sections**: Only show filled parts
- **Minimum content requirements**: Ensure at least one education entry is present
- **Section spacing**: Adjust spacing when sections are removed

#### 1.7 Alternative Implementation (If LaTeX Issues)
If Jinja2 with LaTeX proves problematic, implement a hybrid approach:

```python
def generate_latex_conditionally(data: dict) -> str:
    """Generate LaTeX by conditionally including sections"""
    template_parts = []
    
    # Always include header
    template_parts.append(render_header(data['personal_info']))
    
    # Always include education (but filter rows)
    template_parts.append(render_education_table(data['education']))
    
    # Conditionally include other sections
    if data.get('achievements'):
        template_parts.append(render_achievements_section(data['achievements']))
    
    if data.get('internships'):
        template_parts.append(render_internships_section(data['internships']))
    
    # ... continue for all sections
    
    return '\n\n'.join(template_parts)
```

### Testing Strategy

#### 1.8 Test Cases
1. **All fields filled**: Verify nothing changes from current behavior
2. **Some optional fields empty**: Verify those sections don't appear
3. **All optional fields empty**: Verify only required sections appear
4. **Mixed scenarios**: Some internships filled, some empty
5. **Edge cases**: Single character entries, special characters

#### 1.9 Validation Rules
- **Required sections**: Personal info, at least one education entry
- **Optional sections**: All others can be completely omitted
- **Graceful degradation**: If template rendering fails, fall back to static template

### Benefits

#### For Users
- **Professional appearance**: No empty sections or bullet points
- **Cleaner output**: Only relevant information displayed
- **Flexible**: Can fill as much or as little as desired

#### For System
- **Better templates**: More maintainable conditional logic
- **Reduced file sizes**: Smaller HTML/PDF when fewer sections used
- **Easier customization**: Template modifications easier with Jinja2

### Migration Strategy

#### Phase 1: Development
1. Create new Jinja2 templates alongside existing ones
2. Add feature flag to switch between old and new rendering
3. Test thoroughly with various data combinations

#### Phase 2: Testing
1. A/B test with subset of users
2. Compare output quality between old and new systems
3. Performance testing (Jinja2 vs string replacement)

#### Phase 3: Deployment
1. Switch default to new system
2. Keep old system as fallback for 1-2 releases
3. Remove old templates once confidence is high

---

## Task 2: Enhanced JSON Data Storage

### Description
Expand the current minimal JSON storage to include complete user form data for resume regeneration and editing.

### Current State
```python
user_data = {"full_name": full_name}
```

### Target State
Store all form fields in structured JSON format.

### Implementation Steps

#### 1.1 Create comprehensive data structure
- **File**: `main.py` (in `generate_cv` function)
- **Action**: Replace the current user_data creation with complete form data
- **Structure**:
```python
user_data = {
    "metadata": {
        "cv_id": cv_id,
        "created_at": datetime.utcnow().isoformat(),
        "last_modified": datetime.utcnow().isoformat(),
        "version": "1.0"
    },
    "personal_info": {
        "full_name": full_name,
        "highest_education": highest_education,
        "city": city,
        "phone": phone,
        "email": email
    },
    "education": [
        {
            "qualification": edu_1_qual,
            "stream": edu_1_stream,
            "institute": edu_1_institute,
            "year": edu_1_year,
            "cgpa": edu_1_cgpa
        },
        {
            "qualification": edu_2_qual,
            "stream": edu_2_stream,
            "institute": edu_2_institute,
            "year": edu_2_year,
            "cgpa": edu_2_cgpa
        },
        {
            "qualification": edu_3_qual,
            "stream": edu_3_stream,
            "institute": edu_3_institute,
            "year": edu_3_year,
            "cgpa": edu_3_cgpa
        }
    ],
    "achievements": [
        {"description": ach_1_desc, "year": ach_1_year},
        {"description": ach_2_desc, "year": ach_2_year}
    ],
    "internships": [
        {
            "company": intern_1_company,
            "role": intern_1_role,
            "duration": intern_1_duration,
            "points": [intern_1_point_1, intern_1_point_2]
        },
        {
            "company": intern_2_company,
            "role": intern_2_role,
            "duration": intern_2_duration,
            "points": [intern_2_point_1, intern_2_point_2]
        }
    ],
    "projects": [
        {
            "title": proj_1_title,
            "type": proj_1_type,
            "duration": proj_1_duration,
            "points": [proj_1_point_1, proj_1_point_2]
        },
        {
            "title": proj_2_title,
            "type": proj_2_type,
            "duration": proj_2_duration,
            "points": [proj_2_point_1, proj_2_point_2]
        }
    ],
    "positions_of_responsibility": [
        {
            "club": por_1_club,
            "role": por_1_role,
            "duration": por_1_duration,
            "points": [por_1_point_1, por_1_point_2]
        },
        {
            "club": por_2_club,
            "role": por_2_role,
            "duration": por_2_duration,
            "points": [por_2_point_1, por_2_point_2]
        }
    ],
    "extracurricular": [
        extracur_1_desc,
        extracur_2_desc,
        extracur_3_desc,
        extracur_4_desc,
        extracur_5_desc
    ],
    "technical_skills": [
        techskill_1,
        techskill_2,
        techskill_3,
        techskill_4,
        techskill_5
    ]
}
```

#### 1.2 Add data transformation helpers
- **File**: `main.py`
- **Action**: Create utility functions to convert between form data and template variables
- **Functions needed**:
  - `json_to_template_vars(user_data)` - Convert JSON back to template variable format
  - `validate_user_data(user_data)` - Ensure data integrity
  - `sanitize_user_data(user_data)` - Clean user input for security

---

## Task 2: AWS S3 Integration Setup

### Description
Set up AWS S3 bucket and implement basic upload/download functionality.

### Prerequisites
- AWS account with S3 access
- AWS credentials configured (IAM user with S3 permissions)

### Implementation Steps

#### 2.1 Install AWS SDK
- **Action**: Add boto3 to requirements
- **File**: `requirements.txt`
- **Add**: `boto3>=1.26.0`

#### 2.2 Configure S3 settings
- **File**: `main.py` (add at top)
- **Code**:
```python
import boto3
from botocore.exceptions import ClientError
import os
from datetime import datetime

# S3 Configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "cv-generator-storage")
S3_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

s3_client = boto3.client(
    's3',
    region_name=S3_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)
```

#### 2.3 Create S3 utility functions
- **File**: `s3_utils.py` (new file)
- **Functions to implement**:
```python
def upload_json_to_s3(cv_id: str, user_data: dict) -> bool:
    """Upload user data JSON to S3"""
    pass

def download_json_from_s3(cv_id: str) -> dict:
    """Download user data JSON from S3"""
    pass

def upload_file_to_s3(local_path: str, s3_key: str) -> bool:
    """Upload any file to S3"""
    pass

def check_cv_exists(cv_id: str) -> bool:
    """Check if CV exists in S3"""
    pass

def list_cvs_by_prefix(prefix: str = "") -> list:
    """List CVs matching a prefix (for search)"""
    pass
```

#### 2.4 S3 bucket structure design
```
cv-generator-bucket/
├── metadata/
│   ├── {cv_id}.json          # User form data
│   └── search-index.json     # Search index (optional)
├── generated/
│   ├── html/
│   │   └── {cv_id}.html     # Generated HTML files
│   ├── pdf/
│   │   └── {cv_id}.pdf      # Generated PDF files
│   └── latex/
│       └── {cv_id}.tex      # LaTeX source files
└── templates/
    ├── latex/
    │   └── 1pg_CV.tex       # LaTeX template
    └── html/
        └── template.html     # HTML template
```

---

## Task 3: S3 Upload Integration

### Description
Modify the CV generation process to upload all files to S3 instead of local storage.

### Implementation Steps

#### 3.1 Update generate_cv endpoint
- **File**: `main.py`
- **Action**: Replace local file operations with S3 uploads
- **Changes needed**:
  1. Upload JSON data to `metadata/{cv_id}.json`
  2. Upload LaTeX file to `generated/latex/{cv_id}.tex`
  3. Upload HTML file to `generated/html/{cv_id}.html`
  4. Upload display HTML to `generated/html/{cv_id}_display.html`

#### 3.2 Modify file serving endpoints
- **Endpoints to update**:
  - `GET /cv/{cv_id}` - Download HTML from S3
  - `GET /cv/{cv_id}/html` - Download raw HTML from S3
  - `GET /cv/{cv_id}/pdf` - Generate PDF and upload to S3, then serve

#### 3.3 Add error handling
- **Handle S3 upload failures**
- **Implement retry logic for transient failures**
- **Graceful degradation to local storage if S3 unavailable**

---

## Task 4: Search Functionality

### Description
Implement search capabilities to find CVs by various criteria stored in S3.

### Implementation Steps

#### 4.1 Create search endpoint
- **File**: `main.py`
- **Endpoint**: `GET /search`
- **Parameters**: 
  - `name` (optional) - Search by name
  - `email` (optional) - Search by email
  - `company` (optional) - Search by company name
  - `skill` (optional) - Search by technical skill
  - `limit` (optional, default=20) - Limit results

#### 4.2 Implement search logic
- **Method 1: Prefix-based search**
  - Use S3 object prefixes for basic organization
  - Suitable for name-based searches
- **Method 2: Metadata-based search**
  - Use S3 object metadata tags
  - Better for complex queries
- **Method 3: Index-based search**
  - Maintain a search index file in S3
  - Most flexible but requires index maintenance

#### 4.3 Search response format
```python
{
    "results": [
        {
            "cv_id": "uuid",
            "name": "John Doe",
            "email": "john@example.com",
            "created_at": "2024-01-01T00:00:00Z",
            "preview_url": "/cv/{cv_id}",
            "edit_url": "/edit/{cv_id}"
        }
    ],
    "total": 150,
    "page": 1,
    "limit": 20
}
```

---

## Task 5: Resume Editing Functionality

### Description
Allow users to load existing CVs for editing and regeneration.

### Implementation Steps

#### 5.1 Create edit endpoint
- **File**: `main.py`
- **Endpoint**: `GET /edit/{cv_id}`
- **Action**: Load CV data from S3 and pre-populate the form

#### 5.2 Pre-populate form template
- **File**: `templates/form.html` (assumed to exist)
- **Action**: Modify form to accept URL parameters or POST data for pre-population
- **JavaScript needed**: Auto-fill form fields from JSON data

#### 5.3 Create form pre-population endpoint
- **Endpoint**: `GET /api/cv/{cv_id}/data`
- **Response**: JSON data for form population
- **Security**: Consider access controls

#### 5.4 Update form submission
- **Handle both new CV creation and existing CV updates**
- **Preserve CV ID for updates**
- **Update metadata timestamps**

---

## Task 6: Enhanced Search Interface

### Description
Create a user-friendly search interface for finding and managing CVs.

### Implementation Steps

#### 6.1 Create search page
- **File**: `templates/search.html` (new file)
- **Features**:
  - Search form with multiple criteria
  - Results display with pagination
  - Links to view/edit/download each CV

#### 6.2 Add search endpoint to main page
- **File**: `templates/form.html`
- **Add**: Link to search page in navigation

#### 6.3 Implement advanced search features
- **Date range filtering**
- **Sorting options** (name, date created, etc.)
- **Bulk operations** (delete multiple CVs)

---

## Task 7: Environment Configuration

### Description
Set up proper environment configuration for different deployment scenarios.

### Implementation Steps

#### 7.1 Create environment configuration
- **File**: `.env.example`
- **Contents**:
```
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
S3_BUCKET_NAME=cv-generator-storage

# Application Configuration
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Optional: Enable local fallback
ENABLE_LOCAL_FALLBACK=true
LOCAL_STORAGE_PATH=./generated
```

#### 7.2 Update main.py for environment loading
- **Add**: `python-dotenv` to requirements.txt
- **Add**: Environment loading at app startup

#### 7.3 Create deployment configurations
- **File**: `docker-compose.yml` (if using Docker)
- **File**: `Dockerfile` (if using Docker)
- **File**: `deploy.yml` (if using GitHub Actions or similar)

---

## Task 8: Error Handling and Logging

### Description
Implement comprehensive error handling and logging for production readiness.

### Implementation Steps

#### 8.1 Add structured logging
- **Install**: `structlog` or use Python's `logging`
- **Log levels**: DEBUG, INFO, WARNING, ERROR
- **Log S3 operations, user actions, errors**

#### 8.2 Implement error boundaries
- **Handle S3 connection failures**
- **Handle malformed JSON data**
- **Handle missing CV IDs**
- **Provide user-friendly error messages**

#### 8.3 Add health check endpoints
- **Endpoint**: `GET /health`
- **Check**: S3 connectivity, disk space, etc.

---

## Task 9: Security Enhancements

### Description
Implement security best practices for production deployment.

### Implementation Steps

#### 9.1 Input validation
- **Validate all form inputs**
- **Sanitize user data before storage**
- **Prevent XSS and injection attacks**

#### 9.2 Access controls
- **Rate limiting for API endpoints**
- **Optional: User authentication for edit functionality**
- **S3 bucket policies and CORS configuration**

#### 9.3 Data privacy
- **Optional: Data encryption at rest**
- **Data retention policies**
- **GDPR compliance considerations**

---

## Implementation Priority

### Phase 1 (Core Functionality)
1. Task 1: Enhanced JSON Data Storage
2. Task 2: AWS S3 Integration Setup
3. Task 3: S3 Upload Integration

### Phase 2 (Search & Edit)
4. Task 4: Search Functionality
5. Task 5: Resume Editing Functionality

### Phase 3 (Polish & Production)
6. Task 6: Enhanced Search Interface
7. Task 7: Environment Configuration
8. Task 8: Error Handling and Logging
9. Task 9: Security Enhancements

---

## Testing Strategy

### Unit Tests
- Test S3 upload/download functions
- Test data transformation functions
- Test search logic

### Integration Tests
- Test full CV generation workflow with S3
- Test edit and regeneration workflow
- Test search functionality

### Manual Testing
- End-to-end user workflows
- Error scenarios (S3 down, invalid data, etc.)
- Performance testing with multiple CVs

---

## Deployment Considerations

### AWS Setup
1. Create S3 bucket with appropriate permissions
2. Set up IAM user with minimal required permissions
3. Configure CORS for bucket if serving files directly
4. Consider using CloudFront for better performance

### Application Deployment
1. Set environment variables
2. Ensure AWS credentials are properly configured
3. Test S3 connectivity before going live
4. Monitor S3 usage and costs

### Backup Strategy
1. S3 provides durability, but consider cross-region replication
2. Regular exports of critical data
3. Version control for templates

---

## Expected Benefits

### For Users
- **Persistent CVs**: Never lose your CV data
- **Easy editing**: Modify existing CVs without starting over
- **Search capability**: Find old CVs quickly
- **Shareable links**: Send CV links that always work

### For System
- **Scalability**: Handle unlimited CVs
- **Reliability**: 99.999999999% durability
- **Global access**: Fast access from anywhere
- **Cost-effective**: Pay only for what you use

### For Development
- **Stateless application**: Easier deployment and scaling
- **Data portability**: Easy to migrate or backup
- **API-first**: Easy to add mobile apps or other interfaces