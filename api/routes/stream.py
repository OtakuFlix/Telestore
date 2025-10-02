# ==================== api/routes/stream.py ====================
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from database.operations import get_file_by_id, increment_views
from bot.client import bot
from config import config
import re

router = APIRouter()

@router.get("/{fileId}")
async def stream_file(fileId: str, request: Request):
    """Stream file directly (video URL for players)"""
    # Get file from database
    file_data = await get_file_by_id(fileId)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")
    
    telegram_file_id = file_data.get('telegramFileId')
    if not telegram_file_id:
        raise HTTPException(status_code=404, detail="Telegram file ID not found")
    
    # Increment view count
    await increment_views(fileId)
    
    try:
        # Get file from Telegram
        file_size = file_data.get('size', 0)
        mime_type = file_data.get('mimeType', 'video/mp4')
        
        # Parse range header for seeking support
        range_header = request.headers.get('range')
        start = 0
        end = file_size - 1
        
        if range_header:
            range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
            if range_match:
                start = int(range_match.group(1))
                if range_match.group(2):
                    end = int(range_match.group(2))
        
        # Stream file from Telegram
        async def file_stream():
            offset = start
            chunk_size = 1024 * 1024  # 1MB chunks
            
            while offset <= end:
                try:
                    chunk = await bot.download_media(
                        telegram_file_id,
                        in_memory=True,
                        file_size=min(chunk_size, end - offset + 1),
                        offset=offset
                    )
                    
                    if not chunk:
                        break
                    
                    yield chunk
                    offset += len(chunk)
                    
                except Exception as e:
                    print(f"Error streaming chunk: {e}")
                    break
        
        headers = {
            'Content-Type': mime_type,
            'Accept-Ranges': 'bytes',
            'Content-Length': str(end - start + 1),
        }
        
        if range_header:
            headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            status_code = 206
        else:
            status_code = 200
        
        return StreamingResponse(
            file_stream(),
            status_code=status_code,
            headers=headers,
            media_type=mime_type
        )
        
    except Exception as e:
        print(f"Error streaming file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/watch/{fileId}")
async def watch_file(fileId: str):
    """Embedded video player page"""
    file_data = await get_file_by_id(fileId)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_name = file_data.get('fileName', 'Video')
    stream_url = f"{config.BASE_APP_URL}/{fileId}"
    download_url = f"{config.BASE_APP_URL}/dl/{fileId}"
    thumbnail = file_data.get('thumbnail', '')
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{file_name}</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                background: #000;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                display: flex;
                flex-direction: column;
                min-height: 100vh;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                width: 100%;
                padding: 20px;
            }}
            .video-wrapper {{
                position: relative;
                width: 100%;
                padding-top: 56.25%;
                background: #000;
                border-radius: 8px;
                overflow: hidden;
            }}
            video {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                outline: none;
            }}
            .info {{
                margin-top: 20px;
                color: #fff;
            }}
            h1 {{
                font-size: 24px;
                margin-bottom: 10px;
            }}
            .actions {{
                margin-top: 20px;
                display: flex;
                gap: 10px;
            }}
            .btn {{
                padding: 10px 20px;
                background: #1976d2;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                font-weight: 500;
                transition: background 0.3s;
            }}
            .btn:hover {{
                background: #1565c0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="video-wrapper">
                <video controls autoplay poster="{thumbnail}">
                    <source src="{stream_url}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            </div>
            <div class="info">
                <h1>{file_name}</h1>
                <div class="actions">
                    <a href="{download_url}" class="btn" download>⬇️ Download</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)