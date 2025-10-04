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
    
    # Create bot client INSIDE async context
    bot = Client(
        name="telestore_bot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN,
        workdir=".",
    )
    print(f"[STARTUP] Bot client created")
    
    # Register handlers (do this BEFORE start)
    register_handlers(bot)
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

def register_handlers(client):
    """Register all bot handlers"""
    from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
    from bot.keyboards import (
        main_menu_kb, folders_kb, folder_view_kb, 
        file_actions_kb, confirm_delete_kb
    )
    from database.operations import (
        get_stats, create_folder, get_user_folders, get_folder_files, 
        get_file_by_id, delete_file, delete_folder, get_folder_by_id,
        count_user_folders, count_folder_files
    )
    import secrets
    import string
    import math
    
    PAGE_SIZE = 8
    
    # ==================== COMMAND HANDLERS ====================
    
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
• Use /newfolder <name> to create a folder
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
            f"💾 Storage: {stats['total_size_mb']:.2f} MB\n"
            f"🔗 Total Views: {stats.get('views', 0)}\n"
            f"⬇️ Total Downloads: {stats.get('downloads', 0)}",
            reply_markup=main_menu_kb()
        )
    
    @client.on_message(filters.command("myfolders") & filters.private)
    async def myfolders_command(c, message: Message):
        await show_folders_page(message, page=1, edit=False)
    
    # ==================== CALLBACK HANDLERS ====================
    
    @client.on_callback_query(filters.regex("^main_menu$"))
    async def main_menu_callback(c, callback: CallbackQuery):
        print(f"[BOT] ✅ Received main_menu callback from {callback.from_user.id}")
        await callback.message.edit_text(
            "🏠 **Main Menu**\n\n"
            "Choose an option below:",
            reply_markup=main_menu_kb()
        )
        await callback.answer()
    
    @client.on_callback_query(filters.regex(r"^folders:(\d+)$"))
    async def folders_callback(c, callback: CallbackQuery):
        print(f"[BOT] ✅ Received folders callback from {callback.from_user.id}")
        page = int(callback.data.split(":")[1])
        await show_folders_page(callback.message, page, edit=True)
        await callback.answer()
    
    @client.on_callback_query(filters.regex(r"^folder:([^:]+):(\d+)$"))
    async def folder_view_callback(c, callback: CallbackQuery):
        print(f"[BOT] ✅ Received folder view callback from {callback.from_user.id}")
        parts = callback.data.split(":")
        folder_id = parts[1]
        page = int(parts[2])
        
        await show_folder_contents(callback.message, folder_id, page, edit=True)
        await callback.answer()
    
    @client.on_callback_query(filters.regex("^file:([^:]+)$"))
    async def file_view_callback(c, callback: CallbackQuery):
        print(f"[BOT] ✅ Received file view callback from {callback.from_user.id}")
        file_id = callback.data.split(":")[1]
        
        file_data = await get_file_by_id(file_id)
        if not file_data:
            await callback.answer("❌ File not found!", show_alert=True)
            return
        
        # Build file info
        info = f"🎬 **{file_data.get('fileName', 'Unnamed')}**\n\n"
        
        if file_data.get('size'):
            size_mb = file_data['size'] / (1024 * 1024)
            info += f"💾 Size: {size_mb:.2f} MB\n"
        
        if file_data.get('mimeType'):
            info += f"📄 Type: {file_data['mimeType']}\n"
        
        if file_data.get('quality'):
            info += f"🎥 Quality: {file_data['quality']}\n"
        
        if file_data.get('language'):
            info += f"🗣 Language: {file_data['language']}\n"
        
        if file_data.get('caption'):
            info += f"\n📝 {file_data['caption']}\n"
        
        info += f"\n🔗 **Links:**"
        info += f"\n▶️ Watch: {config.BASE_APP_URL}/{file_id}"
        info += f"\n⬇️ Download: {config.BASE_APP_URL}/dl/{file_id}"
        
        await callback.message.edit_text(
            info,
            reply_markup=file_actions_kb(file_id, file_data['folderId'])
        )
        await callback.answer()
    
    @client.on_callback_query(filters.regex("^delete_file:([^:]+):([^:]+)$"))
    async def delete_file_confirm_callback(c, callback: CallbackQuery):
        print(f"[BOT] ✅ Received delete file confirm callback")
        parts = callback.data.split(":")
        file_id = parts[1]
        folder_id = parts[2]
        
        await callback.message.edit_text(
            "⚠️ **Delete File?**\n\n"
            "Are you sure you want to delete this file?\n"
            "This action cannot be undone.",
            reply_markup=confirm_delete_kb("file", file_id, folder_id)
        )
        await callback.answer()
    
    @client.on_callback_query(filters.regex("^confirm_delete_file:([^:]+):([^:]+)$"))
    async def confirm_delete_file_callback(c, callback: CallbackQuery):
        print(f"[BOT] ✅ Received confirm delete file callback")
        parts = callback.data.split(":")
        file_id = parts[1]
        folder_id = parts[2]
        
        success = await delete_file(file_id)
        
        if success:
            await callback.answer("✅ File deleted successfully!", show_alert=True)
            await show_folder_contents(callback.message, folder_id, 1, edit=True)
        else:
            await callback.answer("❌ Failed to delete file!", show_alert=True)
    
    @client.on_callback_query(filters.regex("^delete_folder:([^:]+)$"))
    async def delete_folder_confirm_callback(c, callback: CallbackQuery):
        print(f"[BOT] ✅ Received delete folder confirm callback")
        folder_id = callback.data.split(":")[1]
        
        folder = await get_folder_by_id(folder_id)
        if not folder:
            await callback.answer("❌ Folder not found!", show_alert=True)
            return
        
        await callback.message.edit_text(
            f"⚠️ **Delete Folder?**\n\n"
            f"📁 **{folder['name']}**\n\n"
            f"This will delete the folder and ALL files inside it.\n"
            f"This action cannot be undone!",
            reply_markup=confirm_delete_kb("folder", folder_id)
        )
        await callback.answer()
    
    @client.on_callback_query(filters.regex("^confirm_delete_folder:([^:]+)$"))
    async def confirm_delete_folder_callback(c, callback: CallbackQuery):
        print(f"[BOT] ✅ Received confirm delete folder callback")
        folder_id = callback.data.split(":")[1]
        
        success = await delete_folder(folder_id, callback.from_user.id)
        
        if success:
            await callback.answer("✅ Folder deleted successfully!", show_alert=True)
            await show_folders_page(callback.message, 1, edit=True)
        else:
            await callback.answer("❌ Failed to delete folder!", show_alert=True)
    
    @client.on_callback_query(filters.regex("^stats$"))
    async def stats_callback(c, callback: CallbackQuery):
        print(f"[BOT] ✅ Received stats callback")
        stats = await get_stats(callback.from_user.id)
        
        await callback.message.edit_text(
            f"📊 **Your Statistics:**\n\n"
            f"📁 Total Folders: {stats['folders']}\n"
            f"🎬 Total Files: {stats['files']}\n"
            f"💾 Total Storage: {stats['total_size_mb']:.2f} MB\n"
            f"🔗 Total Views: {stats.get('views', 0)}\n"
            f"⬇️ Total Downloads: {stats.get('downloads', 0)}",
            reply_markup=main_menu_kb()
        )
        await callback.answer()
    
    @client.on_callback_query(filters.regex("^help$"))
    async def help_callback(c, callback: CallbackQuery):
        print(f"[BOT] ✅ Received help callback")
        help_text = """
📖 **Quick Guide:**

**Folders:** Organize your files
**Add Files:** Send videos to any folder
**Links:** Get instant streaming links
**Embed:** Use links in any website

Use /help for detailed instructions.
        """
        await callback.message.edit_text(
            help_text,
            reply_markup=main_menu_kb()
        )
        await callback.answer()
    
    @client.on_callback_query(filters.regex("^new_folder$"))
    async def new_folder_callback(c, callback: CallbackQuery):
        print(f"[BOT] ✅ Received new folder callback")
        await callback.message.edit_text(
            "📁 **Create New Folder**\n\n"
            "Send the folder name using:\n"
            "`/newfolder Folder Name`\n\n"
            "Example: `/newfolder My Movies`",
            reply_markup=main_menu_kb()
        )
        await callback.answer()
    
    @client.on_callback_query(filters.regex("^add_files:([^:]+)$"))
    async def add_files_callback(c, callback: CallbackQuery):
        print(f"[BOT] ✅ Received add files callback")
        folder_id = callback.data.split(":")[1]
        
        # Set folder context for user
        from bot.handlers.media import set_user_folder_context
        set_user_folder_context(callback.from_user.id, folder_id)
        
        folder = await get_folder_by_id(folder_id)
        
        await callback.message.edit_text(
            f"📤 **Add Files to: {folder['name']}**\n\n"
            f"Send me any video or document files.\n"
            f"I'll automatically add them to this folder.\n\n"
            f"Supported formats: MP4, MKV, AVI, MOV, etc.\n\n"
            f"When done, use /done",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Folder", callback_data=f"folder:{folder_id}:1")
            ]])
        )
        await callback.answer("✅ Now send me your files!")
    
    @client.on_callback_query(filters.regex("^noop$"))
    async def noop_callback(c, callback: CallbackQuery):
        await callback.answer()
    
    # ==================== MEDIA HANDLERS ====================
    
    @client.on_message(filters.private & (filters.video | filters.document))
    async def handle_media(c, message: Message):
        print(f"[BOT] ✅ Received media from {message.from_user.id}")
        from bot.handlers.media import user_folder_context
        from database.operations import add_file_to_folder
        import re
        
        user_id = message.from_user.id
        folder_id = user_folder_context.get(user_id)
        
        if not folder_id:
            await message.reply_text(
                "📤 To save this file:\n\n"
                "1. First create a folder: /newfolder <name>\n"
                "2. Open the folder from /myfolders\n"
                "3. Click 'Add Files'\n"
                "4. Send your media files"
            )
            return
        
        try:
            # Extract file information
            if message.video:
                media = message.video
                file_id = media.file_id
                file_unique_id = media.file_unique_id
                file_name = media.file_name or "video.mp4"
                mime_type = media.mime_type
                file_size = media.file_size
                duration = media.duration
                width = media.width
                height = media.height
                thumbnail = media.thumbs[0].file_id if media.thumbs else None
            elif message.document:
                media = message.document
                file_id = media.file_id
                file_unique_id = media.file_unique_id
                file_name = media.file_name or "document"
                mime_type = media.mime_type
                file_size = media.file_size
                thumbnail = media.thumbs[0].file_id if media.thumbs else None
                duration = None
                width = None
                height = None
            else:
                await message.reply_text("❌ Unsupported file type.")
                return
            
            # Extract quality and language
            def extract_quality(filename):
                quality_patterns = [
                    r'\b(4320p|2160p|1440p|1080p|720p|480p|360p|240p)\b',
                    r'\b(4K|2K|HD|FHD|UHD|8K)\b',
                ]
                for pattern in quality_patterns:
                    match = re.search(pattern, filename, re.IGNORECASE)
                    if match:
                        return match.group(1).upper()
                return None
            
            def extract_language(filename):
                language_patterns = {
                    r'\b(Hindi|Tamil|Telugu|Malayalam|Kannada|Bengali|Marathi|Gujarati|Punjabi)\b': lambda m: m.group(1),
                    r'\b(English|Eng)\b': lambda m: 'English',
                    r'\b(Dual Audio|Multi Audio)\b': lambda m: 'Multi Audio',
                }
                for pattern, extractor in language_patterns.items():
                    match = re.search(pattern, filename, re.IGNORECASE)
                    if match:
                        return extractor(match)
                return None
            
            quality = extract_quality(file_name)
            language = extract_language(file_name)
            
            # Generate unique file ID
            unique_file_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            
            # Save to database
            file_doc = {
                'fileId': unique_file_id,
                'telegramFileId': file_id,
                'telegramFileUniqueId': file_unique_id,
                'fileName': file_name,
                'mimeType': mime_type,
                'size': file_size,
                'folderId': folder_id,
                'caption': message.caption,
                'quality': quality,
                'language': language,
                'duration': duration,
                'width': width,
                'height': height,
                'thumbnail': thumbnail,
            }
            
            await add_file_to_folder(file_doc, user_id)
            
            # Generate URLs
            watch_url = f"{config.BASE_APP_URL}/{unique_file_id}"
            download_url = f"{config.BASE_APP_URL}/dl/{unique_file_id}"
            
            size_mb = file_size / (1024 * 1024) if file_size else 0
            
            response = (
                f"✅ **File Added Successfully!**\n\n"
                f"📄 **Name:** {file_name}\n"
                f"💾 **Size:** {size_mb:.2f} MB\n"
            )
            
            if quality:
                response += f"🎥 **Quality:** {quality}\n"
            if language:
                response += f"🗣 **Language:** {language}\n"
            if duration:
                mins = duration // 60
                secs = duration % 60
                response += f"⏱ **Duration:** {mins}m {secs}s\n"
            
            response += (
                f"\n🔗 **Links:**\n"
                f"▶️ Watch: `{watch_url}`\n"
                f"⬇️ Download: `{download_url}`\n\n"
                f"Send more files or use /done when finished."
            )
            
            await message.reply_text(response)
            
        except Exception as e:
            print(f"Error handling media: {e}")
            await message.reply_text("❌ Failed to save file. Please try again.")
    
    @client.on_message(filters.command("done") & filters.private)
    async def done_adding_files(c, message: Message):
        print(f"[BOT] ✅ Received /done from {message.from_user.id}")
        from bot.handlers.media import user_folder_context
        
        user_id = message.from_user.id
        
        if user_id in user_folder_context:
            folder_id = user_folder_context.pop(user_id)
            folder = await get_folder_by_id(folder_id)
            
            await message.reply_text(
                f"✅ Finished adding files to **{folder['name']}**\n\n"
                f"Use /myfolders to view your folders."
            )
        else:
            await message.reply_text("You weren't adding files to any folder.")
    
    # ==================== HELPER FUNCTIONS ====================
    
    async def show_folders_page(message: Message, page: int, edit: bool = False):
        """Show folders page"""
        user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
        
        total = await count_user_folders(user_id)
        total_pages = max(1, math.ceil(total / PAGE_SIZE))
        page = min(page, total_pages)
        
        folders = await get_user_folders(user_id, page, PAGE_SIZE)
        
        text = f"📁 **Your Folders** (Page {page}/{total_pages})\n\n"
        
        if not folders:
            text += "No folders yet. Create one to get started!"
        else:
            text += f"Total: {total} folders"
        
        if edit:
            await message.edit_text(text, reply_markup=folders_kb(folders, page, total_pages))
        else:
            await message.reply_text(text, reply_markup=folders_kb(folders, page, total_pages))
    
    async def show_folder_contents(message: Message, folder_id: str, page: int, edit: bool = False):
        """Show folder contents"""
        folder = await get_folder_by_id(folder_id)
        if not folder:
            if edit:
                await message.edit_text("❌ Folder not found!", reply_markup=main_menu_kb())
            return
        
        total = await count_folder_files(folder_id)
        total_pages = max(1, math.ceil(total / PAGE_SIZE))
        page = min(page, total_pages)
        
        files = await get_folder_files(folder_id, page, PAGE_SIZE)
        
        text = f"📁 **{folder['name']}**\n\n"
        
        if not files:
            text += "No files in this folder yet.\nClick 'Add Files' to upload."
        else:
            text += f"Total: {total} files (Page {page}/{total_pages})"
        
        if edit:
            await message.edit_text(text, reply_markup=folder_view_kb(folder_id, files, page, total_pages))
        else:
            await message.reply_text(text, reply_markup=folder_view_kb(folder_id, files, page, total_pages))
    
    print(f"[HANDLERS] All handlers registered successfully")

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