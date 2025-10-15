# ==================== api/routes/download.py ====================
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from database.operations import get_file_by_id, increment_downloads
from bot.client import get_bot
from pyrogram import raw
from pyrogram.file_id import FileId, FileType, ThumbnailSource
from pyrogram import utils as pyro_utils
from pyrogram.session import Session, Auth
import re
import os

router = APIRouter()

@router.get("/dl/{fileId}")
async def download_file(fileId: str):
    """Direct download with DC migration support"""
    if not re.match(r'^[a-f0-9]{24}$', fileId):
        raise HTTPException(status_code=400, detail="Invalid file ID format")
    
    try:
        bot_client = get_bot()
    except Exception:
        raise HTTPException(status_code=503, detail="Bot service not ready")
    
    file_data = await get_file_by_id(fileId)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")
    
    telegram_file_id = file_data.get('telegramFileId')
    if not telegram_file_id:
        raise HTTPException(status_code=404, detail="Telegram file ID not found")
    
    await increment_downloads(fileId)
    
    # Get filename and mime type
    file_name = file_data.get('fileName', 'download')
    mime_type = file_data.get('mimeType', 'application/octet-stream')
    file_size = file_data.get('size', 0)
    
    # Ensure file has an extension; if not, add .mkv
    if not os.path.splitext(file_name)[1]:
        file_name += '.mkv'
    
    # Decode file_id
    file_id_obj = FileId.decode(telegram_file_id)
    
    # Get or create media session for the DC
    media_session = await get_media_session(bot_client, file_id_obj)
    
    async def file_stream():
        offset = 0
        chunk_size = 1024 * 1024  # 1MB
        
        # Get file location
        location = await get_location(file_id_obj)
        
        try:
            while offset < file_size:
                r = await media_session.invoke(
                    raw.functions.upload.GetFile(
                        location=location,
                        offset=offset,
                        limit=chunk_size
                    )
                )
                
                if isinstance(r, raw.types.upload.File):
                    chunk = r.bytes
                    if not chunk:
                        break
                    yield chunk
                    offset += len(chunk)
                else:
                    break
                    
        except Exception as e:
            print(f"Error downloading: {e}")
            raise
    
    headers = {
        'Content-Disposition': f'attachment; filename="{file_name}"',
        'Content-Type': mime_type,
        'Content-Length': str(file_size),
    }
    
    return StreamingResponse(
        file_stream(),
        headers=headers,
        media_type=mime_type
    )


async def get_media_session(client, file_id: FileId):
    """Get or create media session for file's DC"""
    dc_id = file_id.dc_id
    
    if not hasattr(client, 'media_sessions'):
        client.media_sessions = {}
    
    if dc_id in client.media_sessions:
        return client.media_sessions[dc_id]
    
    if dc_id != await client.storage.dc_id():
        # Export authorization
        media_session = Session(
            client,
            dc_id,
            await Auth(client, dc_id, await client.storage.test_mode()).create(),
            await client.storage.test_mode(),
            is_media=True
        )
        await media_session.start()
        
        for _ in range(6):
            try:
                exported_auth = await client.invoke(
                    raw.functions.auth.ExportAuthorization(dc_id=dc_id)
                )
                
                await media_session.invoke(
                    raw.functions.auth.ImportAuthorization(
                        id=exported_auth.id,
                        bytes=exported_auth.bytes
                    )
                )
                break
            except Exception as e:
                print(f"Auth attempt failed: {e}")
                continue
        
        client.media_sessions[dc_id] = media_session
        return media_session
    else:
        # Same DC as bot
        media_session = Session(
            client,
            dc_id,
            await client.storage.auth_key(),
            await client.storage.test_mode(),
            is_media=True
        )
        await media_session.start()
        client.media_sessions[dc_id] = media_session
        return media_session


async def get_location(file_id: FileId):
    """Get file location for raw API"""
    file_type = file_id.file_type
    
    if file_type == FileType.CHAT_PHOTO:
        if file_id.chat_id > 0:
            peer = raw.types.InputPeerUser(
                user_id=file_id.chat_id,
                access_hash=file_id.chat_access_hash
            )
        else:
            if file_id.chat_access_hash == 0:
                peer = raw.types.InputPeerChat(chat_id=-file_id.chat_id)
            else:
                peer = raw.types.InputPeerChannel(
                    channel_id=pyro_utils.get_channel_id(file_id.chat_id),
                    access_hash=file_id.chat_access_hash
                )
        
        location = raw.types.InputPeerPhotoFileLocation(
            peer=peer,
            volume_id=file_id.volume_id,
            local_id=file_id.local_id,
            big=file_id.thumbnail_source == ThumbnailSource.CHAT_PHOTO_BIG
        )
    elif file_type == FileType.PHOTO:
        location = raw.types.InputPhotoFileLocation(
            id=file_id.media_id,
            access_hash=file_id.access_hash,
            file_reference=file_id.file_reference,
            thumb_size=file_id.thumbnail_size
        )
    else:
        location = raw.types.InputDocumentFileLocation(
            id=file_id.media_id,
            access_hash=file_id.access_hash,
            file_reference=file_id.file_reference,
            thumb_size=file_id.thumbnail_size
        )
    
    return location
