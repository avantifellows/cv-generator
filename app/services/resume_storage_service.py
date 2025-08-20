"""
Resume Storage Service for managing UUID-based resume persistence
Supports both local storage and future S3 integration
"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from app.core.logging import get_logger

logger = get_logger(__name__)


class ResumeStorageService:
    """Service for managing resume data storage with UUID-based persistence"""
    
    def __init__(self, base_path: Path, storage_type: str = "local"):
        self.base_path = base_path
        self.storage_type = storage_type
        self.storage_dir = base_path / "resume_data"
        self.metadata_file = self.storage_dir / "resume_metadata.json"
        
        # Ensure storage directory exists
        self.storage_dir.mkdir(exist_ok=True)
        
        # Initialize metadata file if it doesn't exist
        if not self.metadata_file.exists():
            self._initialize_metadata()
    
    def _initialize_metadata(self):
        """Initialize the metadata file with empty structure"""
        initial_metadata = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "resumes": {}
        }
        self._save_metadata(initial_metadata)
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from file"""
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Error loading metadata: {e}, initializing new metadata")
            self._initialize_metadata()
            return self._load_metadata()
    
    def _save_metadata(self, metadata: Dict[str, Any]):
        """Save metadata to file"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
            raise
    
    def _get_resume_file_path(self, resume_id: str) -> Path:
        """Get the file path for a specific resume"""
        return self.storage_dir / f"{resume_id}.json"
    
    def create_new_resume(self, initial_data: Optional[Dict[str, Any]] = None, resume_id: Optional[str] = None) -> str:
        """Create a new resume with a unique UUID or a provided one"""
        if not resume_id:
            resume_id = str(uuid.uuid4())
        
        # Create resume data structure
        resume_data = {
            "resume_id": resume_id,
            "created_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "data": initial_data or {},
            "is_completed": False
        }
        
        # Save resume data
        self._save_resume_data(resume_id, resume_data)
        
        # Update metadata
        metadata = self._load_metadata()
        metadata["resumes"][resume_id] = {
            "created_at": resume_data["created_at"],
            "last_modified": resume_data["last_modified"],
            "is_completed": resume_data["is_completed"]
        }
        self._save_metadata(metadata)
        
        logger.info(f"Created new resume with ID: {resume_id}")
        return resume_id
    
    def get_resume_data(self, resume_id: str) -> Optional[Dict[str, Any]]:
        """Get resume data by UUID"""
        try:
            resume_file = self._get_resume_file_path(resume_id)
            if not resume_file.exists():
                logger.warning(f"Resume file not found for ID: {resume_id}")
                return None
            
            with open(resume_file, 'r', encoding='utf-8') as f:
                resume_data = json.load(f)
            
            logger.info(f"Retrieved resume data for ID: {resume_id}")
            return resume_data
            
        except Exception as e:
            logger.error(f"Error retrieving resume data for ID {resume_id}: {e}")
            return None
    
    def update_resume_data(self, resume_id: str, data: Dict[str, Any], is_completed: bool = False) -> bool:
        """Update existing resume data"""
        try:
            # Load existing data
            existing_data = self.get_resume_data(resume_id)
            if not existing_data:
                logger.warning(f"Cannot update non-existent resume: {resume_id}")
                return False
            
            # Update resume data
            resume_data = {
                "resume_id": resume_id,
                "created_at": existing_data["created_at"],
                "last_modified": datetime.now().isoformat(),
                "data": data,
                "is_completed": is_completed
            }
            
            # Save updated data
            self._save_resume_data(resume_id, resume_data)
            
            # Update metadata
            metadata = self._load_metadata()
            if resume_id in metadata["resumes"]:
                metadata["resumes"][resume_id]["last_modified"] = resume_data["last_modified"]
                metadata["resumes"][resume_id]["is_completed"] = is_completed
                self._save_metadata(metadata)
            
            logger.info(f"Updated resume data for ID: {resume_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating resume data for ID {resume_id}: {e}")
            return False
    
    def _save_resume_data(self, resume_id: str, resume_data: Dict[str, Any]):
        """Save resume data to file"""
        try:
            resume_file = self._get_resume_file_path(resume_id)
            with open(resume_file, 'w', encoding='utf-8') as f:
                json.dump(resume_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving resume data for ID {resume_id}: {e}")
            raise
    
    def resume_exists(self, resume_id: str) -> bool:
        """Check if a resume exists"""
        resume_file = self._get_resume_file_path(resume_id)
        return resume_file.exists()
    
    def delete_resume(self, resume_id: str) -> bool:
        """Delete a resume and its data"""
        try:
            # Remove resume file
            resume_file = self._get_resume_file_path(resume_id)
            if resume_file.exists():
                resume_file.unlink()
            
            # Update metadata
            metadata = self._load_metadata()
            if resume_id in metadata["resumes"]:
                del metadata["resumes"][resume_id]
                self._save_metadata(metadata)
            
            logger.info(f"Deleted resume with ID: {resume_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting resume with ID {resume_id}: {e}")
            return False
    
    def list_resumes(self) -> Dict[str, Any]:
        """List all resumes with metadata"""
        try:
            metadata = self._load_metadata()
            return metadata
        except Exception as e:
            logger.error(f"Error listing resumes: {e}")
            return {"resumes": {}, "version": "1.0"}
    
    def cleanup_old_resumes(self, days_old: int = 30) -> int:
        """Clean up old incomplete resumes"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cleaned_count = 0
            
            metadata = self._load_metadata()
            resumes_to_remove = []
            
            for resume_id, resume_info in metadata["resumes"].items():
                if not resume_info.get("is_completed", False):
                    created_at = datetime.fromisoformat(resume_info["created_at"])
                    if created_at < cutoff_date:
                        resumes_to_remove.append(resume_id)
            
            for resume_id in resumes_to_remove:
                if self.delete_resume(resume_id):
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} old resumes")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old resumes: {e}")
            return 0


# Factory function for creating storage service
def create_resume_storage_service(base_path: Path, storage_type: str = "local") -> ResumeStorageService:
    """Create a resume storage service instance"""
    if storage_type == "local":
        return ResumeStorageService(base_path, "local")
    elif storage_type == "s3":
        # Future S3 implementation
        raise NotImplementedError("S3 storage not yet implemented")
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")


