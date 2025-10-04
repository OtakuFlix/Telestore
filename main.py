# ==================== main.py ====================
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pyrogram import Client, idle
from bot.client import set_bot
from database.connection import connect_db, disconnect_db
from config import config

# Global bot variable
bot = None
idle_task = None

# ---------------------- LIFESPAN ----------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage bot, database, and API lifecycle"""
    global bot, idle_task

    print("[STARTUP] Initializing TeleStore Bot...")
    
    # Connect to database
    await connect_db()
    print("[DATABASE] Connected successfully")
    
    # Create bot client
    bot = Client(
        name="telestore_bot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN,
        workdir="."
    )
    set_bot(bot)
    print("[STARTUP] Bot client created")
    
    # Register all handlers
    register_handlers(bot)
    print("[STARTUP] Handlers registered")
    
    # Start bot
    await bot.start()
    me = await bot.get_me()
    print(f"[STARTUP] Bot started: @{me.username}")
    print(f"[STARTUP] API server running on port {config.PORT}")
    print(f"[STARTUP] Base URL: {config.BASE_APP_URL}")
    
    # Run idle in background to keep bot polling
    idle_task = asyncio.create_task(idle())
    print("[STARTUP] Bot is now listening for messages...")

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

# ---------------------- HANDLER REGISTRATION ----------------------
def register_handlers(bot_instance):
    """Register all modular bot handlers"""
    from bot.handlers import commands, media, callbacks

    # Register command handlers
    commands.register_command_handlers(bot_instance)
    
    # Register media handlers
    media.register_media_handlers(bot_instance)
    
    # Register callback handlers
    callbacks.register_callback_handlers(bot_instance)

    print("[HANDLERS] All handlers successfully registered")

# ---------------------- FASTAPI APP ----------------------
app = FastAPI(
    title="TeleStore API",
    description="Stream and download files from Telegram",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
from api.routes import stream, download
app.include_router(stream.router)
app.include_router(download.router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "TeleStore API",
        "version": "1.0.0",
        "endpoints": {
            "stream": "/{fileId}",
            "watch": "/watch/{fileId}",
            "download": "/dl/{fileId}",
            "health": "/health"
        }
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ---------------------- ENTRY POINT ----------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.PORT, log_level="info")
