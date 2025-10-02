# ==================== main.py ====================
import asyncio
from contextlib import asynccontextmanager
from api.app import app
from bot.client import bot
from config import config

@asynccontextmanager
async def lifespan(application):
    """Manage bot and API lifecycle"""
    print(f"[STARTUP] Starting Telegram bot and API server on port {config.PORT}...")
    await bot.start()
    print(f"[STARTUP] Bot started successfully: @{(await bot.get_me()).username}")
    
    yield
    
    print("[SHUTDOWN] Stopping bot...")
    await bot.stop()
    print("[SHUTDOWN] Bot stopped")

app.router.lifespan_context = lifespan

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.PORT,
        log_level="info"
    )
