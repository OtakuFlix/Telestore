# ==================== main_threaded.py ====================
# Run bot in separate thread with its own event loop
import asyncio
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pyrogram import Client, filters, idle
from database.connection import connect_db, disconnect_db
from config import config

# Global variables
bot_thread = None
bot_stop_event = None

def run_bot_thread():
    """Run bot in separate thread with its own event loop"""
    # Create new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def bot_main():
        print("[BOT THREAD] Starting bot...")
        
        # Create bot client
        bot = Client(
            name="telestore_bot",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            workdir=".",
        )
        
        # Register handlers
        from bot.handlers import commands, callbacks, media
        print("[BOT THREAD] Handlers registered")
        
        # Start bot
        await bot.start()
        me = await bot.get_me()
        print(f"[BOT THREAD] Bot started: @{me.username}")
        print(f"[BOT THREAD] Listening for messages...")
        
        # Keep bot alive (like your working test)
        await idle()
        
        # Stop bot
        await bot.stop()
        print("[BOT THREAD] Bot stopped")
    
    # Run bot
    loop.run_until_complete(bot_main())
    loop.close()

# Create FastAPI app
app = FastAPI(
    title="TeleStore API",
    description="Stream and download files from Telegram",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Start bot and database on startup"""
    global bot_thread
    
    print("[STARTUP] Initializing services...")
    
    # Connect to database
    await connect_db()
    
    # Start bot in separate thread
    bot_thread = threading.Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()
    
    print(f"[STARTUP] API server running on port {config.PORT}")
    print(f"[STARTUP] Base URL: {config.BASE_APP_URL}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("[SHUTDOWN] Stopping services...")
    await disconnect_db()
    print("[SHUTDOWN] Shutdown complete")

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