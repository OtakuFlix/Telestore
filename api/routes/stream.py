# ==================== api/routes/stream.py ====================
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from database.operations import get_file_by_id, increment_views
from config import config
import re

router = APIRouter()

def _extract_bot_client():
    """Retrieve the active bot client from the global store."""
    from bot.client import get_bot
    return get_bot()

@router.get("/{fileId}")
async def stream_file(fileId: str, request: Request):
    """Stream file directly (video URL for players)"""
    try:
        bot_client = _extract_bot_client()
    except Exception as exc:  # get_bot raises if bot not ready
        raise HTTPException(status_code=503, detail="Bot service not ready") from exc
    
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
                    chunk = await bot_client.download_media(
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
    """Embedded video player page with ArtPlayer"""
    file_data = await get_file_by_id(fileId)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_name = file_data.get('fileName', 'Video')
    stream_url = f"{config.BASE_APP_URL}/{fileId}"
    download_url = f"{config.BASE_APP_URL}/dl/{fileId}"
    thumbnail = file_data.get('thumbnail', '')
    
    # Extract metadata
    quality = file_data.get('quality', '')
    language = file_data.get('language', '')
    size_mb = file_data.get('size', 0) / (1024 * 1024)
    duration = file_data.get('duration', 0)
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{file_name} - TeleStore</title>
        
        <!-- ArtPlayer CSS -->
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/artplayer@5.1.1/dist/artplayer.css">
        
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                background: linear-gradient(135deg, #0f0f0f 0%, #1a1a2e 100%);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                color: #fff;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }}
            
            .header {{
                background: rgba(0, 0, 0, 0.3);
                backdrop-filter: blur(10px);
                padding: 15px 30px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            .logo {{
                font-size: 24px;
                font-weight: bold;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                width: 100%;
                padding: 30px 20px;
                flex: 1;
            }}
            
            .video-section {{
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            .player-wrapper {{
                position: relative;
                width: 100%;
                padding-top: 56.25%;
                background: #000;
            }}
            
            .artplayer-app {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
            }}
            
            .info-section {{
                padding: 25px 30px;
            }}
            
            .title {{
                font-size: 28px;
                font-weight: 600;
                margin-bottom: 15px;
                line-height: 1.3;
            }}
            
            .metadata {{
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin-bottom: 20px;
                padding: 15px;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 8px;
            }}
            
            .meta-item {{
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 14px;
                color: #b0b0b0;
            }}
            
            .meta-icon {{
                font-size: 18px;
            }}
            
            .meta-value {{
                color: #fff;
                font-weight: 500;
            }}
            
            .actions {{
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
            }}
            
            .btn {{
                display: inline-flex;
                align-items: center;
                gap: 10px;
                padding: 12px 24px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 500;
                font-size: 15px;
                transition: all 0.3s ease;
                border: none;
                cursor: pointer;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }}
            
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
            }}
            
            .btn-secondary {{
                background: rgba(255, 255, 255, 0.1);
                box-shadow: none;
            }}
            
            .btn-secondary:hover {{
                background: rgba(255, 255, 255, 0.2);
                box-shadow: none;
            }}
            
            .footer {{
                text-align: center;
                padding: 20px;
                color: #666;
                font-size: 14px;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            @media (max-width: 768px) {{
                .header {{
                    padding: 12px 20px;
                }}
                
                .logo {{
                    font-size: 20px;
                }}
                
                .container {{
                    padding: 20px 15px;
                }}
                
                .title {{
                    font-size: 22px;
                }}
                
                .metadata {{
                    gap: 15px;
                }}
                
                .actions {{
                    flex-direction: column;
                }}
                
                .btn {{
                    width: 100%;
                    justify-content: center;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">🎬 TeleStore</div>
        </div>
        
        <div class="container">
            <div class="video-section">
                <div class="player-wrapper">
                    <div id="artplayer"></div>
                </div>
                
                <div class="info-section">
                    <h1 class="title">{file_name}</h1>
                    
                    <div class="metadata">
                        {f'<div class="meta-item"><span class="meta-icon">🎥</span><span class="meta-value">{quality}</span></div>' if quality else ''}
                        {f'<div class="meta-item"><span class="meta-icon">🗣️</span><span class="meta-value">{language}</span></div>' if language else ''}
                        <div class="meta-item">
                            <span class="meta-icon">💾</span>
                            <span class="meta-value">{size_mb:.2f} MB</span>
                        </div>
                        {f'<div class="meta-item"><span class="meta-icon">⏱️</span><span class="meta-value">{duration // 60}m {duration % 60}s</span></div>' if duration else ''}
                    </div>
                    
                    <div class="actions">
                        <a href="{download_url}" class="btn" download>
                            ⬇️ Download Video
                        </a>
                        <button onclick="copyLink()" class="btn btn-secondary">
                            🔗 Copy Link
                        </button>
                        <button onclick="shareVideo()" class="btn btn-secondary">
                            📤 Share
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            Powered by TeleStore • Fast & Secure Video Streaming
        </div>
        
        <!-- ArtPlayer JS -->
        <script src="https://cdn.jsdelivr.net/npm/artplayer@5.1.1/dist/artplayer.js"></script>
        
        <script>
            // Initialize ArtPlayer
            const art = new Artplayer({{
                container: '#artplayer',
                url: '{stream_url}',
                title: '{file_name}',
                poster: '{thumbnail}',
                volume: 0.8,
                autoplay: false,
                pip: true,
                fullscreen: true,
                fullscreenWeb: true,
                setting: true,
                playbackRate: true,
                aspectRatio: true,
                screenshot: true,
                hotkey: true,
                mutex: true,
                theme: '#667eea',
                settings: [
                    {{
                        html: 'Quality',
                        selector: [
                            {{
                                html: 'Auto',
                                default: true,
                            }},
                        ],
                    }},
                ],
                moreVideoAttr: {{
                    crossOrigin: 'anonymous',
                }},
            }});
            
            // Auto-play on load (optional)
            art.on('ready', () => {{
                console.log('Player ready');
            }});
            
            // Copy link function
            function copyLink() {{
                const url = window.location.href;
                navigator.clipboard.writeText(url).then(() => {{
                    alert('✅ Link copied to clipboard!');
                }}).catch(err => {{
                    console.error('Failed to copy:', err);
                }});
            }}
            
            // Share function
            function shareVideo() {{
                if (navigator.share) {{
                    navigator.share({{
                        title: '{file_name}',
                        text: 'Watch this video on TeleStore',
                        url: window.location.href
                    }}).catch(err => console.log('Error sharing:', err));
                }} else {{
                    copyLink();
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)