# ==================== main.py ====================
import asyncio
from contextlib import asynccontextmanager
from api.app import app
from bot.client import bot
from database.connection import connect_db, disconnect_db
from config import config

@asynccontextmanager
async def lifespan(application):
    """Manage bot, database and API lifecycle"""
    print(f"[STARTUP] Initializing TeleStore Bot...")
    
    # Connect to database
    await connect_db()
    
    # Start Telegram bot
    await bot.start()
    print(f"[STARTUP] Bot started: @{(await bot.get_me()).username}")
    print(f"[STARTUP] API server running on port {config.PORT}")
    print(f"[STARTUP] Base URL: {config.BASE_APP_URL}")
    
    yield
    
    # Cleanup
    print("[SHUTDOWN] Stopping services...")
    await bot.stop()
    await disconnect_db()
    print("[SHUTDOWN] Shutdown complete")

app.router.lifespan_context = lifespan

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.PORT,
        log_level="info"
    )