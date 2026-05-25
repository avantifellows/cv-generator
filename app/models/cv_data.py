"""
CV Data Models using Pydantic for validation and serialization
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


class PersonalInfo(BaseModel):
    """Personal information section of CV"""
    full_name: str = Field(default="", max_length=100)
    highest_education: str = Field(default="", max_length=100)  
    city: str = Field(default="", max_length=100)
    phone: str = Field(default="", max_length=20)
    email: str = Field(default="")
    github: Optional[str] = Field(None, max_length=100)
    linkedin: Optional[str] = Field(None, max_length=100)


class EducationEntry(BaseModel):
    """Single education entry"""
    qualification: str = Field(default="", max_length=100)
    stream: str = Field(default="", max_length=100)
    institute: str = Field(default="", max_length=200)
    year: str = Field(default="", max_length=10)
    cgpa: str = Field(default="", max_length=10)

    @validator('qualification', 'stream', 'institute', 'year', 'cgpa')
    def validate_not_empty(cls, v):
        if not v:
            return ""
        return v.strip()


class AchievementEntry(BaseModel):
    """Single achievement entry"""
    description: str = Field(default="", max_length=500)
    year: str = Field(default="", max_length=10)

    @validator('description', 'year')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            return ""
        return v.strip()


class CertificationEntry(BaseModel):
    """Single certification entry"""
    description: str = Field(default="", max_length=500)
    year: str = Field(default="", max_length=10)

    @validator('description', 'year')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            return ""
        return v.strip()


class PublicationEntry(BaseModel):
    """Single publication entry"""
    description: str = Field(default="", max_length=500)
    year: str = Field(default="", max_length=10)

    @validator('description', 'year')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            return ""
        return v.strip()


class InternshipEntry(BaseModel):
    """Single internship entry"""
    company: str = Field(default="", max_length=100)
    role: str = Field(default="", max_length=100)
    duration: str = Field(default="", max_length=50)
    points: List[str] = Field(default_factory=list, max_items=5)

    @validator('company', 'role', 'duration')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            return ""
        return v.strip()

    @validator('points')
    def validate_points(cls, v):
        # Filter out empty points
        non_empty_points = [point.strip() for point in v if point and point.strip()]
        return non_empty_points


class WorkExperienceEntry(BaseModel):
    """Single work experience entry"""
    company: str = Field(default="", max_length=100)
    position: str = Field(default="", max_length=100)
    duration: str = Field(default="", max_length=50)
    points: List[str] = Field(default_factory=list, max_items=5)

    @validator('company', 'position', 'duration')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            return ""
        return v.strip()

    @validator('points')
    def validate_points(cls, v):
        # Filter out empty points
        non_empty_points = [point.strip() for point in v if point and point.strip()]
        return non_empty_points


class ProjectEntry(BaseModel):
    """Single project entry"""
    title: str = Field(default="", max_length=100)
    type: str = Field(default="", max_length=50)
    duration: str = Field(default="", max_length=50)
    repo_link: Optional[str] = Field(None, max_length=200)
    points: List[str] = Field(default_factory=list, max_items=5)

    @validator('title', 'type', 'duration')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            return ""
        return v.strip()

    @validator('points')
    def validate_points(cls, v):
        # Filter out empty points
        non_empty_points = [point.strip() for point in v if point and point.strip()]
        return non_empty_points


class PositionEntry(BaseModel):
    """Single position of responsibility entry"""
    club: str = Field(default="", max_length=100)
    role: str = Field(default="", max_length=100)
    duration: str = Field(default="", max_length=50)
    points: List[str] = Field(default_factory=list, max_items=5)

    @validator('club', 'role', 'duration')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            return ""
        return v.strip()

    @validator('points')
    def validate_points(cls, v):
        # Filter out empty points
        non_empty_points = [point.strip() for point in v if point and point.strip()]
        return non_empty_points


class TechnicalSkillsCategory(BaseModel):
    """Technical skills organized by category"""
    programming_languages: List[str] = Field(default_factory=list, max_items=20)
    web_technologies: List[str] = Field(default_factory=list, max_items=20)
    database_management: List[str] = Field(default_factory=list, max_items=20)
    tools_and_technologies: List[str] = Field(default_factory=list, max_items=20)

    @validator('programming_languages', 'web_technologies', 'database_management', 'tools_and_technologies')
    def validate_skills(cls, v):
        # Filter out empty skills
        non_empty_skills = [skill.strip() for skill in v if skill and skill.strip()]
        return non_empty_skills


class FontSettings(BaseModel):
    """Font customization settings"""
    title_font_size: str = Field(default="14px")
    title_font_color: str = Field(default="#4C5196")
    body_font_size: str = Field(default="14px")
    body_font_color: str = Field(default="#000000")
    line_height: str = Field(default="1.5")
    # Multiplier applied to default section spacing in templates (web/pdf have different bases)
    section_spacing_multiplier: str = Field(default="2.0")


class CustomSectionDefaultEntry(BaseModel):
    """Single entry in a default-type custom section"""
    title: str = Field(default="", max_length=200)
    subtitle: str = Field(default="", max_length=200)
    duration: str = Field(default="", max_length=100)
    points: List[str] = Field(default_factory=list, max_items=10)

    @validator('title', 'subtitle', 'duration')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            return ""
        return v.strip()

    @validator('points')
    def validate_points(cls, v):
        return [point.strip() for point in v if point and point.strip()]


class CustomSection(BaseModel):
    """Custom section that can be either default or tabular type"""
    id: str = Field(default="")
    name: str = Field(default="", max_length=100)
    type: str = Field(default="default")  # "default" or "tabular"
    # For default type
    entries: List[CustomSectionDefaultEntry] = Field(default_factory=list)
    # For tabular type
    columns: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)


class CVData(BaseModel):
    """Complete CV data structure"""
    personal_info: PersonalInfo
    summary: Optional[str] = Field(default="", max_length=1000)
    education: List[EducationEntry] = Field(default_factory=list, max_items=5)
    work_experience: List[WorkExperienceEntry] = Field(default_factory=list, max_items=5)
    achievements: List[AchievementEntry] = Field(default_factory=list, max_items=5)
    certifications: List[CertificationEntry] = Field(default_factory=list, max_items=5)
    publications: List[PublicationEntry] = Field(default_factory=list, max_items=5)
    internships: List[InternshipEntry] = Field(default_factory=list, max_items=5)
    projects: List[ProjectEntry] = Field(default_factory=list, max_items=5)
    positions_of_responsibility: List[PositionEntry] = Field(default_factory=list, max_items=5)
    extracurricular: List[str] = Field(default_factory=list, max_items=5)
    languages: List[str] = Field(default_factory=list, max_items=10)
    technical_skills: TechnicalSkillsCategory = Field(default_factory=TechnicalSkillsCategory)
    font_settings: FontSettings = Field(default_factory=FontSettings)
    section_order: List[str] = Field(default_factory=list)
    custom_sections: List[CustomSection] = Field(default_factory=list)

    @validator('extracurricular')
    def validate_extracurricular(cls, v):
        # Filter out empty activities
        return [activity.strip() for activity in v if activity and activity.strip()]
    
    @validator('languages')
    def validate_languages(cls, v):
        # Filter out empty languages
        return [lang.strip() for lang in v if lang and lang.strip()]

    # Legacy support for backward compatibility
    @classmethod
    def from_legacy_skills(cls, **data):
        """Create CVData from legacy format with simple technical_skills list"""
        if 'technical_skills' in data and isinstance(data['technical_skills'], list):
            # Convert legacy skills list to categorized format
            legacy_skills = data['technical_skills']
            categorized_skills = TechnicalSkillsCategory()
            
            # Simple categorization logic - can be improved
            for skill in legacy_skills:
                skill_lower = skill.lower()
                if any(lang in skill_lower for lang in ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'go', 'rust', 'swift', 'kotlin']):
                    categorized_skills.programming_languages.append(skill)
                elif any(tech in skill_lower for tech in ['html', 'css', 'react', 'angular', 'vue', 'node', 'express', 'django', 'flask', 'spring', 'bootstrap', 'jquery']):
                    categorized_skills.web_technologies.append(skill)
                elif any(db in skill_lower for db in ['mysql', 'postgresql', 'mongodb', 'sqlite', 'oracle', 'sql server', 'redis', 'elasticsearch']):
                    categorized_skills.database_management.append(skill)
                else:
                    categorized_skills.tools_and_technologies.append(skill)
            
            data['technical_skills'] = categorized_skills
        
        return cls(**data)


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
    full_name: str = Field(default="", max_length=100)
    highest_education: str = Field(default="", max_length=100)
    city: str = Field(default="", max_length=100)
    phone: str = Field(default="", max_length=20)
    email: str = Field(default="")
    github: Optional[str] = Field(None, max_length=100)
    linkedin: Optional[str] = Field(None, max_length=100)
    
    # Education (support up to 5 entries)
    education_entries: List[EducationEntry] = Field(default_factory=list, max_items=5)
    
    # Work Experience (optional, up to 5)
    work_experience: List[WorkExperienceEntry] = Field(default_factory=list, max_items=5)
    
    # Achievements (optional, up to 5 entries)
    achievements: List[AchievementEntry] = Field(default_factory=list, max_items=5)
    
    # Certifications (optional, up to 5 entries)
    certifications: List[CertificationEntry] = Field(default_factory=list, max_items=5)
    
    # Publications (optional, up to 5 entries)
    publications: List[PublicationEntry] = Field(default_factory=list, max_items=5)
    
    # Internships (optional, up to 5)
    internships: List[InternshipEntry] = Field(default_factory=list, max_items=5)
    
    # Projects (optional, up to 5)
    projects: List[ProjectEntry] = Field(default_factory=list, max_items=5)
    
    # Positions of Responsibility (optional, up to 5)
    positions_of_responsibility: List[PositionEntry] = Field(default_factory=list, max_items=5)
    
    # Extracurricular Activities (optional, up to 5)
    extracurricular: List[str] = Field(default_factory=list, max_items=5)
    
    # Languages (optional, up to 10)
    languages: List[str] = Field(default_factory=list, max_items=10)
    
    # Technical Skills (categorized)
    technical_skills: TechnicalSkillsCategory = Field(default_factory=TechnicalSkillsCategory)

    def to_cv_data(self) -> CVData:
        """Convert form request to structured CV data"""
        return CVData(
            personal_info=PersonalInfo(
                full_name=self.full_name,
                highest_education=self.highest_education,
                city=self.city,
                phone=self.phone,
                email=self.email,
                github=self.github,
                linkedin=self.linkedin
            ),
            education=self.education_entries,
            work_experience=self.work_experience,
            achievements=self.achievements,
            internships=self.internships,
            projects=self.projects,
            positions_of_responsibility=self.positions_of_responsibility,
            extracurricular=self.extracurricular,
            languages=self.languages,
            technical_skills=self.technical_skills
        )


class CVGenerateResponse(BaseModel):
    """Response model for CV generation"""
    cv_id: str
    redirect_url: str
    message: str = "CV generated successfully"