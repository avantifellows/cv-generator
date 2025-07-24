"""
CV Service - Business logic for CV generation and management
"""
import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from app.models.cv_data import CVData, CVDocument, CVMetadata
from app.core.exceptions import CVGenerationError, CVNotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)


class CVService:
    """Service for CV generation and management"""
    
    def __init__(self, base_path: Optional[Path] = None, generated_dir: str = "generated"):
        if base_path:
            self.generated_dir = base_path / generated_dir
        else:
            self.generated_dir = Path(generated_dir)
        self.generated_dir.mkdir(exist_ok=True)
        
    def generate_cv(self, cv_data: CVData) -> str:
        """
        Generate a new CV and return the CV ID
        
        Args:
            cv_data: Validated CV data
            
        Returns:
            str: Generated CV ID
            
        Raises:
            CVGenerationError: If CV generation fails
        """
        try:
            # Generate unique CV ID
            cv_id = str(uuid.uuid4())
            
            # Create metadata
            metadata = CVMetadata(
                cv_id=cv_id,
                created_at=datetime.utcnow(),
                last_modified=datetime.utcnow(),
                version="2.0"
            )
            
            # Create complete CV document
            cv_document = CVDocument(metadata=metadata, data=cv_data)
            
            # Save CV data to file
            self._save_cv_data(cv_document)
            
            logger.info(f"CV generated successfully with ID: {cv_id}")
            return cv_id
            
        except Exception as e:
            logger.error(f"Error generating CV: {str(e)}")
            raise CVGenerationError(f"Failed to generate CV: {str(e)}")
    
    def get_cv_data(self, cv_id: str) -> CVDocument:
        """
        Retrieve CV data by ID
        
        Args:
            cv_id: CV identifier
            
        Returns:
            CVDocument: Complete CV document
            
        Raises:
            CVNotFoundError: If CV not found
        """
        try:
            data_file = self.generated_dir / f"{cv_id}_data.json"
            
            if not data_file.exists():
                raise CVNotFoundError(f"CV with ID {cv_id} not found")
            
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            return CVDocument(**data)
            
        except CVNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving CV data for ID {cv_id}: {str(e)}")
            raise CVGenerationError(f"Failed to retrieve CV data: {str(e)}")
    
    def update_cv_data(self, cv_id: str, cv_data: CVData) -> None:
        """
        Update existing CV data
        
        Args:
            cv_id: CV identifier
            cv_data: Updated CV data
            
        Raises:
            CVNotFoundError: If CV not found
            CVGenerationError: If update fails
        """
        try:
            # Get existing document
            existing_doc = self.get_cv_data(cv_id)
            
            # Update metadata
            existing_doc.metadata.last_modified = datetime.utcnow()
            existing_doc.data = cv_data
            
            # Save updated document
            self._save_cv_data(existing_doc)
            
            logger.info(f"CV updated successfully with ID: {cv_id}")
            
        except CVNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating CV data for ID {cv_id}: {str(e)}")
            raise CVGenerationError(f"Failed to update CV data: {str(e)}")
    
    def delete_cv(self, cv_id: str) -> None:
        """
        Delete CV and all associated files
        
        Args:
            cv_id: CV identifier
            
        Raises:
            CVNotFoundError: If CV not found
        """
        try:
            # Check if CV exists
            if not self.cv_exists(cv_id):
                raise CVNotFoundError(f"CV with ID {cv_id} not found")
            
            # Delete all associated files
            for file_pattern in [f"{cv_id}_data.json", f"{cv_id}.html", f"{cv_id}_display.html"]:
                file_path = self.generated_dir / file_pattern
                if file_path.exists():
                    file_path.unlink()
            
            logger.info(f"CV deleted successfully with ID: {cv_id}")
            
        except CVNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting CV with ID {cv_id}: {str(e)}")
            raise CVGenerationError(f"Failed to delete CV: {str(e)}")
    
    def cv_exists(self, cv_id: str) -> bool:
        """
        Check if CV exists
        
        Args:
            cv_id: CV identifier
            
        Returns:
            bool: True if CV exists
        """
        data_file = self.generated_dir / f"{cv_id}_data.json"
        return data_file.exists()
    
    def list_cvs(self) -> List[Dict[str, Any]]:
        """
        List all CVs with basic metadata
        
        Returns:
            list: List of CV metadata dictionaries
        """
        cvs = []
        
        try:
            for data_file in self.generated_dir.glob("*_data.json"):
                try:
                    with open(data_file, 'r') as f:
                        data = json.load(f)
                    
                    cv_info = {
                        "cv_id": data["metadata"]["cv_id"],
                        "name": data["data"]["personal_info"]["full_name"],
                        "created_at": data["metadata"]["created_at"],
                        "last_modified": data["metadata"]["last_modified"],
                        "version": data["metadata"]["version"]
                    }
                    cvs.append(cv_info)
                    
                except Exception as e:
                    logger.warning(f"Error reading CV data file {data_file}: {str(e)}")
                    continue
            
            # Sort by creation date (newest first)
            cvs.sort(key=lambda x: x["created_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing CVs: {str(e)}")
        
        return cvs
    
    def _save_cv_data(self, cv_document: CVDocument) -> None:
        """
        Save CV document to file
        
        Args:
            cv_document: Complete CV document to save
        """
        data_file = self.generated_dir / f"{cv_document.metadata.cv_id}_data.json"
        
        with open(data_file, 'w') as f:
            json.dump(cv_document.dict(), f, indent=2, default=str)
    
    def convert_legacy_data(self, legacy_data: Dict[str, Any]) -> CVData:
        """
        Convert legacy flat form data to new structured format
        
        Args:
            legacy_data: Legacy form data dictionary
            
        Returns:
            CVData: Structured CV data
        """
        try:
            # Extract personal info
            personal_info = {
                "full_name": legacy_data.get("full_name", ""),
                "highest_education": legacy_data.get("highest_education", ""),
                "city": legacy_data.get("city", ""),
                "phone": legacy_data.get("phone", ""),
                "email": legacy_data.get("email", "")
            }
            
            # Extract education entries
            education = []
            for i in range(1, 6):  # Support up to 5 education entries
                qual = legacy_data.get(f"edu_{i}_qual", "")
                if qual and qual.strip():
                    education.append({
                        "qualification": qual,
                        "stream": legacy_data.get(f"edu_{i}_stream", ""),
                        "institute": legacy_data.get(f"edu_{i}_institute", ""),
                        "year": legacy_data.get(f"edu_{i}_year", ""),
                        "cgpa": legacy_data.get(f"edu_{i}_cgpa", "")
                    })
            
            # Extract achievements
            achievements = []
            for i in range(1, 6):  # Support up to 5 achievements
                desc = legacy_data.get(f"ach_{i}_desc", "")
                if desc and desc.strip():
                    achievements.append({
                        "description": desc,
                        "year": legacy_data.get(f"ach_{i}_year", "")
                    })
            
            # Extract internships
            internships = []
            for i in range(1, 4):  # Support up to 3 internships
                company = legacy_data.get(f"intern_{i}_company", "")
                if company and company.strip():
                    points = []
                    for j in range(1, 6):  # Support up to 5 points per internship
                        point = legacy_data.get(f"intern_{i}_point_{j}", "")
                        if point and point.strip():
                            points.append(point)
                    
                    if points:  # Only add if there are points
                        internships.append({
                            "company": company,
                            "role": legacy_data.get(f"intern_{i}_role", ""),
                            "duration": legacy_data.get(f"intern_{i}_duration", ""),
                            "points": points
                        })
            
            # Extract projects
            projects = []
            for i in range(1, 4):  # Support up to 3 projects
                title = legacy_data.get(f"proj_{i}_title", "")
                if title and title.strip():
                    points = []
                    for j in range(1, 6):  # Support up to 5 points per project
                        point = legacy_data.get(f"proj_{i}_point_{j}", "")
                        if point and point.strip():
                            points.append(point)
                    
                    if points:  # Only add if there are points
                        projects.append({
                            "title": title,
                            "type": legacy_data.get(f"proj_{i}_type", ""),
                            "duration": legacy_data.get(f"proj_{i}_duration", ""),
                            "points": points
                        })
            
            # Extract positions of responsibility
            positions = []
            for i in range(1, 4):  # Support up to 3 positions
                club = legacy_data.get(f"por_{i}_club", "")
                if club and club.strip():
                    points = []
                    for j in range(1, 6):  # Support up to 5 points per position
                        point = legacy_data.get(f"por_{i}_point_{j}", "")
                        if point and point.strip():
                            points.append(point)
                    
                    if points:  # Only add if there are points
                        positions.append({
                            "club": club,
                            "role": legacy_data.get(f"por_{i}_role", ""),
                            "duration": legacy_data.get(f"por_{i}_duration", ""),
                            "points": points
                        })
            
            # Extract extracurricular activities
            extracurricular = []
            for i in range(1, 6):  # Support up to 5 activities
                activity = legacy_data.get(f"extracur_{i}_desc", "")
                if activity and activity.strip():
                    extracurricular.append(activity)
            
            # Extract technical skills
            technical_skills = []
            for i in range(1, 11):  # Support up to 10 skills
                skill = legacy_data.get(f"techskill_{i}", "")
                if skill and skill.strip():
                    technical_skills.append(skill)
            
            # Create structured CV data
            cv_data_dict = {
                "personal_info": personal_info,
                "education": education,
                "achievements": achievements,
                "internships": internships,
                "projects": projects,
                "positions_of_responsibility": positions,
                "extracurricular": extracurricular,
                "technical_skills": technical_skills
            }
            
            return CVData(**cv_data_dict)
            
        except Exception as e:
            logger.error(f"Error converting legacy data: {str(e)}")
            raise CVGenerationError(f"Failed to convert legacy data: {str(e)}")