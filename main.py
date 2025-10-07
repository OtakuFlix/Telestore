# ==================== main.py ====================
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pyrogram import Client, idle
from database.connection import connect_db, disconnect_db
from config import config
from bot.client import set_bot

# Global variables
bot = None
idle_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage bot, database and API lifecycle"""
    global bot, idle_task
    
    print(f"[STARTUP] Initializing TeleStore Bot...")
    
    # Connect to database
    await connect_db()
    
    # Create bot client
    bot = Client(
        name="telestore_bot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN,
        workdir=".",
        sleep_threshold=60,
    )
    print(f"[STARTUP] Bot client created")
    
    # Set bot globally
    set_bot(bot)
    
    # Register handlers
    register_all_handlers(bot)
    print(f"[STARTUP] Handlers registered")
    
    # Start bot
    await bot.start()
    me = await bot.get_me()
    print(f"[STARTUP] Bot started: @{me.username}")
    print(f"[STARTUP] API server running on port {config.PORT}")
    print(f"[STARTUP] Base URL: {config.BASE_APP_URL}")
    print(f"[STARTUP] Channel ID: {config.CHANNEL_ID}")
    
    # Run idle in background to keep bot polling
    idle_task = asyncio.create_task(idle())
    print(f"[STARTUP] Bot is now listening for messages...")
    
    yield
    
    # Cleanup
    print("[SHUTDOWN] Stopping services...")
    if idle_task:
        idle_task.cancel()
        try:
            await idle_task
        except asyncio.CancelledError:
            pass
    await bot.stop()
    await disconnect_db()
    print("[SHUTDOWN] Shutdown complete")

def register_all_handlers(client):
    """Register all bot handlers"""
    # Import handler registration functions
    from bot.handlers.commands import register_command_handlers
    from bot.handlers.callbacks import register_callback_handlers
    from bot.handlers.media import register_media_handlers
    
    # Register all handlers
    register_command_handlers(client)
    register_callback_handlers(client)
    register_media_handlers(client)
    
    print(f"[HANDLERS] All handlers registered successfully")

# Create FastAPI app
app = FastAPI(
    title="TeleStore API",
    description="Stream and download files from Telegram",
    version="2.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="api/static"), name="static")   # <-- add this here

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
from api.routes import stream, download
app.include_router(stream.router)
app.include_router(download.router)

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "TeleStore API",
        "version": "2.0.0",
        "status": "running",
        "bot_connected": bot.is_connected if bot else False,
        "endpoints": {
            "stream": "/{fileId} - Direct video stream with range support",
            "watch": "/watch/{fileId} - Beautiful embedded video player",
            "download": "/dl/{fileId} - Direct file download",
            "health": "/health - Health check endpoint"
        },
        "features": [
            "Video streaming with seeking",
            "ArtPlayer integration",
            "Auto channel backup",
            "Metadata extraction",
            "Quality detection",
            "Language detection"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "bot": "connected" if bot and bot.is_connected else "disconnected",
        "database": "connected",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=config.PORT, 
        log_level="info",
        access_log=True
    )