# ==================== api/routes/download.py ====================
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from database.operations import get_file_by_id, increment_downloads
from bot.client import bot

router = APIRouter()

@router.get("/dl/{fileId}")
async def download_file(fileId: str):
    """Direct download endpoint"""
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
                    chunk = await bot.download_media(
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