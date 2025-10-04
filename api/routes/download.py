# ==================== api/routes/download.py ====================
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from database.operations import get_file_by_id, increment_downloads

router = APIRouter()

def _extract_bot_client():
    """Retrieve the active bot client from the global store."""
    from bot.client import get_bot
    return get_bot()

@router.get("/dl/{fileId}")
async def download_file(fileId: str):
    """Direct download endpoint"""
    try:
        bot_client = _extract_bot_client()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Bot service not ready") from exc
    
    # Get file from database
    file_data = await get_file_by_id(fileId)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")
    
    telegram_file_id = file_data.get('telegramFileId')
    if not telegram_file_id:
        raise HTTPException(status_code=404, detail="Telegram file ID not found")
    
    # Increment download count
    await increment_downloads(fileId)
    
    file_name = file_data.get('fileName', 'download')
    mime_type = file_data.get('mimeType', 'application/octet-stream')
    file_size = file_data.get('size', 0)
    
    try:
        # Stream file from Telegram
        async def file_stream():
            chunk_size = 1024 * 1024  # 1MB chunks
            offset = 0
            
            while offset < file_size:
                try:
                    chunk = await bot_client.download_media(
                        telegram_file_id,
                        in_memory=True,
                        file_size=min(chunk_size, file_size - offset),
                        offset=offset
                    )
                    
                    if not chunk:
                        break
                    
                    yield chunk
                    offset += len(chunk)
                    
                except Exception as e:
                    print(f"Error downloading chunk: {e}")
                    break
        
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
        
    except Exception as e:
        print(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))