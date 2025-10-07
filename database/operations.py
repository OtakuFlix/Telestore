from database.connection import get_database
from datetime import datetime
from typing import List, Optional, Dict
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId
from bson.errors import InvalidId
import secrets
import string
import re

def generate_folder_id(length=12):
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))

def parse_caption_format(caption: str) -> Dict:
    pattern = r'<([^>]+)><([^>]+)><([^>]+)><([^>]+)>'
    match = re.match(pattern, caption)
    if match:
        return {
            'folder_name': match.group(1).strip(),
            'file_name': match.group(2).strip(),
            'quality': match.group(3).strip(),
            'size': match.group(4).strip(),
            'parsed': True
        }
    return {'parsed': False}

async def create_folder(folder_id: str, name: str, created_by: int, parent_folder_id: Optional[str] = None, is_quality_folder: bool = False, quality: Optional[str] = None):
    db = get_database()
    folder = {
        'folderId': folder_id,
        'name': name,
        'createdBy': created_by,
        'createdAt': datetime.utcnow(),
        'updatedAt': datetime.utcnow(),
        'parentFolderId': parent_folder_id,
        'fileCount': 0,
        'subfolderCount': 0,
        'isQualityFolder': is_quality_folder,
        'quality': quality
    }
    result = await db.folders.insert_one(folder)
    
    if parent_folder_id and result.inserted_id:
        await db.folders.update_one(
            {'folderId': parent_folder_id},
            {'$inc': {'subfolderCount': 1}}
        )
    
    return result.inserted_id is not None

async def get_folder_by_id(folder_id: str):
    db = get_database()
    return await db.folders.find_one({'folderId': folder_id})

async def get_or_create_quality_folder(parent_folder_id: str, quality: str, created_by: int):
    db = get_database()
    
    quality_folder = await db.folders.find_one({
        'parentFolderId': parent_folder_id,
        'isQualityFolder': True,
        'quality': quality
    })
    
    if quality_folder:
        return quality_folder['folderId']
    
    quality_folder_id = generate_folder_id()
    await create_folder(
        folder_id=quality_folder_id,
        name=quality,
        created_by=created_by,
        parent_folder_id=parent_folder_id,
        is_quality_folder=True,
        quality=quality
    )
    
    return quality_folder_id

async def get_or_create_folder_by_name(folder_name: str, created_by: int, parent_folder_id: Optional[str] = None):
    db = get_database()
    
    query = {
        'name': folder_name,
        'createdBy': created_by,
        'isQualityFolder': False
    }
    
    if parent_folder_id:
        query['parentFolderId'] = parent_folder_id
    else:
        query['parentFolderId'] = None
    
    folder = await db.folders.find_one(query)
    
    if folder:
        return folder['folderId']
    
    folder_id = generate_folder_id()
    await create_folder(
        folder_id=folder_id,
        name=folder_name,
        created_by=created_by,
        parent_folder_id=parent_folder_id
    )
    
    return folder_id

async def get_user_folders(user_id: int, page: int = 1, page_size: int = 10, parent_id: Optional[str] = None):
    db = get_database()
    skip = (page - 1) * page_size
    
    query = {'createdBy': user_id, 'isQualityFolder': False}
    if parent_id:
        query['parentFolderId'] = parent_id
    else:
        query['parentFolderId'] = None
    
    cursor = db.folders.find(query).sort('createdAt', -1).skip(skip).limit(page_size)
    folders = await cursor.to_list(length=page_size)
    
    for folder in folders:
        folder['fileCount'] = await count_folder_files(folder['folderId'])
        folder['subfolderCount'] = await count_subfolders(folder['folderId'])
    
    return folders

async def get_quality_folders(parent_folder_id: str):
    db = get_database()
    cursor = db.folders.find({
        'parentFolderId': parent_folder_id,
        'isQualityFolder': True
    }).sort('quality', 1)
    return await cursor.to_list(length=10)

async def count_user_folders(user_id: int, parent_id: Optional[str] = None):
    db = get_database()
    query = {'createdBy': user_id, 'isQualityFolder': False}
    if parent_id:
        query['parentFolderId'] = parent_id
    else:
        query['parentFolderId'] = None
    return await db.folders.count_documents(query)

async def count_subfolders(folder_id: str):
    db = get_database()
    return await db.folders.count_documents({'parentFolderId': folder_id})

async def update_folder(folder_id: str, update_data: dict):
    db = get_database()
    update_data['updatedAt'] = datetime.utcnow()
    result = await db.folders.update_one(
        {'folderId': folder_id},
        {'$set': update_data}
    )
    return result.modified_count > 0

async def delete_folder(folder_id: str, user_id: int):
    db = get_database()
    
    folder = await db.folders.find_one({'folderId': folder_id, 'createdBy': user_id})
    if not folder:
        return False
    
    async def recursive_delete(fid):
        subfolders = await db.folders.find({'parentFolderId': fid}).to_list(length=None)
        for subfolder in subfolders:
            await recursive_delete(subfolder['folderId'])
        
        await db.files.delete_many({'folderId': fid})
        await db.folders.delete_one({'folderId': fid})
    
    await recursive_delete(folder_id)
    
    if folder.get('parentFolderId'):
        await db.folders.update_one(
            {'folderId': folder['parentFolderId']},
            {'$inc': {'subfolderCount': -1}}
        )
    
    return True

async def add_file_to_folder(file_data: dict, uploaded_by: int):
    db = get_database()
    
    file_data['uploadedBy'] = uploaded_by
    file_data['uploadedAt'] = datetime.utcnow()
    file_data['views'] = 0
    file_data['downloads'] = 0
    
    if 'baseName' not in file_data:
        file_data['baseName'] = file_data.get('fileName', 'unknown')
    
    if 'quality' not in file_data:
        file_data['quality'] = 'Unknown'
    
    if 'parsedFromCaption' not in file_data:
        file_data['parsedFromCaption'] = False
    
    existing = await db.files.find_one({
        'telegramFileUniqueId': file_data.get('telegramFileUniqueId'),
        'folderId': file_data['folderId']
    })
    if existing:
        return {
            'documentId': str(existing['_id']),
            'inserted': False
        }
    
    result = await db.files.insert_one(file_data)
    
    if result.inserted_id:
        await db.folders.update_one(
            {'folderId': file_data['folderId']},
            {'$inc': {'fileCount': 1}}
        )
    
    return {
        'documentId': str(result.inserted_id),
        'inserted': True
    }

async def get_file_by_id(file_id: str):
    db = get_database()
    try:
        return await db.files.find_one({'_id': ObjectId(file_id)})
    except InvalidId:
        return None

async def get_folder_files(folder_id: str, page: int = 1, page_size: int = 10):
    db = get_database()
    skip = (page - 1) * page_size
    
    cursor = db.files.find({'folderId': folder_id}).sort('uploadedAt', -1).skip(skip).limit(page_size)
    files = await cursor.to_list(length=page_size)
    
    for file in files:
        file['fileId'] = str(file['_id'])
    
    return files

async def get_files_by_basename(folder_id: str, base_name: str):
    db = get_database()
    cursor = db.files.find({
        'folderId': folder_id,
        'baseName': base_name
    }).sort('quality', 1)
    files = await cursor.to_list(length=None)
    
    for file in files:
        file['fileId'] = str(file['_id'])
    
    return files

async def get_simplified_file_list(folder_id: str):
    db = get_database()
    
    pipeline = [
        {'$match': {'folderId': folder_id}},
        {'$group': {
            '_id': '$baseName',
            'baseName': {'$first': '$baseName'},
            'qualities': {'$addToSet': '$quality'},
            'fileCount': {'$sum': 1},
            'totalSize': {'$sum': '$size'},
            'files': {'$push': {
                'fileId': {'$toString': '$_id'},
                'quality': '$quality',
                'size': '$size',
                'fileName': '$fileName'
            }}
        }},
        {'$sort': {'baseName': 1}}
    ]
    
    cursor = db.files.aggregate(pipeline)
    return await cursor.to_list(length=None)

async def count_folder_files(folder_id: str):
    db = get_database()
    return await db.files.count_documents({'folderId': folder_id})

async def update_file(file_id: str, update_data: dict):
    db = get_database()
    try:
        result = await db.files.update_one(
            {'_id': ObjectId(file_id)},
            {'$set': update_data}
        )
        return result.modified_count > 0
    except InvalidId:
        return False

async def delete_file(file_id: str):
    db = get_database()
    
    try:
        file = await db.files.find_one({'_id': ObjectId(file_id)})
        if not file:
            return False
        
        result = await db.files.delete_one({'_id': ObjectId(file_id)})
        
        if result.deleted_count > 0:
            await db.folders.update_one(
                {'folderId': file['folderId']},
                {'$inc': {'fileCount': -1}}
            )
        
        return result.deleted_count > 0
    except InvalidId:
        return False

async def increment_views(file_id: str):
    db = get_database()
    try:
        await db.files.update_one(
            {'_id': ObjectId(file_id)},
            {'$inc': {'views': 1}}
        )
    except InvalidId:
        pass

async def increment_downloads(file_id: str):
    db = get_database()
    try:
        await db.files.update_one(
            {'_id': ObjectId(file_id)},
            {'$inc': {'downloads': 1}}
        )
    except InvalidId:
        pass

async def get_all_users() -> List[int]:
    db = get_database()
    
    folder_users = await db.folders.distinct('createdBy')
    file_users = await db.files.distinct('uploadedBy')
    
    all_users = list(set(folder_users + file_users))
    return all_users

async def get_stats(user_id: int):
    db = get_database()
    
    folder_count = await db.folders.count_documents({'createdBy': user_id, 'isQualityFolder': False})
    
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