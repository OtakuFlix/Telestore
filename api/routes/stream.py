from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from database.operations import get_file_by_id, increment_views, get_files_by_basename
from bot.client import get_bot
from config import config
from pyrogram import raw
from pyrogram.file_id import FileId, FileType, ThumbnailSource
from pyrogram.session import Session, Auth
from pyrogram import utils as pyro_utils
import re
import math

router = APIRouter()

def get_artplayer_config_with_quality(file_id: str, stream_url: str, file_name: str, is_mkv: bool, download_url: str = None, current_quality: str = "Unknown"):
    controls_config = """[
        {
            position: 'left',
            html: '<i class="fas fa-backward"></i>',
            tooltip: 'Back 10s (J)',
            style: { fontSize: '18px', padding: '0 10px' },
            click: function () {
                art.backward = 10;
                art.notice.show = '<i class="fas fa-backward"></i> -10s';
            },
        },
        {
            position: 'left',
            html: '<i class="fas fa-forward"></i>',
            tooltip: 'Forward 10s (L)',
            style: { fontSize: '18px', padding: '0 10px' },
            click: function () {
                art.forward = 10;
                art.notice.show = '<i class="fas fa-forward"></i> +10s';
            },
        },"""
    
    if download_url:
        controls_config += f"""
        {{
            position: 'right',
            html: '<i class="fas fa-download"></i>',
            tooltip: 'Download Video',
            style: {{ fontSize: '18px', padding: '0 10px' }},
            click: function () {{
                window.open('{download_url}', '_blank');
                art.notice.show = '<i class="fas fa-download"></i> Starting download...';
            }},
        }},"""
    
    controls_config += "\n    ]"
    
    mkv_custom_type = ""
    if is_mkv:
        mkv_custom_type = """customType: {
            mkv: (video, url) => {
                if (Hls.isSupported()) {
                    const hls = new Hls({ enableWorker: true, lowLatencyMode: true, backBufferLength: 90 });
                    hls.loadSource(url);
                    hls.attachMedia(video);
                    hls.on(Hls.Events.MANIFEST_PARSED, () => { console.log('HLS manifest loaded'); });
                    if (hls.audioTracks && hls.audioTracks.length > 1) { window.hlsInstance = hls; }
                } else if (video.canPlayType('application/x-mpegURL')) {
                    video.src = url;
                }
            }
        },"""
    
    return f"""
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
            aspectRatio: false,
            screenshot: true,
            hotkey: true,
            mutex: true,
            loop: false,
            flip: true,
            theme: '#dc2626',
            lang: navigator.language.toLowerCase(),
            fastForward: true,
            moreVideoAttr: {{
                crossOrigin: 'anonymous',
                preload: 'metadata',
            }},
            {mkv_custom_type}
            settings: [],
            controls: {controls_config},
        }});

        async function fetchQualityOptions() {{
            try {{
                const response = await fetch('/api/quality_info/{file_id}');
                const data = await response.json();
                return data.qualities || [];
            }} catch (error) {{
                console.error('Failed to fetch quality options:', error);
                return [];
            }}
        }}

        fetchQualityOptions().then(qualities => {{
            if (qualities.length > 1) {{
                const qualityOptions = qualities.map(q => {{
                    const sizeMB = (q.size / (1024 * 1024)).toFixed(1);
                    return {{
                        html: `${{q.quality}} (${{sizeMB}}MB)`,
                        value: q.fileId,
                        url: `{config.BASE_APP_URL}/${{q.fileId}}`,
                        quality: q.quality,
                        default: q.quality === '{current_quality}'
                    }};
                }});

                art.setting.add({{
                    html: 'Quality',
                    icon: '<i class="fas fa-sliders"></i>',
                    selector: qualityOptions,
                    onSelect: function (item) {{
                        const currentTime = art.currentTime;
                        const wasPlaying = !art.paused;
                        
                        art.switchUrl(item.url);
                        
                        art.once('video:canplay', () => {{
                            art.currentTime = currentTime;
                            if (wasPlaying) {{
                                art.play();
                            }}
                        }});
                        
                        art.notice.show = `<i class="fas fa-sliders"></i> Switched to ${{item.quality}}`;
                        
                        window.history.replaceState(null, '', `/watch/${{item.value}}`);
                        
                        return item.html;
                    }},
                }});
            }}

            art.setting.add({{
                html: 'Multi Audio',
                icon: '<i class="fas fa-headphones"></i>',
                switch: false,
                onSwitch: function(item) {{
                    const streamUrl = '{download_url}';
                    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

                    if (isMobile) {{
                        alert('You are being redirected to VLC Player on your mobile device.\\n\\nOnce VLC opens, you can adjust audio tracks and subtitles directly in the app.');
                        window.location.href = 'vlc://' + streamUrl;
                    }} else {{
                        alert('VLC Player is available for desktop, but your browser cannot open it directly.\\n\\nPlease follow these steps:\\n\\n1. Copy the link below:\\n' + streamUrl + '\\n\\n2. Open VLC → Media → Open Network Stream.\\n3. Paste the URL and click Play.\\n\\nYou can now switch audio and subtitle tracks in VLC.');
                        window.open(streamUrl, '_blank');
                    }}

                    return !item.switch;
                }}
            }});

            art.setting.add({{
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
                    art.notice.show = '<i class="fas fa-gauge-high"></i> Speed: ' + item.html;
                    return item.html;
                }},
            }});

            art.setting.add({{
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
                    art.notice.show = '<i class="fas fa-expand"></i> Aspect: ' + item.html;
                    return item.html;
                }},
            }});

            art.setting.add({{
                html: 'Loop Playback',
                icon: '<i class="fas fa-repeat"></i>',
                switch: false,
                onSwitch: function (item) {{
                    art.loop = !art.loop;
                    item.tooltip = art.loop ? 'Loop: On' : 'Loop: Off';
                    art.notice.show = art.loop ? '<i class="fas fa-check"></i> Loop enabled' : '<i class="fas fa-times"></i> Loop disabled';
                    return !item.switch;
                }},
            }});
        }});
    """

def get_tap_functionality_script():
    return """
        art.on('ready', () => {
            art.template.$video.style.pointerEvents = 'none';
        });
        
        let tapCount = 0;
        let tapTimer = null;
        let lastTapTime = 0;
        
        const videoContainer = document.querySelector('.player-wrapper');
        
        const createSeekIndicator = (direction, x, y) => {
            const indicator = document.createElement('div');
            indicator.className = 'seek-indicator';
            indicator.innerHTML = direction === 'forward' 
                ? '<i class="fas fa-forward"></i><span>+10s</span>' 
                : '<i class="fas fa-backward"></i><span>-10s</span>';
            indicator.style.left = x + 'px';
            indicator.style.top = y + 'px';
            videoContainer.appendChild(indicator);
            
            setTimeout(() => indicator.remove(), 800);
        };
        
        const createFullscreenIndicator = (x, y) => {
            const indicator = document.createElement('div');
            indicator.className = 'seek-indicator';
            indicator.innerHTML = '<i class="fas fa-expand"></i><span>Fullscreen</span>';
            indicator.style.left = x + 'px';
            indicator.style.top = y + 'px';
            videoContainer.appendChild(indicator);
            
            setTimeout(() => indicator.remove(), 800);
        };
        
        videoContainer.addEventListener('click', (e) => {
            if (e.target.closest('.art-controls') || e.target.closest('.art-layers') || 
                e.target.closest('.art-control') || e.target.closest('.art-icon') || 
                e.target.closest('button')) return;
            
            e.preventDefault();
            e.stopPropagation();
            
            const currentTime = Date.now();
            if (currentTime - lastTapTime > 500) tapCount = 0;
            
            tapCount++;
            lastTapTime = currentTime;
            clearTimeout(tapTimer);
            
            tapTimer = setTimeout(() => {
                const rect = videoContainer.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                const screenWidth = rect.width;
                
                if (tapCount === 1) {
                    art.toggle();
                } else if (tapCount === 2) {
                    if (x < screenWidth / 2) {
                        art.backward = 10;
                        art.notice.show = '<i class="fas fa-backward"></i> -10s';
                        createSeekIndicator('backward', x, y);
                    } else {
                        art.forward = 10;
                        art.notice.show = '<i class="fas fa-forward"></i> +10s';
                        createSeekIndicator('forward', x, y);
                    }
                } else if (tapCount >= 3) {
                    art.fullscreen = !art.fullscreen;
                    createFullscreenIndicator(x, y);
                }
                
                tapCount = 0;
            }, 350);
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            
            if (e.key === 'l' || e.key === 'L') {
                art.forward = 10;
                art.notice.show = '<i class="fas fa-forward"></i> +10s';
                e.preventDefault();
            }
            if (e.key === 'j' || e.key === 'J') {
                art.backward = 10;
                art.notice.show = '<i class="fas fa-backward"></i> -10s';
                e.preventDefault();
            }
            if (e.key === 'k' || e.key === 'K') {
                art.toggle();
                e.preventDefault();
            }
            if (e.key === 'f' || e.key === 'F') {
                art.fullscreen = !art.fullscreen;
                e.preventDefault();
            }
        });
    """

@router.get("/{fileId}")
async def stream_file(fileId: str, request: Request):
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
    if not re.match(r'^[a-f0-9]{24}$', fileId):
        raise HTTPException(status_code=400, detail="Invalid file ID")
    
    file_data = await get_file_by_id(fileId)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_name = file_data.get('fileName', 'Video')
    base_name = file_data.get('baseName', file_name)
    stream_url = f"{config.BASE_APP_URL}/{fileId}"
    download_url = f"{config.BASE_APP_URL}/dl/{fileId}"
    quality = file_data.get('quality', 'Unknown')
    language = file_data.get('language', '')
    size_mb = file_data.get('size', 0) / (1024 * 1024)
    duration = file_data.get('duration', 0)
    views = file_data.get('views', 0)
    is_mkv = file_name.lower().endswith('.mkv')
    
    artplayer_config = get_artplayer_config_with_quality(fileId, stream_url, file_name, is_mkv, download_url, quality)
    tap_script = get_tap_functionality_script()
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{file_name}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/artplayer@5.1.1/dist/artplayer.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="/static/player-theme.css">
</head>
<body>
    <div class="top-header">
        <div class="logo">
            <i class="fas fa-play-circle"></i>
            <span>TeleStore</span>
        </div>
        <div class="header-actions">
            <button class="theme-toggle" onclick="toggleTheme()" title="Toggle Theme">
                <i class="fas fa-moon"></i>
            </button>
        </div>
    </div>

    <div class="glass-container">
        <div class="player-header">
            <div class="title">{base_name}</div>
            <div class="meta-badges">
                {f'<span class="badge"><i class="fas fa-video"></i> {quality}</span>' if quality else ''}
                {f'<span class="badge"><i class="fas fa-language"></i> {language}</span>' if language else ''}
                <span class="badge"><i class="fas fa-hdd"></i> {size_mb:.1f}MB</span>
            </div>
        </div>
        
        <div class="player-wrapper">
            <div id="artplayer"></div>
        </div>
        
        <div class="player-footer">
            <div class="action-buttons">
                <a href="{download_url}" class="glass-btn glass-btn-primary" download>
                    <i class="fas fa-download"></i> Download
                </a>
                <button onclick="copyLink()" class="glass-btn">
                    <i class="fas fa-link"></i> Copy Link
                </button>
                <button onclick="share()" class="glass-btn">
                    <i class="fas fa-share-alt"></i> Share
                </button>
            </div>
            <div class="stats">
                <span><i class="fas fa-eye"></i> {views} views</span>
                {f'<span><i class="fas fa-clock"></i> {duration//60}m {duration%60}s</span>' if duration else ''}
            </div>
        </div>

        <div class="external-players">
            <h3><i class="fas fa-mobile-screen"></i> Play in External Apps</h3>
            <div class="player-grid">
                <a href="vlc://{stream_url}" class="player-card">
                    <i class="fas fa-play"></i>
                    <span>VLC Player</span>
                </a>
                <a href="intent:{stream_url}#Intent;package=com.mxtech.videoplayer.ad;S.title={file_name};end" class="player-card">
                    <i class="fas fa-film"></i>
                    <span>MX Player</span>
                </a>
                <a href="intent:{stream_url}#Intent;package=com.mxtech.videoplayer.pro;S.title={file_name};end" class="player-card">
                    <i class="fas fa-star"></i>
                    <span>MX Player Pro</span>
                </a>
                <a href="intent:{stream_url}#Intent;type=video/*;package=is.xyz.mpv;end" class="player-card">
                    <i class="fas fa-video"></i>
                    <span>mpv</span>
                </a>
                <a href="splayer://play?url={stream_url}&title={file_name}" class="player-card">
                    <i class="fas fa-circle-play"></i>
                    <span>SPlayer</span>
                </a>
                <a href="intent:{stream_url}#Intent;type=video/*;package=com.bsplayer.bspandroid.free;S.title={file_name};end" class="player-card">
                    <i class="fas fa-square-play"></i>
                    <span>BSPlayer</span>
                </a>
                <a href="nplayer-{stream_url}" class="player-card">
                    <i class="fas fa-n"></i>
                    <span>nPlayer</span>
                </a>
                <a href="kmplayer://play?url={stream_url}&title={file_name}" class="player-card">
                    <i class="fas fa-k"></i>
                    <span>KMPlayer</span>
                </a>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/artplayer@5.1.1/dist/artplayer.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <script>
        function toggleTheme() {{
            const body = document.body;
            const icon = document.querySelector('.theme-toggle i');
            
            if (body.getAttribute('data-theme') === 'light') {{
                body.removeAttribute('data-theme');
                icon.classList.replace('fa-sun', 'fa-moon');
                localStorage.setItem('theme', 'dark');
            }} else {{
                body.setAttribute('data-theme', 'light');
                icon.classList.replace('fa-moon', 'fa-sun');
                localStorage.setItem('theme', 'light');
            }}
        }}

        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'light') {{
            document.body.setAttribute('data-theme', 'light');
            document.querySelector('.theme-toggle i').classList.replace('fa-moon', 'fa-sun');
        }}

        {artplayer_config}
        {tap_script}
        
        art.on('ready', () => {{
            console.log('Player ready');
            
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
                }}
            }}''' if is_mkv else ''}
        }});
        
        art.on('error', (err) => {{
            console.error('Playback error:', err);
            art.notice.show = '<i class="fas fa-exclamation-triangle"></i> Playback error';
        }});
        
        art.on('video:timeupdate', () => {{
            if (art.duration - art.currentTime < 1) {{
                localStorage.removeItem('playback_{fileId}');
            }} else {{
                localStorage.setItem('playback_{fileId}', art.currentTime);
            }}
        }});
        
        art.on('ready', () => {{
            const savedTime = localStorage.getItem('playback_{fileId}');
            if (savedTime && parseFloat(savedTime) > 10) {{
                art.currentTime = parseFloat(savedTime);
                art.notice.show = '<i class="fas fa-play"></i> Resumed from ' + Math.floor(savedTime) + 's';
            }}
        }});
        
        function copyLink() {{
            navigator.clipboard.writeText(window.location.href);
            art.notice.show = '<i class="fas fa-check"></i> Link copied!';
        }}
        
        function share() {{
            if (navigator.share) {{
                navigator.share({{title: '{file_name}', url: window.location.href}}).catch(() => copyLink());
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
    if not re.match(r'^[a-f0-9]{24}$', fileId):
        raise HTTPException(status_code=400, detail="Invalid file ID")

    file_data = await get_file_by_id(fileId)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")

    file_name = file_data.get('fileName', 'Video')
    stream_url = f"{config.BASE_APP_URL}/{fileId}"
    download_url = f"{config.BASE_APP_URL}/dl/{fileId}"
    quality = file_data.get('quality', 'Unknown')
    is_mkv = file_name.lower().endswith('.mkv')

    artplayer_config = get_artplayer_config_with_quality(fileId, stream_url, file_name, is_mkv, download_url, quality)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{file_name}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/artplayer@5.1.1/dist/artplayer.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
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
        {artplayer_config}
        
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
                    icon: '<i class="fas fa-music"></i>',
                    selector: audioOptions,
                    onSelect: function (item) {{
                        window.hlsInstance.audioTrack = item.value;
                        art.notice.show = '<i class="fas fa-music"></i> ' + item.html;
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
    if file_id.file_type == FileType.PHOTO:
        return raw.types.InputPhotoFileLocation(id=file_id.media_id, access_hash=file_id.access_hash, file_reference=file_id.file_reference, thumb_size=file_id.thumbnail_size)
    return raw.types.InputDocumentFileLocation(id=file_id.media_id, access_hash=file_id.access_hash, file_reference=file_id.file_reference, thumb_size=file_id.thumbnail_size)