# CV Generator v2.0 - Clean Architecture

## Overview

This is the refactored version of the CV Generator with clean architecture, Pydantic models, and proper service layer separation. It is a FastAPI application ready for deployment.

## Architecture

### Project Structure
```
cv-generator/
├── app/
│   ├── models/
│   │   └── cv_data.py          # Pydantic models for data validation
│   ├── services/
│   │   └── cv_service.py       # Business logic layer
│   ├── core/
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── logging.py          # Logging configuration
│   └── utils/
├── templates/                   # Jinja2 templates
├── static/                      # Static assets
├── generated/                   # Generated CV files
├── main.py                      # FastAPI application
└── requirements.txt
```

### Key Improvements

#### 1. **Pydantic Models** 🔥
- **Before**: Manual field validation with 50+ individual parameters
- **After**: Structured data models with automatic validation

```python
class CVData(BaseModel):
    personal_info: PersonalInfo
    education: List[EducationEntry]
    internships: List[InternshipEntry]
    # ... etc
```

#### 2. **Service Layer** 🔥
- **Before**: Business logic mixed with API endpoints
- **After**: Clean separation with dedicated service classes

```python
class CVService:
    def generate_cv(self, cv_data: CVData) -> str:
        # Clean business logic
    
    def get_cv_data(self, cv_id: str) -> CVDocument:
        # Data retrieval logic
```

#### 3. **Proper Error Handling** 🔥
- **Before**: Generic HTTP exceptions
- **After**: Custom exceptions with proper logging

```python
@app.exception_handler(CVNotFoundError)
async def cv_not_found_handler(request: Request, exc: CVNotFoundError):
    logger.warning(f"CV not found: {str(exc)}")
    return HTTPException(status_code=404, detail=str(exc))
```

#### 4. **Structured Logging** 🔥
- **Before**: Print statements
- **After**: Proper structured logging with levels

```python
logger.info(f"CV generated successfully: {cv_id}")
logger.error(f"Error generating PDF: {str(e)}")
```

#### 5. **API Versioning** 🔥
- **Before**: No API structure
- **After**: Versioned API endpoints

```python
@app.get("/api/v1/cvs")
@app.get("/api/v1/cv/{cv_id}")
@app.delete("/api/v1/cv/{cv_id}")
```

## Usage

### Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### API Endpoints

#### Web Interface
- `GET /` - CV form
- `GET /test` - Pre-filled test form
- `POST /generate` - Generate CV from form data
- `GET /cv/{cv_id}` - View CV with download button
- `GET /cv/{cv_id}/pdf` - Download PDF

#### API Endpoints
- `GET /api/v1/cvs` - List all CVs
- `GET /api/v1/cv/{cv_id}` - Get CV data
- `DELETE /api/v1/cv/{cv_id}` - Delete CV
- `GET /health` - Health check

### Testing

```bash
# Test the models and services
python -c "
from app.models.cv_data import CVData
from app.services.cv_service import CVService
import json

# Load test data
with open('test_data_structured.json', 'r') as f:
    data = json.load(f)

# Validate data
cv_data = CVData(**data)
print(f'✓ Validation passed: {cv_data.personal_info.full_name}')

# Test service
service = CVService()
cv_id = service.generate_cv(cv_data)
print(f'✓ CV generated: {cv_id}')
"
```

## Data Structure

The new version uses proper data structures instead of flat field names:

```json
{
  "personal_info": {
    "full_name": "Jane Smith",
    "email": "jane@example.com"
  },
  "education": [
    {
      "qualification": "M.Tech",
      "institute": "Stanford University",
      "year": "2023"
    }
  ],
  "internships": [
    {
      "company": "Google",
      "role": "Software Engineer",
      "points": ["Achievement 1", "Achievement 2"]
    }
  ]
}
```

The system still supports a legacy flat format for backward compatibility during form submission.

## Features

### Data Validation
- **Email validation** with regex patterns
- **Required field validation** with meaningful error messages
- **Data type validation** (strings, lists, etc.)
- **Length constraints** (min/max characters)
- **Array size limits** (max entries per section)

### Error Handling
- **Custom exceptions** for different error types
- **Structured logging** with different levels
- **Graceful error recovery** with fallback options
- **Detailed error messages** for debugging

### Performance
- **Efficient data processing** with Pydantic models
- **Proper file handling** with context managers
- **Memory-efficient** PDF generation
- **Caching-ready** template rendering

### Security
- **Input validation** prevents injection attacks
- **Proper error messages** don't expose internals
- **File path validation** prevents directory traversal
- **Content-type validation** for uploads

## Development

### Adding New Fields

1. **Update the models** in `app/models/cv_data.py`:
   ```python
   class PersonalInfo(BaseModel):
       full_name: str
       new_field: str = Field(..., min_length=1)
   ```

2. **Update the service** in `app/services/cv_service.py`:
   ```python
   def convert_legacy_data(self, legacy_data: dict) -> CVData:
       # Add conversion logic for new field
   ```

3. **Update templates** to display the new field

### Adding New Endpoints

1. **Add to main.py**:
   ```python
   @app.get("/api/v1/new-endpoint")
   async def new_endpoint():
       return {"message": "New endpoint"}
   ```

2. **Add proper error handling**:
   ```python
   try:
       result = service.new_operation()
       return result
   except CustomException as e:
       logger.error(f"Error in new endpoint: {str(e)}")
       raise HTTPException(status_code=500, detail=str(e))
   ```

## Testing

### Unit Tests
```bash
# Test models
python -m pytest tests/test_models.py

# Test services
python -m pytest tests/test_services.py

# Test API endpoints
python -m pytest tests/test_api.py
```

### Integration Tests
```bash
# Test full workflow
python -m pytest tests/test_integration.py
```

## Deployment

For detailed deployment instructions, please see `DEPLOYMENT_GUIDE.md`.

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Logs
```bash
# View logs
tail -f app.log

# Filter by level
grep "ERROR" app.log
```

## Contributing

1. **Follow the new architecture** patterns
2. **Add proper validation** for new fields
3. **Include error handling** for new endpoints
4. **Add logging** for debugging
5. **Update tests** for new functionality
6. **Update documentation** for API changes

## Changelog

### v2.0.0
- ✅ Pydantic models for data validation
- ✅ Service layer architecture
- ✅ Proper error handling and logging
- ✅ API versioning
- ✅ Structured test data
- ✅ Health check endpoint
- ✅ Backward compatibility with legacy format

### v1.0.0
- ✅ Basic CV generation
- ✅ HTML and PDF output
- ✅ Form-based interface
- ✅ Template rendering