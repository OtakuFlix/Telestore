# ==================== database/models.py ====================
from datetime import datetime
from typing import Optional

class Folder:
    """Folder model"""
    def __init__(
        self,
        folder_id: str,
        name: str,
        created_by: int,
        created_at: datetime = None,
        updated_at: datetime = None,
        parent_folder_id: Optional[str] = None,
        file_count: int = 0
    ):
        self.folderId = folder_id
        self.name = name
        self.createdBy = created_by
        self.createdAt = created_at or datetime.utcnow()
        self.updatedAt = updated_at or datetime.utcnow()
        self.parentFolderId = parent_folder_id
        self.fileCount = file_count
    
    def to_dict(self):
        return {
            'folderId': self.folderId,
            'name': self.name,
            'createdBy': self.createdBy,
            'createdAt': self.createdAt,
            'updatedAt': self.updatedAt,
            'parentFolderId': self.parentFolderId,
            'fileCount': self.fileCount
        }

class File:
    """File model"""
    def __init__(
        self,
        file_id: str,
        telegram_file_id: str,
        telegram_file_unique_id: str,
        folder_id: str,
        file_name: str,
        mime_type: str,
        size: int,
        uploaded_by: int,
        uploaded_at: datetime = None,
        caption: Optional[str] = None,
        quality: Optional[str] = None,
        language: Optional[str] = None,
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumbnail: Optional[str] = None,
        views: int = 0,
        downloads: int = 0
    ):
        self.fileId = file_id
        self.telegramFileId = telegram_file_id
        self.telegramFileUniqueId = telegram_file_unique_id
        self.folderId = folder_id
        self.fileName = file_name
        self.mimeType = mime_type
        self.size = size
        self.uploadedBy = uploaded_by
        self.uploadedAt = uploaded_at or datetime.utcnow()
        self.caption = caption
        self.quality = quality
        self.language = language
        self.duration = duration
        self.width = width
        self.height = height
        self.thumbnail = thumbnail
        self.views = views
        self.downloads = downloads
    
    def to_dict(self):
        return {
            'fileId': self.fileId,
            'telegramFileId': self.telegramFileId,
            'telegramFileUniqueId': self.telegramFileUniqueId,
            'folderId': self.folderId,
            'fileName': self.fileName,
            'mimeType': self.mimeType,
            'size': self.size,
            'uploadedBy': self.uploadedBy,
            'uploadedAt': self.uploadedAt,
            'caption': self.caption,
            'quality': self.quality,
            'language': self.language,
            'duration': self.duration,
            'width': self.width,
            'height': self.height,
            'thumbnail': self.thumbnail,
            'views': self.views,
            'downloads': self.downloads
        }