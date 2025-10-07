from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from database.operations import get_file_by_id, increment_views
from bot.client import get_bot
from config import config
from pyrogram import raw
from pyrogram.file_id import FileId, FileType, ThumbnailSource
from pyrogram.session import Session, Auth
from pyrogram import utils as pyro_utils
import re
import math

router = APIRouter()

@router.get("/{fileId}")
async def stream_file(fileId: str, request: Request):
    """Direct stream endpoint with range support"""
    if not re.match(r'^[a-f0-9]{24}$', fileId):
        raise HTTPException(status_code=400, detail="Invalid file ID format")
    
    file_data = await get_file_by_id(fileId)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")
    
    telegram_file_id = file_data.get('telegramFileId')
    if not telegram_file_id:
        raise HTTPException(status_code=404, detail="Telegram file ID not found")
    
    await increment_views(fileId)
    
    return await stream_file_direct(file_data, request)

async def stream_file_direct(file_data: dict, request: Request):
    """Stream with DC migration support"""
    try:
        bot_client = get_bot()
    except Exception:
        raise HTTPException(status_code=503, detail="Bot service not ready")
    
    telegram_file_id = file_data.get('telegramFileId')
    file_size = file_data.get('size', 0)
    mime_type = file_data.get('mimeType', 'video/mp4')
    file_name = file_data.get('fileName', 'file')
    
    range_header = request.headers.get('range', '')
    
    if range_header:
        from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
        from_bytes = int(from_bytes)
        until_bytes = int(until_bytes) if until_bytes else file_size - 1
    else:
        from_bytes = 0
        until_bytes = file_size - 1
    
    if (until_bytes > file_size) or (from_bytes < 0) or (until_bytes < from_bytes):
        raise HTTPException(status_code=416, detail="Range not satisfiable")
    
    chunk_size = 1024 * 1024
    until_bytes = min(until_bytes, file_size - 1)
    
    offset = from_bytes - (from_bytes % chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = until_bytes % chunk_size + 1
    
    req_length = until_bytes - from_bytes + 1
    part_count = math.ceil(until_bytes / chunk_size) - math.floor(offset / chunk_size)
    
    file_id_obj = FileId.decode(telegram_file_id)
    media_session = await get_media_session(bot_client, file_id_obj)
    location = await get_location(file_id_obj)
    
    async def file_stream():
        nonlocal offset
        current_part = 1
        
        try:
            r = await media_session.invoke(
                raw.functions.upload.GetFile(location=location, offset=offset, limit=chunk_size)
            )
            
            if isinstance(r, raw.types.upload.File):
                while True:
                    chunk = r.bytes
                    if not chunk:
                        break
                    
                    if part_count == 1:
                        yield chunk[first_part_cut:last_part_cut]
                    elif current_part == 1:
                        yield chunk[first_part_cut:]
                    elif current_part == part_count:
                        yield chunk[:last_part_cut]
                    else:
                        yield chunk
                    
                    current_part += 1
                    offset += chunk_size
                    
                    if current_part > part_count:
                        break
                    
                    r = await media_session.invoke(
                        raw.functions.upload.GetFile(location=location, offset=offset, limit=chunk_size)
                    )
        except Exception as e:
            print(f"Stream error: {e}")
            raise
    
    headers = {
        'Content-Type': mime_type,
        'Accept-Ranges': 'bytes',
        'Content-Length': str(req_length),
        'Content-Disposition': f'inline; filename="{file_name}"'
    }
    
    if range_header:
        headers['Content-Range'] = f'bytes {from_bytes}-{until_bytes}/{file_size}'
        status_code = 206
    else:
        status_code = 200
    
    return StreamingResponse(file_stream(), status_code=status_code, headers=headers, media_type=mime_type)

@router.get("/watch/{fileId}")
async def watch_file(fileId: str):
    """Enhanced glassmorphism player with advanced features"""
    if not re.match(r'^[a-f0-9]{24}$', fileId):
        raise HTTPException(status_code=400, detail="Invalid file ID")
    
    file_data = await get_file_by_id(fileId)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_name = file_data.get('fileName', 'Video')
    stream_url = f"{config.BASE_APP_URL}/{fileId}"
    download_url = f"{config.BASE_APP_URL}/dl/{fileId}"
    quality = file_data.get('quality', '')
    language = file_data.get('language', '')
    size_mb = file_data.get('size', 0) / (1024 * 1024)
    duration = file_data.get('duration', 0)
    views = file_data.get('views', 0)
    is_mkv = file_name.lower().endswith('.mkv')
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{file_name}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/artplayer@5.1.1/dist/artplayer.css">
    <link rel="stylesheet" href="/static/player-theme.css">
</head>
<body>
    <div class="glass-container">
        <div class="player-header">
            <div class="title">{file_name}</div>
            <div class="meta-badges">
                {f'<span class="badge">🎥 {quality}</span>' if quality else ''}
                {f'<span class="badge">🗣️ {language}</span>' if language else ''}
                <span class="badge">💾 {size_mb:.1f}MB</span>
            </div>
        </div>
        <div class="player-wrapper"><div id="artplayer"></div></div>
        <div class="player-footer">
            <div class="action-buttons">
                <a href="{download_url}" class="glass-btn glass-btn-primary" download>⬇️ Download</a>
                <button onclick="copyLink()" class="glass-btn">🔗 Copy</button>
                <button onclick="share()" class="glass-btn">📤 Share</button>
            </div>
            <div class="stats">
                <span>👁️ {views} views</span>
                {f'<span>⏱️ {duration//60}m {duration%60}s</span>' if duration else ''}
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/artplayer@5.1.1/dist/artplayer.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <script>
        const art = new Artplayer({{
            container: '#artplayer',
            url: '{stream_url}',
            title: '{file_name}',
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
            loop: false,
            flip: true,
            theme: '#667eea',
            lang: navigator.language.toLowerCase(),
            moreVideoAttr: {{
                crossOrigin: 'anonymous',
                preload: 'metadata',
            }},
            {f"customType: {{ mkv: (video, url) => {{ if (Hls.isSupported()) {{ const hls = new Hls({{ enableWorker: true, lowLatencyMode: true, backBufferLength: 90 }}); hls.loadSource(url); hls.attachMedia(video); hls.on(Hls.Events.MANIFEST_PARSED, () => {{ console.log('HLS manifest loaded'); }}); if (hls.audioTracks && hls.audioTracks.length > 1) {{ window.hlsInstance = hls; }} }} else if (video.canPlayType('application/x-mpegURL')) {{ video.src = url; }} }} }}," if is_mkv else ''}
            settings: [
                {{
                    html: 'Playback Speed',
                    icon: '<i class="fas fa-gauge-high"></i>',
                    selector: [
                        {{ html: '0.25x', value: 0.25 }},
                        {{ html: '0.5x', value: 0.5 }},
                        {{ html: '0.75x', value: 0.75 }},
                        {{ html: 'Normal', value: 1, default: true }},
                        {{ html: '1.25x', value: 1.25 }},
                        {{ html: '1.5x', value: 1.5 }},
                        {{ html: '1.75x', value: 1.75 }},
                        {{ html: '2x', value: 2 }},
                    ],
                    onSelect: function (item) {{
                        art.playbackRate = item.value;
                        art.notice.show = 'Speed: ' + item.html;
                        return item.html;
                    }},
                }},
                {{
                    html: 'Aspect Ratio',
                    icon: '<i class="fas fa-expand"></i>',
                    selector: [
                        {{ html: 'Default', value: 'default', default: true }},
                        {{ html: '16:9', value: '16:9' }},
                        {{ html: '4:3', value: '4:3' }},
                        {{ html: '21:9', value: '21:9' }},
                        {{ html: '2.35:1', value: '2.35:1' }},
                    ],
                    onSelect: function (item) {{
                        art.aspectRatio = item.value;
                        art.notice.show = 'Aspect: ' + item.html;
                        return item.html;
                    }},
                }},
                {{
                    html: 'Loop Playback',
                    icon: '<i class="fas fa-repeat"></i>',
                    switch: false,
                    onSwitch: function (item) {{
                        art.loop = !art.loop;
                        item.tooltip = art.loop ? 'Loop: On' : 'Loop: Off';
                        art.notice.show = art.loop ? '<i class="fas fa-check"></i> Loop enabled' : '<i class="fas fa-times"></i> Loop disabled';
                        return !item.switch;
                    }},
                }},
            ],
            controls: [
                {{
                    position: 'left',
                    html: '<i class="fas fa-backward"></i>',
                    tooltip: 'Back 10s (J)',
                    style: {{ fontSize: '18px', padding: '0 10px' }},
                    click: function () {{
                        art.backward = 10;
                        art.notice.show = '<i class="fas fa-backward"></i> -10s';
                    }},
                }},
                {{
                    position: 'right',
                    html: '<i class="fas fa-forward"></i>',
                    tooltip: 'Forward 10s (L)',
                    style: {{ fontSize: '18px', padding: '0 10px' }},
                    click: function () {{
                        art.forward = 10;
                        art.notice.show = '<i class="fas fa-forward"></i> +10s';
                    }},
                }},
            ],
        }});
        
        // Add keyboard shortcuts
        art.on('ready', () => {{
            console.log('Player ready');
            
            // Custom keyboard controls
            document.addEventListener('keydown', (e) => {{
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
                
                if (e.key === 'l' || e.key === 'L') {{
                    art.forward = 10;
                    art.notice.show = '<i class="fas fa-forward"></i> +10s';
                    e.preventDefault();
                }}
                if (e.key === 'j' || e.key === 'J') {{
                    art.backward = 10;
                    art.notice.show = '<i class="fas fa-backward"></i> -10s';
                    e.preventDefault();
                }}
                if (e.key === 'k' || e.key === 'K') {{
                    art.toggle();
                    e.preventDefault();
                }}
            }});
            
            // Multi-audio track support for MKV via HLS
            {f'''if (window.hlsInstance && window.hlsInstance.audioTracks) {{
                const audioTracks = window.hlsInstance.audioTracks;
                if (audioTracks.length > 1) {{
                    const audioOptions = audioTracks.map((track, index) => ({{
                        html: track.name || `Track ${{index + 1}}` + (track.lang ? ` (${{track.lang.toUpperCase()}})` : ''),
                        value: index,
                        default: index === window.hlsInstance.audioTrack
                    }}));
                    
                    art.setting.add({{
                        html: 'Audio Track',
                        icon: '<i class="fas fa-music"></i>',
                        selector: audioOptions,
                        onSelect: function (item) {{
                            window.hlsInstance.audioTrack = item.value;
                            art.notice.show = '<i class="fas fa-music"></i> ' + item.html;
                            return item.html;
                        }},
                    }});
                    console.log('Multi-audio tracks available:', audioTracks.length);
                }}
            }}''' if is_mkv else ''}
            
            // Multi-quality/subtitle tracks support
            {f'''if (window.hlsInstance && window.hlsInstance.subtitleTracks) {{
                const subtitleTracks = window.hlsInstance.subtitleTracks;
                if (subtitleTracks.length > 0) {{
                    const subtitleOptions = [{{ html: 'Off', value: -1, default: true }}].concat(
                        subtitleTracks.map((track, index) => ({{
                            html: track.name || `Subtitle ${{index + 1}}` + (track.lang ? ` (${{track.lang.toUpperCase()}})` : ''),
                            value: index
                        }}))
                    );
                    
                    art.setting.add({{
                        html: 'Subtitles',
                        icon: '<i class="fas fa-closed-captioning"></i>',
                        selector: subtitleOptions,
                        onSelect: function (item) {{
                            window.hlsInstance.subtitleTrack = item.value;
                            art.notice.show = item.value === -1 ? '<i class="fas fa-times"></i> Subtitles Off' : '<i class="fas fa-closed-captioning"></i> ' + item.html;
                            return item.html;
                        }},
                    }});
                }}
            }}''' if is_mkv else ''}
        }});
        
        // Enhanced error handling
        art.on('error', (err) => {{
            console.error('Playback error:', err);
            art.notice.show = 'Playback error. Please try again.';
        }});
        
        // Save playback position
        art.on('video:timeupdate', () => {{
            if (art.duration - art.currentTime < 1) {{
                localStorage.removeItem('playback_' + '{fileId}');
            }} else {{
                localStorage.setItem('playback_' + '{fileId}', art.currentTime);
            }}
        }});
        
        // Resume from saved position
        art.on('ready', () => {{
            const savedTime = localStorage.getItem('playback_' + '{fileId}');
            if (savedTime && parseFloat(savedTime) > 10) {{
                art.currentTime = parseFloat(savedTime);
                art.notice.show = 'Resumed from ' + Math.floor(savedTime) + 's';
            }}
        }});
        
        function copyLink() {{
            navigator.clipboard.writeText(window.location.href);
            art.notice.show = 'Link copied to clipboard!';
        }}
        
        function share() {{
            if (navigator.share) {{
                navigator.share({{title: '{file_name}', url: window.location.href}});
            }} else {{
                copyLink();
            }}
        }}
    </script>
</body>
</html>"""
    
    return HTMLResponse(content=html)

@router.get("/embed/{fileId}")
async def embed_file(fileId: str):
    """Enhanced minimal fullscreen player for embedding"""
    if not re.match(r'^[a-f0-9]{24}$', fileId):
        raise HTTPException(status_code=400, detail="Invalid file ID")

    file_data = await get_file_by_id(fileId)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")

    file_name = file_data.get('fileName', 'Video')
    stream_url = f"{config.BASE_APP_URL}/{fileId}"
    is_mkv = file_name.lower().endswith('.mkv')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{file_name}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/artplayer@5.1.1/dist/artplayer.css">
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            background: #000;
            width: 100%;
            height: 100%;
            overflow: hidden;
        }}
        #artplayer {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
        }}
    </style>
</head>
<body>
    <div id="artplayer"></div>
    <script src="https://cdn.jsdelivr.net/npm/artplayer@5.1.1/dist/artplayer.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <script>
        const art = new Artplayer({{
            container: '#artplayer',
            url: '{stream_url}',
            title: '{file_name}',
            volume: 0.8,
            autoplay: true,
            pip: true,
            fullscreen: true,
            fullscreenWeb: true,
            setting: true,
            playbackRate: true,
            aspectRatio: true,
            hotkey: true,
            theme: '#667eea',
            mutex: true,
            loop: false,
            {f"customType: {{ mkv: (video, url) => {{ if (Hls.isSupported()) {{ const hls = new Hls({{ enableWorker: true, lowLatencyMode: true }}); hls.loadSource(url); hls.attachMedia(video); if (hls.audioTracks && hls.audioTracks.length > 1) {{ window.hlsInstance = hls; }} }} else if (video.canPlayType('application/x-mpegURL')) {{ video.src = url; }} }} }}," if is_mkv else ''}
            controls: [
                {{
                    position: 'left',
                    html: '⏪',
                    tooltip: 'Backward 10s',
                    click: function () {{
                        art.backward = 10;
                    }},
                }},
                {{
                    position: 'right',
                    html: '⏩',
                    tooltip: 'Forward 10s',
                    click: function () {{
                        art.forward = 10;
                    }},
                }},
            ],
        }});

        art.on('ready', () => {{
            console.log('Embed player ready');
            
            {f'''if (window.hlsInstance && window.hlsInstance.audioTracks && window.hlsInstance.audioTracks.length > 1) {{
                const audioOptions = window.hlsInstance.audioTracks.map((track, index) => ({{
                    html: track.name || `Audio ${{index + 1}}` + (track.lang ? ` (${{track.lang}})` : ''),
                    value: index,
                    default: index === window.hlsInstance.audioTrack
                }}));
                
                art.setting.add({{
                    html: 'Audio Track',
                    selector: audioOptions,
                    onSelect: function (item) {{
                        window.hlsInstance.audioTrack = item.value;
                        return item.html;
                    }},
                }});
            }}''' if is_mkv else ''}
        }});
    </script>
</body>
</html>"""
    
    return HTMLResponse(content=html)

async def get_media_session(client, file_id: FileId):
    """Get/create media session for DC"""
    dc_id = file_id.dc_id
    if not hasattr(client, 'media_sessions'):
        client.media_sessions = {}
    if dc_id in client.media_sessions:
        return client.media_sessions[dc_id]
    
    if dc_id != await client.storage.dc_id():
        media_session = Session(client, dc_id, await Auth(client, dc_id, await client.storage.test_mode()).create(), await client.storage.test_mode(), is_media=True)
        await media_session.start()
        for _ in range(6):
            try:
                exported = await client.invoke(raw.functions.auth.ExportAuthorization(dc_id=dc_id))
                await media_session.invoke(raw.functions.auth.ImportAuthorization(id=exported.id, bytes=exported.bytes))
                break
            except:
                continue
        client.media_sessions[dc_id] = media_session
        return media_session
    else:
        media_session = Session(client, dc_id, await client.storage.auth_key(), await client.storage.test_mode(), is_media=True)
        await media_session.start()
        client.media_sessions[dc_id] = media_session
        return media_session

async def get_location(file_id: FileId):
    """Get file location"""
    if file_id.file_type == FileType.PHOTO:
        return raw.types.InputPhotoFileLocation(id=file_id.media_id, access_hash=file_id.access_hash, file_reference=file_id.file_reference, thumb_size=file_id.thumbnail_size)
    return raw.types.InputDocumentFileLocation(id=file_id.media_id, access_hash=file_id.access_hash, file_reference=file_id.file_reference, thumb_size=file_id.thumbnail_size)