# ==================== bot/handlers/commands.py ====================
from pyrogram import filters
from pyrogram.types import Message
from bot.client import bot
from bot.keyboards import main_menu_kb
from database.operations import get_stats, create_folder
from config import config
import secrets
import string

@bot.on_message(filters.command(["start", "menu"]) & filters.private)
async def start_command(client, message: Message):
    """Handle /start and /menu commands"""
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

@bot.on_message(filters.command("help") & filters.private)
async def help_command(client, message: Message):
    """Handle /help command"""
    help_text = """
📖 **How to use TeleStore Bot:**

**Creating Folders:**
• Use /newfolder <name> to create a folder
• Or click "New Folder" in the menu

**Adding Files:**
1. Open any folder
2. Click "Add Files"
3. Send me any video/document
4. Files will be auto-saved with metadata

**Getting Links:**
• Click on any file to get Watch & Download links
• Watch link: Streamable in browser
• Download link: Direct download

**Managing Content:**
• Rename folders and files anytime
• Delete individual files or entire folders
• All links update automatically

**Supported Formats:**
MP4, MKV, AVI, MOV, WMV, FLV, and more!

Need help? Contact support.
    """
    await message.reply_text(help_text, reply_markup=main_menu_kb())

@bot.on_message(filters.command("newfolder") & filters.private)
async def newfolder_command(client, message: Message):
    """Handle /newfolder command"""
    try:
        # Extract folder name
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply_text(
                "❌ Please provide a folder name.\n\n"
                "**Usage:** `/newfolder My Movies`"
            )
            return
        
        folder_name = parts[1].strip()
        if len(folder_name) < 2:
            await message.reply_text("❌ Folder name must be at least 2 characters long.")
            return
        
        # Generate unique folder ID
        folder_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        # Create folder in database
        await create_folder(
            folder_id=folder_id,
            name=folder_name,
            created_by=message.from_user.id
        )
        
        await message.reply_text(
            f"✅ Folder created successfully!\n\n"
            f"📁 **Name:** {folder_name}\n"
            f"🆔 **ID:** `{folder_id}`\n\n"
            f"Now you can add files to this folder.",
            reply_markup=main_menu_kb()
        )
    
    except Exception as e:
        print(f"Error creating folder: {e}")
        await message.reply_text(
            "❌ Failed to create folder. Please try again.",
            reply_markup=main_menu_kb()
        )

@bot.on_message(filters.command("stats") & filters.private)
async def stats_command(client, message: Message):
    """Handle /stats command"""
    stats = await get_stats(message.from_user.id)
    
    await message.reply_text(
        f"📊 **Your Statistics:**\n\n"
        f"📁 Total Folders: {stats['folders']}\n"
        f"🎬 Total Files: {stats['files']}\n"
        f"💾 Total Storage: {stats['total_size_mb']:.2f} MB\n"
        f"🔗 Total Views: {stats.get('views', 0)}\n"
        f"⬇️ Total Downloads: {stats.get('downloads', 0)}",
        reply_markup=main_menu_kb()
    )

@bot.on_message(filters.command("myfolders") & filters.private)
async def myfolders_command(client, message: Message):
    """Handle /myfolders command - quick access to folders"""
    from bot.handlers.callbacks import show_folders_page
    await show_folders_page(message, page=1, edit=False)

