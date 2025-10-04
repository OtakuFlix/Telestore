# ==================== database/operations.py ====================
from database.connection import get_database
from datetime import datetime
from typing import List, Optional
from pymongo.errors import DuplicateKeyError

# ==================== FOLDER OPERATIONS ====================

async def create_folder(folder_id: str, name: str, created_by: int, parent_folder_id: Optional[str] = None):
    """Create a new folder"""
    db = get_database()
    folder = {
        'folderId': folder_id,
        'name': name,
        'createdBy': created_by,
        'createdAt': datetime.utcnow(),
        'updatedAt': datetime.utcnow(),
        'parentFolderId': parent_folder_id,
        'fileCount': 0
    }
    result = await db.folders.insert_one(folder)
    return result.inserted_id is not None

async def get_folder_by_id(folder_id: str):
    """Get folder by ID"""
    db = get_database()
    return await db.folders.find_one({'folderId': folder_id})

async def get_user_folders(user_id: int, page: int = 1, page_size: int = 10, parent_id: Optional[str] = None):
    """Get user's folders with pagination"""
    db = get_database()
    skip = (page - 1) * page_size
    
    query = {'createdBy': user_id}
    if parent_id:
        query['parentFolderId'] = parent_id
    else:
        query['parentFolderId'] = None
    
    cursor = db.folders.find(query).sort('createdAt', -1).skip(skip).limit(page_size)
    folders = await cursor.to_list(length=page_size)
    
    # Add file count to each folder
    for folder in folders:
        folder['fileCount'] = await count_folder_files(folder['folderId'])
    
    return folders

async def count_user_folders(user_id: int, parent_id: Optional[str] = None):
    """Count user's folders"""
    db = get_database()
    query = {'createdBy': user_id}
    if parent_id:
        query['parentFolderId'] = parent_id
    else:
        query['parentFolderId'] = None
    return await db.folders.count_documents(query)

async def update_folder(folder_id: str, update_data: dict):
    """Update folder"""
    db = get_database()
    update_data['updatedAt'] = datetime.utcnow()
    result = await db.folders.update_one(
        {'folderId': folder_id},
        {'$set': update_data}
    )
    return result.modified_count > 0

async def delete_folder(folder_id: str, user_id: int):
    """Delete folder and all its files"""
    db = get_database()
    
    # Check ownership
    folder = await db.folders.find_one({'folderId': folder_id, 'createdBy': user_id})
    if not folder:
        return False
    
    # Delete all files in folder
    await db.files.delete_many({'folderId': folder_id})
    
    # Delete folder
    result = await db.folders.delete_one({'folderId': folder_id})
    return result.deleted_count > 0

# ==================== FILE OPERATIONS ====================

async def add_file_to_folder(file_data: dict, uploaded_by: int):
    """Add file to folder"""
    db = get_database()
    
    file_data['uploadedBy'] = uploaded_by
    file_data['uploadedAt'] = datetime.utcnow()
    file_data['views'] = 0
    file_data['downloads'] = 0
    
    # Allow same Telegram file in different folders but prevent duplicates within the same folder
    existing = await db.files.find_one({
        '$or': [
            {
                'telegramFileId': file_data['telegramFileId'],
                'folderId': file_data['folderId']
            },
            {
                'telegramFileUniqueId': file_data.get('telegramFileUniqueId'),
                'folderId': file_data['folderId']
            }
        ]
    })
    if existing:
        return False
    
    try:
        result = await db.files.insert_one(file_data)
    except DuplicateKeyError:
        return False
    
    # Increment folder file count
    if result.inserted_id:
        await db.folders.update_one(
            {'folderId': file_data['folderId']},
            {'$inc': {'fileCount': 1}}
        )
    
    return result.inserted_id is not None

async def get_file_by_id(file_id: str):
    """Get file by ID"""
    db = get_database()
    return await db.files.find_one({'fileId': file_id})

async def get_folder_files(folder_id: str, page: int = 1, page_size: int = 10):
    """Get files in folder with pagination"""
    db = get_database()
    skip = (page - 1) * page_size
    
    cursor = db.files.find({'folderId': folder_id}).sort('uploadedAt', -1).skip(skip).limit(page_size)
    return await cursor.to_list(length=page_size)

async def count_folder_files(folder_id: str):
    """Count files in folder"""
    db = get_database()
    return await db.files.count_documents({'folderId': folder_id})

async def update_file(file_id: str, update_data: dict):
    """Update file"""
    db = get_database()
    result = await db.files.update_one(
        {'fileId': file_id},
        {'$set': update_data}
    )
    return result.modified_count > 0

async def delete_file(file_id: str):
    """Delete file"""
    db = get_database()
    
    # Get file to get folder ID
    file = await db.files.find_one({'fileId': file_id})
    if not file:
        return False
    
    # Delete file
    result = await db.files.delete_one({'fileId': file_id})
    
    # Decrement folder file count
    if result.deleted_count > 0:
        await db.folders.update_one(
            {'folderId': file['folderId']},
            {'$inc': {'fileCount': -1}}
        )
    
    return result.deleted_count > 0

async def increment_views(file_id: str):
    """Increment file view count"""
    db = get_database()
    await db.files.update_one(
        {'fileId': file_id},
        {'$inc': {'views': 1}}
    )

async def increment_downloads(file_id: str):
    """Increment file download count"""
    db = get_database()
    await db.files.update_one(
        {'fileId': file_id},
        {'$inc': {'downloads': 1}}
    )

# ==================== USER OPERATIONS ====================

async def get_all_users() -> List[int]:
    """Get all unique user IDs from the database"""
    db = get_database()
    
    # Get unique user IDs from folders
    folder_users = await db.folders.distinct('createdBy')
    
    # Get unique user IDs from files
    file_users = await db.files.distinct('uploadedBy')
    
    # Combine and deduplicate user IDs
    all_users = list(set(folder_users + file_users))
    return all_users

# ==================== STATISTICS ====================

async def get_stats(user_id: int):
    """Get user statistics"""
    db = get_database()
    
    # Count folders
    folder_count = await db.folders.count_documents({'createdBy': user_id})
    
    # Count files and get total size
    pipeline = [
        {
            '$lookup': {
                'from': 'folders',
                'localField': 'folderId',
                'foreignField': 'folderId',
                'as': 'folder'
            }
        },
        {
            '$match': {
                'folder.createdBy': user_id
            }
        },
        {
            '$group': {
                '_id': None,
                'totalFiles': {'$sum': 1},
                'totalSize': {'$sum': '$size'},
                'totalViews': {'$sum': '$views'},
                'totalDownloads': {'$sum': '$downloads'}
            }
        }
    ]
    
    result = await db.files.aggregate(pipeline).to_list(1)
    
    if result:
        stats = result[0]
        return {
            'folders': folder_count,
            'files': stats.get('totalFiles', 0),
            'total_size_mb': stats.get('totalSize', 0) / (1024 * 1024),
            'views': stats.get('totalViews', 0),
            'downloads': stats.get('totalDownloads', 0)
        }
    
    return {
        'folders': folder_count,
        'files': 0,
        'total_size_mb': 0.0,
        'views': 0,
        'downloads': 0
    }