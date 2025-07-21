"""
CV Data Models using Pydantic for validation and serialization
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


class PersonalInfo(BaseModel):
    """Personal information section of CV"""
    full_name: str = Field(..., min_length=1, max_length=100)
    highest_education: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=1, max_length=20)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class EducationEntry(BaseModel):
    """Single education entry"""
    qualification: str = Field(..., min_length=1, max_length=100)
    stream: str = Field(..., min_length=1, max_length=100)
    institute: str = Field(..., min_length=1, max_length=200)
    year: str = Field(..., min_length=1, max_length=10)
    cgpa: str = Field(..., min_length=1, max_length=10)

    @validator('qualification', 'stream', 'institute', 'year', 'cgpa')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()


class AchievementEntry(BaseModel):
    """Single achievement entry"""
    description: str = Field(..., min_length=1, max_length=500)
    year: str = Field(..., min_length=1, max_length=10)

    @validator('description', 'year')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()


class InternshipEntry(BaseModel):
    """Single internship entry"""
    company: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., min_length=1, max_length=100)
    duration: str = Field(..., min_length=1, max_length=50)
    points: List[str] = Field(..., min_items=1, max_items=5)

    @validator('company', 'role', 'duration')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

    @validator('points')
    def validate_points(cls, v):
        if not v:
            raise ValueError('At least one point is required')
        # Filter out empty points and validate remaining
        non_empty_points = [point.strip() for point in v if point and point.strip()]
        if not non_empty_points:
            raise ValueError('At least one non-empty point is required')
        return non_empty_points


class ProjectEntry(BaseModel):
    """Single project entry"""
    title: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., min_length=1, max_length=50)
    duration: str = Field(..., min_length=1, max_length=50)
    repo_link: Optional[str] = Field(None, max_length=200)
    points: List[str] = Field(..., min_items=1, max_items=5)

    @validator('title', 'type', 'duration')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

    @validator('points')
    def validate_points(cls, v):
        if not v:
            raise ValueError('At least one point is required')
        # Filter out empty points and validate remaining
        non_empty_points = [point.strip() for point in v if point and point.strip()]
        if not non_empty_points:
            raise ValueError('At least one non-empty point is required')
        return non_empty_points


class PositionEntry(BaseModel):
    """Single position of responsibility entry"""
    club: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., min_length=1, max_length=100)
    duration: str = Field(..., min_length=1, max_length=50)
    points: List[str] = Field(..., min_items=1, max_items=5)

    @validator('club', 'role', 'duration')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

    @validator('points')
    def validate_points(cls, v):
        if not v:
            raise ValueError('At least one point is required')
        # Filter out empty points and validate remaining
        non_empty_points = [point.strip() for point in v if point and point.strip()]
        if not non_empty_points:
            raise ValueError('At least one non-empty point is required')
        return non_empty_points


class CVData(BaseModel):
    """Complete CV data structure"""
    personal_info: PersonalInfo
    education: List[EducationEntry] = Field(..., min_items=1, max_items=5)
    achievements: List[AchievementEntry] = Field(default_factory=list, max_items=5)
    internships: List[InternshipEntry] = Field(..., min_items=1, max_items=3)
    projects: List[ProjectEntry] = Field(..., min_items=1, max_items=3)
    positions_of_responsibility: List[PositionEntry] = Field(..., min_items=1, max_items=3)
    extracurricular: List[str] = Field(default_factory=list, max_items=5)
    technical_skills: List[str] = Field(..., min_items=1, max_items=10)

    @validator('extracurricular')
    def validate_extracurricular(cls, v):
        # Filter out empty activities
        return [activity.strip() for activity in v if activity and activity.strip()]

    @validator('technical_skills')
    def validate_technical_skills(cls, v):
        if not v:
            raise ValueError('At least one technical skill is required')
        # Filter out empty skills and validate remaining
        non_empty_skills = [skill.strip() for skill in v if skill and skill.strip()]
        if not non_empty_skills:
            raise ValueError('At least one non-empty technical skill is required')
        return non_empty_skills


class CVMetadata(BaseModel):
    """CV metadata for storage and tracking"""
    cv_id: str
    created_at: datetime
    last_modified: datetime
    version: str = "2.0"


class CVDocument(BaseModel):
    """Complete CV document with metadata"""
    metadata: CVMetadata
    data: CVData

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CVGenerateRequest(BaseModel):
    """Request model for CV generation from form data"""
    # Personal Information
    full_name: str = Field(..., min_length=1, max_length=100)
    highest_education: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=1, max_length=20)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    # Education (support up to 5 entries)
    education_entries: List[EducationEntry] = Field(..., min_items=1, max_items=5)
    
    # Achievements (optional, up to 5 entries)
    achievements: List[AchievementEntry] = Field(default_factory=list, max_items=5)
    
    # Internships (at least 1, up to 3)
    internships: List[InternshipEntry] = Field(..., min_items=1, max_items=3)
    
    # Projects (at least 1, up to 3)
    projects: List[ProjectEntry] = Field(..., min_items=1, max_items=3)
    
    # Positions of Responsibility (at least 1, up to 3)
    positions_of_responsibility: List[PositionEntry] = Field(..., min_items=1, max_items=3)
    
    # Extracurricular Activities (optional, up to 5)
    extracurricular: List[str] = Field(default_factory=list, max_items=5)
    
    # Technical Skills (at least 1, up to 10)
    technical_skills: List[str] = Field(..., min_items=1, max_items=10)

    def to_cv_data(self) -> CVData:
        """Convert form request to structured CV data"""
        return CVData(
            personal_info=PersonalInfo(
                full_name=self.full_name,
                highest_education=self.highest_education,
                city=self.city,
                phone=self.phone,
                email=self.email
            ),
            education=self.education_entries,
            achievements=self.achievements,
            internships=self.internships,
            projects=self.projects,
            positions_of_responsibility=self.positions_of_responsibility,
            extracurricular=self.extracurricular,
            technical_skills=self.technical_skills
        )


class CVGenerateResponse(BaseModel):
    """Response model for CV generation"""
    cv_id: str
    redirect_url: str
    message: str = "CV generated successfully"