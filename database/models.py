from datetime import datetime
from typing import Optional, List
from enum import Enum

class Quality(str, Enum):
    Q_4K = "4K"
    Q_1080P = "1080p"
    Q_720P = "720p"
    Q_480P = "480p"
    Q_360P = "360p"
    UNKNOWN = "Unknown"

class Folder:
    def __init__(
        self,
        folder_id: str,
        name: str,
        created_by: int,
        created_at: datetime = None,
        updated_at: datetime = None,
        parent_folder_id: Optional[str] = None,
        file_count: int = 0,
        subfolder_count: int = 0,
        is_quality_folder: bool = False,
        quality: Optional[str] = None
    ):
        self.folderId = folder_id
        self.name = name
        self.createdBy = created_by
        self.createdAt = created_at or datetime.utcnow()
        self.updatedAt = updated_at or datetime.utcnow()
        self.parentFolderId = parent_folder_id
        self.fileCount = file_count
        self.subfolderCount = subfolder_count
        self.isQualityFolder = is_quality_folder
        self.quality = quality
    
    def to_dict(self):
        return {
            'folderId': self.folderId,
            'name': self.name,
            'createdBy': self.createdBy,
            'createdAt': self.createdAt,
            'updatedAt': self.updatedAt,
            'parentFolderId': self.parentFolderId,
            'fileCount': self.fileCount,
            'subfolderCount': self.subfolderCount,
            'isQualityFolder': self.isQualityFolder,
            'quality': self.quality
        }

class File:
    def __init__(
        self,
        file_id: str,
        telegram_file_id: str,
        telegram_file_unique_id: str,
        folder_id: str,
        file_name: str,
        base_name: str,
        mime_type: str,
        size: int,
        uploaded_by: int,
        uploaded_at: datetime = None,
        caption: Optional[str] = None,
        quality: str = "Unknown",
        language: Optional[str] = None,
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumbnail: Optional[str] = None,
        views: int = 0,
        downloads: int = 0,
        quality_group_id: Optional[str] = None,
        parsed_from_caption: bool = False
    ):
        self.fileId = file_id
        self.telegramFileId = telegram_file_id
        self.telegramFileUniqueId = telegram_file_unique_id
        self.folderId = folder_id
        self.fileName = file_name
        self.baseName = base_name
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
        self.qualityGroupId = quality_group_id
        self.parsedFromCaption = parsed_from_caption
    
    def to_dict(self):
        return {
            'fileId': self.fileId,
            'telegramFileId': self.telegramFileId,
            'telegramFileUniqueId': self.telegramFileUniqueId,
            'folderId': self.folderId,
            'fileName': self.fileName,
            'baseName': self.baseName,
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
            'downloads': self.downloads,
            'qualityGroupId': self.qualityGroupId,
            'parsedFromCaption': self.parsedFromCaption
        }