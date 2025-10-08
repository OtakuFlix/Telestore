from fastapi import APIRouter, HTTPException, Query
from database.operations import (
    get_user_folders, get_folder_files, get_folder_by_id,
    get_simplified_file_list, get_quality_folders, get_files_by_basename,
    get_file_by_id
)
from typing import Optional
from utils.master_id import generate_master_group_id

router = APIRouter()
@router.get("/api/folder_list")
async def get_folder_list(user_id: int, parent_id: Optional[str] = None, page: int = 1, page_size: int = 20):
    try:
        folders = await get_user_folders(user_id, page=page, page_size=page_size, parent_id=parent_id)
        
        result = []
        for folder in folders:
            result.append({
                'folderId': folder['folderId'],
                'name': folder['name'],
                'createdAt': folder['createdAt'].isoformat(),
                'fileCount': folder.get('fileCount', 0),
                'subfolderCount': folder.get('subfolderCount', 0),
                'isQualityFolder': folder.get('isQualityFolder', False),
                'quality': folder.get('quality')
            })
        
        return {
            'success': True,
            'folders': result,
            'page': page,
            'pageSize': page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/file_list/{folder_id}")
async def get_simplified_file_list_api(folder_id: str):
    try:
        folder = await get_folder_by_id(folder_id)
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        from database.connection import get_database
        db = get_database()
        
        quality_folders = await get_quality_folders(folder_id)
        
        if not quality_folders:
            pipeline = [
                {'$match': {'folderId': folder_id}},
                {'$group': {
                    '_id': '$baseName',
                    'baseName': {'$first': '$baseName'},
                    'files': {'$push': {
                        'fileId': {'$toString': '$_id'},
                        'quality': '$quality',
                        'size': '$size',
                        'fileName': '$fileName',
                        'uploadedAt': '$uploadedAt'
                    }}
                }},
                {'$sort': {'baseName': 1}}
            ]
            
            cursor = db.files.aggregate(pipeline)
            file_groups = await cursor.to_list(length=None)
        else:
            quality_folder_ids = [qf['folderId'] for qf in quality_folders]
            
            pipeline = [
                {'$match': {'folderId': {'$in': quality_folder_ids}}},
                {'$group': {
                    '_id': '$baseName',
                    'baseName': {'$first': '$baseName'},
                    'files': {'$push': {
                        'fileId': {'$toString': '$_id'},
                        'quality': '$quality',
                        'size': '$size',
                        'fileName': '$fileName',
                        'uploadedAt': '$uploadedAt'
                    }}
                }},
                {'$sort': {'baseName': 1}}
            ]
            
            cursor = db.files.aggregate(pipeline)
            file_groups = await cursor.to_list(length=None)
        
        result = []
        for group in file_groups:
            base_name = group['baseName']
            
            file_name_without_ext = base_name
            if '.' in base_name:
                parts = base_name.rsplit('.', 1)
                if parts[1].lower() in ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm']:
                    file_name_without_ext = parts[0]
            
            master_group_id = generate_master_group_id(folder_id, file_name_without_ext)
            
            qualities = {}
            for file in group['files']:
                quality = file['quality']
                size_bytes = file['size']
                size_gb = size_bytes / (1024 * 1024 * 1024)
                size_mb = size_bytes / (1024 * 1024)
                
                if size_gb >= 1:
                    size_str = f"{size_gb:.2f} GB"
                else:
                    size_str = f"{size_mb:.1f} MB"
                
                qualities[quality] = {
                    'fileId': file['fileId'],
                    'size': size_str,
                    'uploaded_date': file['uploadedAt'].isoformat() if file.get('uploadedAt') else None
                }
            
            result.append({
                'name': file_name_without_ext,
                'master_group_id': master_group_id,
                'qualities': qualities
            })
        
        return {
            'success': True,
            'folderId': folder_id,
            'folderName': folder['name'],
            'files': result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/stream/{master_group_id}")
async def stream_by_master_group(master_group_id: str, quality: str = Query(default="1080p")):
    try:
        from database.connection import get_database
        db = get_database()
        
        all_files = await db.files.find({}).to_list(length=None)
        
        target_file = None
        for file in all_files:
            base_name = file.get('baseName', '')
            folder_id = file.get('folderId', '')
            computed_id = generate_master_group_id(folder_id, base_name)
            
            if computed_id == master_group_id and file.get('quality') == quality:
                target_file = file
                break
        
        if not target_file:
            available_qualities = []
            for file in all_files:
                base_name = file.get('baseName', '')
                folder_id = file.get('folderId', '')
                computed_id = generate_master_group_id(folder_id, base_name)
                
                if computed_id == master_group_id:
                    available_qualities.append(file.get('quality'))
            
            if available_qualities:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Quality '{quality}' not available. Available: {', '.join(set(available_qualities))}"
                )
            else:
                raise HTTPException(status_code=404, detail="Master group not found")
        
        file_id = str(target_file['_id'])
        
        from config import config
        return {
            'success': True,
            'message': f'Streaming {quality} version',
            'fileId': file_id,
            'streamUrl': f"{config.BASE_APP_URL}/{file_id}",
            'watchUrl': f"{config.BASE_APP_URL}/watch/{file_id}",
            'downloadUrl': f"{config.BASE_APP_URL}/dl/{file_id}",
            'quality': quality,
            'fileName': target_file.get('fileName'),
            'size': target_file.get('size')
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/quality_info/{file_id}")
async def get_quality_info(file_id: str):
    try:
        from bson.objectid import ObjectId
        
        file_data = await get_file_by_id(file_id)
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        
        base_name = file_data.get('baseName')
        folder_id = file_data.get('folderId')
        
        if not base_name:
            return {
                'success': True,
                'master_group_id': generate_master_group_id(folder_id, file_data.get('fileName', '')),
                'qualities': [{
                    'quality': file_data.get('quality', 'Unknown'),
                    'fileId': str(file_data['_id']),
                    'streamUrl': f"/{str(file_data['_id'])}",
                    'size': file_data.get('size', 0)
                }]
            }
        
        files = await get_files_by_basename(folder_id, base_name)
        
        qualities = []
        for f in files:
            qualities.append({
                'quality': f.get('quality', 'Unknown'),
                'fileId': f['fileId'],
                'streamUrl': f"/{f['fileId']}",
                'size': f.get('size', 0)
            })
        
        quality_order = {'4K': 0, '1080p': 1, '720p': 2, '480p': 3, '360p': 4, 'Unknown': 99}
        qualities_sorted = sorted(qualities, key=lambda x: quality_order.get(x['quality'], 50))
        
        return {
            'success': True,
            'master_group_id': generate_master_group_id(folder_id, base_name),
            'baseName': base_name,
            'qualities': qualities_sorted
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/s_file_list/{folder_id}")
async def get_simplified_files(folder_id: str):
    try:
        folder = await get_folder_by_id(folder_id)
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        file_groups = await get_simplified_file_list(folder_id)
        
        result = []
        for group in file_groups:
            result.append({
                'baseName': group['baseName'],
                'qualities': sorted(group.get('qualities', [])),
                'fileCount': group.get('fileCount', 0),
                'totalSize': group.get('totalSize', 0),
                'files': group.get('files', [])
            })
        
        return {
            'success': True,
            'folderId': folder_id,
            'folderName': folder['name'],
            'fileGroups': result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/quality_folders/{parent_folder_id}")
async def get_quality_folder_list(parent_folder_id: str):
    try:
        parent_folder = await get_folder_by_id(parent_folder_id)
        if not parent_folder:
            raise HTTPException(status_code=404, detail="Parent folder not found")
        
        quality_folders = await get_quality_folders(parent_folder_id)
        
        result = []
        for qf in quality_folders:
            result.append({
                'folderId': qf['folderId'],
                'quality': qf.get('quality', 'Unknown'),
                'fileCount': qf.get('fileCount', 0),
                'createdAt': qf['createdAt'].isoformat()
            })
        
        return {
            'success': True,
            'parentFolderId': parent_folder_id,
            'parentFolderName': parent_folder['name'],
            'qualityFolders': result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/files_by_name/{folder_id}/{base_name}")
async def get_files_by_name(folder_id: str, base_name: str):
    try:
        files = await get_files_by_basename(folder_id, base_name)
        
        result = []
        for file in files:
            result.append({
                'fileId': file['fileId'],
                'fileName': file.get('fileName', 'Unnamed'),
                'quality': file.get('quality', 'Unknown'),
                'size': file.get('size', 0),
                'mimeType': file.get('mimeType', ''),
                'duration': file.get('duration'),
                'watchUrl': f"/watch/{file['fileId']}",
                'streamUrl': f"/{file['fileId']}",
                'downloadUrl': f"/dl/{file['fileId']}"
            })
        
        master_group_id = generate_master_group_id(folder_id, base_name)
        
        return {
            'success': True,
            'folderId': folder_id,
            'baseName': base_name,
            'master_group_id': master_group_id,
            'files': result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/master_info/{master_group_id}")
async def get_master_group_info(master_group_id: str):
    try:
        from database.connection import get_database
        db = get_database()
        
        # Search by parent_master_group_id (for quality folder structure)
        matched_files = await db.files.find({
            'parent_master_group_id': master_group_id
        }).to_list(length=None)
        
        if not matched_files:
            raise HTTPException(status_code=404, detail="Master group not found")
        
        folder_id = matched_files[0].get('folderId')
        base_name = matched_files[0].get('baseName')
        
        qualities = {}
        for file in matched_files:
            quality = file.get('quality', 'Unknown')
            size_mb = file.get('size', 0) / (1024 * 1024)
            
            qualities[quality] = {
                'fileId': str(file['_id']),
                'size': f"{size_mb:.1f} MB",
                'fileName': file.get('fileName'),
                'uploadedAt': file.get('uploadedAt').isoformat() if file.get('uploadedAt') else None
            }
        
        return {
            'success': True,
            'master_group_id': master_group_id,
            'folderId': folder_id,
            'baseName': base_name,
            'qualities': qualities,
            'totalFiles': len(matched_files)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))