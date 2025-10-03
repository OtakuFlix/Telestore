# ==================== main.py ====================
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pyrogram import idle
from database.connection import connect_db, disconnect_db
from config import config

# Import bot client
from bot.client import bot

# Global variables
idle_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage bot, database and API lifecycle"""
    global idle_task
    
    print(f"[STARTUP] Initializing TeleStore Bot...")
    
    # Connect to database
    await connect_db()
    
    # Import handlers to register them (this must happen BEFORE bot.start())
    print(f"[STARTUP] Registering handlers...")
    from bot.handlers import commands, callbacks, media
    print(f"[STARTUP] Handlers registered")
    
    # Start bot
    await bot.start()
    me = await bot.get_me()
    print(f"[STARTUP] Bot started: @{me.username}")
    print(f"[STARTUP] API server running on port {config.PORT}")
    print(f"[STARTUP] Base URL: {config.BASE_APP_URL}")
    
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

# Create FastAPI app
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

# Include routes
from api.routes import stream, download
app.include_router(stream.router)
app.include_router(download.router)

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

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.PORT, log_level="info")