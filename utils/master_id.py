import hashlib
import re

def generate_master_group_id(folder_id: str, name: str) -> str:
    """
    Generate master group ID from folder ID and file name.
    This function normalizes the name by removing extension and quality tags.
    
    Args:
        folder_id: The folder ID
        name: Either baseName (already cleaned) or fileName (with extension)
    
    Returns:
        A 24-character hex hash as master group ID
    """
    # Remove extension if present
    clean_name = name
    if '.' in name:
        parts = name.rsplit('.', 1)
        if len(parts) == 2 and parts[1].lower() in ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mp3', 'm4v']:
            clean_name = parts[0]
    
    # Remove quality tags (1080p, 720p, etc.) and extra spaces for consistency
    clean_name = re.sub(
        r'\b(4320p|2160p|1440p|1080p|720p|480p|360p|240p|4K|2K|HD|FHD|UHD|8K)\b',
        '',
        clean_name,
        flags=re.IGNORECASE
    )
    clean_name = re.sub(r'\s+', ' ', clean_name).strip()
    
    # Generate hash
    combined = f"{folder_id}:{clean_name}"
    return hashlib.md5(combined.encode()).hexdigest()[:24]

def get_base_name_from_filename(filename: str) -> str:
    """
    Extract base name from filename by removing extension and quality tags.
    
    Args:
        filename: Full filename like "Movie.1080p.mp4"
    
    Returns:
        Clean base name like "Movie"
    """
    # Remove extension
    name = filename
    if '.' in filename:
        parts = filename.rsplit('.', 1)
        if len(parts) == 2 and parts[1].lower() in ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mp3', 'm4v']:
            name = parts[0]
    
    # Remove quality tags
    name = re.sub(
        r'\b(4320p|2160p|1440p|1080p|720p|480p|360p|240p|4K|2K|HD|FHD|UHD|8K)\b',
        '',
        name,
        flags=re.IGNORECASE
    )
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name