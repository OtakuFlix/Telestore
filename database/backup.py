import json
import os
from datetime import datetime
from typing import Dict, List
from database.connection import get_database
from bson import ObjectId
from config import config

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

async def export_database() -> str:
    db = get_database()
    
    folders = await db.folders.find({}).to_list(length=None)
    files = await db.files.find({}).to_list(length=None)
    
    backup_data = {
        'export_date': datetime.utcnow().isoformat(),
        'database_name': config.MONGODB_DB,
        'folders': folders,
        'files': files,
        'stats': {
            'total_folders': len(folders),
            'total_files': len(files)
        }
    }
    
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:16]
    filename = f"backup_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, cls=JSONEncoder, indent=2, ensure_ascii=False)
    
    return filename

async def import_database(json_path: str) -> Dict:
    db = get_database()
    
    with open(json_path, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)
    
    folders = backup_data.get('folders', [])
    files = backup_data.get('files', [])
    
    for folder in folders:
        if '_id' in folder:
            folder['_id'] = ObjectId(folder['_id'])
        if 'createdAt' in folder:
            folder['createdAt'] = datetime.fromisoformat(folder['createdAt'])
        if 'updatedAt' in folder:
            folder['updatedAt'] = datetime.fromisoformat(folder['updatedAt'])
    
    for file in files:
        if '_id' in file:
            file['_id'] = ObjectId(file['_id'])
        if 'uploadedAt' in file:
            file['uploadedAt'] = datetime.fromisoformat(file['uploadedAt'])
    
    folders_inserted = 0
    files_inserted = 0
    folders_skipped = 0
    files_skipped = 0
    
    if folders:
        for folder in folders:
            try:
                await db.folders.insert_one(folder)
                folders_inserted += 1
            except Exception:
                folders_skipped += 1
    
    if files:
        for file in files:
            try:
                await db.files.insert_one(file)
                files_inserted += 1
            except Exception:
                files_skipped += 1
    
    return {
        'success': True,
        'folders_imported': folders_inserted,
        'folders_skipped': folders_skipped,
        'files_imported': files_inserted,
        'files_skipped': files_skipped,
        'total_folders': len(folders),
        'total_files': len(files)
    }

async def log_change(operation: str, collection: str, data: Dict):
    db = get_database()
    
    log_entry = {
        'timestamp': datetime.utcnow(),
        'operation': operation,
        'collection': collection,
        'data': data
    }
    
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:16]
    filename = f"{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(log_entry, f, cls=JSONEncoder, indent=2, ensure_ascii=False)
    
    return filename