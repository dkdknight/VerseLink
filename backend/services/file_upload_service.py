import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import aiofiles
from fastapi import UploadFile, HTTPException
from pathlib import Path
from PIL import Image
import mimetypes

from models.tournament import Attachment, AttachmentType
from database import get_database

class FileUploadService:
    """Service for handling file uploads for match attachments"""
    
    def __init__(self):
        self.db = get_database()
        self.upload_dir = Path("/app/uploads")
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_image_types = {
            "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"
        }
        self.allowed_video_types = {
            "video/mp4", "video/webm", "video/avi", "video/mov", "video/mkv"
        }
        self.allowed_other_types = {
            "text/plain", "application/json", "text/csv"
        }
        
        # Create upload directory if it doesn't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.upload_dir / "screenshots").mkdir(exist_ok=True)
        (self.upload_dir / "videos").mkdir(exist_ok=True)
        (self.upload_dir / "logs").mkdir(exist_ok=True)
        (self.upload_dir / "other").mkdir(exist_ok=True)
    
    def _get_attachment_type(self, mime_type: str) -> AttachmentType:
        """Determine attachment type from MIME type"""
        if mime_type in self.allowed_image_types:
            return AttachmentType.SCREENSHOT
        elif mime_type in self.allowed_video_types:
            return AttachmentType.VIDEO
        elif mime_type in self.allowed_other_types:
            return AttachmentType.LOG
        else:
            return AttachmentType.OTHER
    
    def _get_upload_subdirectory(self, attachment_type: AttachmentType) -> str:
        """Get subdirectory for attachment type"""
        if attachment_type == AttachmentType.SCREENSHOT:
            return "screenshots"
        elif attachment_type == AttachmentType.VIDEO:
            return "videos"
        elif attachment_type == AttachmentType.LOG:
            return "logs"
        else:
            return "other"
    
    def _is_allowed_type(self, mime_type: str) -> bool:
        """Check if file type is allowed"""
        return mime_type in (
            self.allowed_image_types | 
            self.allowed_video_types | 
            self.allowed_other_types
        )
    
    async def validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """Validate uploaded file"""
        # Check file size
        file_size = 0
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File size ({file_size} bytes) exceeds maximum allowed size ({self.max_file_size} bytes)"
            )
        
        # Determine MIME type
        mime_type = file.content_type
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(file.filename)
            mime_type = mime_type or "application/octet-stream"
        
        # Check if file type is allowed
        if not self._is_allowed_type(mime_type):
            raise HTTPException(
                status_code=415,
                detail=f"File type {mime_type} is not allowed"
            )
        
        return {
            "filename": file.filename,
            "mime_type": mime_type,
            "file_size": file_size,
            "attachment_type": self._get_attachment_type(mime_type)
        }
    
    async def save_file(self, match_id: str, user_id: str, file: UploadFile, description: Optional[str] = None) -> Attachment:
        """Save uploaded file and create attachment record"""
        # Validate file
        file_info = await self.validate_file(file)
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Determine subdirectory
        subdirectory = self._get_upload_subdirectory(file_info["attachment_type"])
        file_path = self.upload_dir / subdirectory / unique_filename
        
        # Save file to disk
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                while content := await file.read(8192):  # Read 8KB chunks
                    await f.write(content)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )
        
        # Create attachment record
        attachment = Attachment(
            match_id=match_id,
            user_id=user_id,
            filename=file.filename,
            file_path=str(file_path),
            file_size=file_info["file_size"],
            mime_type=file_info["mime_type"],
            attachment_type=file_info["attachment_type"],
            description=description
        )
        
        # Save to database
        await self.db.attachments.insert_one(attachment.dict())
        
        return attachment
    
    async def get_match_attachments(self, match_id: str) -> List[Attachment]:
        """Get all attachments for a match"""
        attachments = []
        async for attachment_doc in self.db.attachments.find({"match_id": match_id}).sort("uploaded_at", -1):
            attachments.append(Attachment(**attachment_doc))
        
        return attachments
    
    async def delete_attachment(self, attachment_id: str, user_id: str) -> bool:
        """Delete attachment (owner only)"""
        attachment_doc = await self.db.attachments.find_one({"id": attachment_id})
        if not attachment_doc:
            raise HTTPException(status_code=404, detail="Attachment not found")
        
        attachment = Attachment(**attachment_doc)
        
        # Check if user is owner
        if attachment.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this attachment")
        
        # Delete file from disk
        try:
            file_path = Path(attachment.file_path)
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Warning: Failed to delete file {attachment.file_path}: {e}")
        
        # Delete from database
        result = await self.db.attachments.delete_one({"id": attachment_id})
        return result.deleted_count > 0
    
    def get_file_url(self, attachment: Attachment) -> str:
        """Get download URL for attachment"""
        return f"/api/v1/attachments/{attachment.id}/download"
    
    async def get_attachment_for_download(self, attachment_id: str) -> Optional[Attachment]:
        """Get attachment for download"""
        attachment_doc = await self.db.attachments.find_one({"id": attachment_id})
        return Attachment(**attachment_doc) if attachment_doc else None
    
    async def optimize_image(self, file_path: Path, max_width: int = 1920, max_height: int = 1080, quality: int = 85) -> bool:
        """Optimize uploaded image (reduce size/quality if needed)"""
        try:
            if not file_path.exists():
                return False
            
            # Check if it's an image
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type or not mime_type.startswith('image/'):
                return False
            
            # Open and optimize image
            with Image.open(file_path) as img:
                # Convert RGBA to RGB if saving as JPEG
                if img.mode == 'RGBA' and file_path.suffix.lower() in ['.jpg', '.jpeg']:
                    img = img.convert('RGB')
                
                # Resize if too large
                if img.width > max_width or img.height > max_height:
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Save optimized version
                img.save(file_path, optimize=True, quality=quality)
            
            return True
            
        except Exception as e:
            print(f"Failed to optimize image {file_path}: {e}")
            return False