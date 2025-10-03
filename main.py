# ==================== main.py ====================
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pyrogram import Client, filters, idle
from database.connection import connect_db, disconnect_db
from config import config

# Global bot variable
bot = None
idle_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage bot, database and API lifecycle"""
    global bot, idle_task
    
    print(f"[STARTUP] Initializing TeleStore Bot...")
    
    # Connect to database
    await connect_db()
    
    # Create bot client INSIDE async context (like your working test!)
    bot = Client(
        name="telestore_bot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN,
        workdir=".",
    )
    print(f"[STARTUP] Bot client created")
    
    # Register handlers (do this BEFORE start, like your test)
    register_handlers(bot)
    print(f"[STARTUP] Handlers registered")
    
    # Start bot
    await bot.start()
    me = await bot.get_me()
    print(f"[STARTUP] Bot started: @{me.username}")
    print(f"[STARTUP] API server running on port {config.PORT}")
    print(f"[STARTUP] Base URL: {config.BASE_APP_URL}")
    
    # Run idle in background to keep bot polling (like your test does await idle())
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

def register_handlers(client):
    """Register all bot handlers"""
    from pyrogram.types import Message
    from bot.keyboards import main_menu_kb
    from database.operations import get_stats, create_folder
    import secrets
    import string
    
    @client.on_message(filters.command(["start", "menu"]) & filters.private)
    async def start_command(c, message: Message):
        print(f"[BOT] ✅ Received /start from {message.from_user.id}")
        user = message.from_user
        await message.reply_text(
            f"👋 Welcome {user.first_name}!\n\n"
            f"🎬 **TeleStore Bot** - Your personal cloud storage for videos.\n\n"
            f"📁 Organize files in folders\n"
            f"🔗 Get instant streaming links\n"
            f"⬇️ Direct download support\n"
            f"🌐 Embed videos anywhere\n\n"
            f"Use the menu below to get started:",
            reply_markup=main_menu_kb()
        )
        print(f"[BOT] ✅ Sent reply")
    
    @client.on_message(filters.command("help") & filters.private)
    async def help_command(c, message: Message):
        help_text = """
📖 **How to use TeleStore Bot:**

**Creating Folders:**
• Use /newfolder <n> to create a folder
• Or click "New Folder" in the menu

**Adding Files:**
1. Open any folder
2. Click "Add Files"
3. Send me any video/document

**Getting Links:**
• Click on any file to get Watch & Download links

**Supported Formats:**
MP4, MKV, AVI, MOV, WMV, FLV, and more!
        """
        await message.reply_text(help_text, reply_markup=main_menu_kb())
    
    @client.on_message(filters.command("newfolder") & filters.private)
    async def newfolder_command(c, message: Message):
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply_text("❌ Please provide a folder name.\n\n**Usage:** `/newfolder My Movies`")
            return
        
        folder_name = parts[1].strip()
        folder_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        await create_folder(folder_id=folder_id, name=folder_name, created_by=message.from_user.id)
        
        await message.reply_text(
            f"✅ Folder created!\n\n📁 **Name:** {folder_name}\n🆔 **ID:** `{folder_id}`",
            reply_markup=main_menu_kb()
        )
    
    @client.on_message(filters.command("stats") & filters.private)
    async def stats_command(c, message: Message):
        stats = await get_stats(message.from_user.id)
        await message.reply_text(
            f"📊 **Your Statistics:**\n\n"
            f"📁 Folders: {stats['folders']}\n"
            f"🎬 Files: {stats['files']}\n"
            f"💾 Storage: {stats['total_size_mb']:.2f} MB",
            reply_markup=main_menu_kb()
        )
    
    # Import and register other handlers
    from bot.handlers import callbacks, media
    
    print(f"[HANDLERS] All handlers registered")

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