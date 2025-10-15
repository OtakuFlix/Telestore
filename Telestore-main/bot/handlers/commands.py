from pyrogram import filters
from pyrogram.types import Message
from bot.keyboards import main_menu_kb
from database.operations import get_stats, create_folder
import secrets
import string

from bot.handlers.helpers import show_folders_page, show_folder_contents


def register_command_handlers(bot):
    """Register all command handlers on the given bot instance"""

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

**Database Backup/Restore:**
• Use /vanish to export entire database
• Use /retrieve to restore from backup JSON

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
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply_text(
                "❌ Please provide a folder name.\n\n**Usage:** `/newfolder My Movies`"
            )
            return

        folder_name = parts[1].strip()
        if len(folder_name) < 2:
            await message.reply_text("❌ Folder name must be at least 2 characters long.")
            return

        folder_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))

        await create_folder(folder_id=folder_id, name=folder_name, created_by=message.from_user.id)

        await message.reply_text(
            f"✅ Folder created successfully!\n\n"
            f"📁 **Name:** {folder_name}\n"
            f"🆔 **ID:** `{folder_id}`\n\n"
            f"Now you can add files to this folder.",
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
        await show_folders_page(message, page=1, edit=False)

    @bot.on_message(filters.command("vanish") & filters.private)
    async def vanish_command(client, message: Message):
        """Handle /vanish command - Export database backup"""
        from database.backup import export_database
        from config import config
        import os
        
        user_id = message.from_user.id
        
        status_msg = await message.reply_text("🔄 **Exporting database...**\n\nThis may take a moment...")
        
        try:
            json_file = await export_database()
            
            if not os.path.exists(json_file):
                await status_msg.edit_text("❌ Failed to create backup file.")
                return
            
            file_size = os.path.getsize(json_file) / (1024 * 1024)
            
            await status_msg.edit_text(f"📤 **Uploading backup...**\n💾 Size: {file_size:.2f} MB")
            
            from datetime import datetime
            backup_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            
            caption = (
                f"📦 **Database Backup**\n\n"
                f"📅 Date: {backup_time}\n"
                f"💾 Size: {file_size:.2f} MB\n"
                f"👤 Requested by: {message.from_user.first_name} ({user_id})\n\n"
                f"⚠️ **Keep this file safe!**\n"
                f"Use /retrieve to restore this backup"
            )
            
            if config.CHANNEL_ID:
                try:
                    await client.send_document(
                        chat_id=config.CHANNEL_ID,
                        document=json_file,
                        caption=caption
                    )
                except Exception as e:
                    print(f"[VANISH] Error sending to channel: {e}")
            
            await client.send_document(
                chat_id=message.chat.id,
                document=json_file,
                caption="✅ **Database backup created successfully!**\n\n"
                        "📥 Keep this file safe in a secure location.\n"
                        "🔄 Use /retrieve to restore it when needed."
            )
            
            await status_msg.delete()
            
            os.remove(json_file)
            print(f"[VANISH] Backup file deleted from server: {json_file}")
            
        except Exception as e:
            print(f"[VANISH] Error: {e}")
            await status_msg.edit_text(f"❌ Error creating backup:\n`{str(e)}`")

    @bot.on_message(filters.command("retrieve") & filters.private)
    async def retrieve_command(client, message: Message):
        """Handle /retrieve command - Prompt for backup file"""
        from bot.handlers.backup_handlers import user_waiting_for_json
        
        user_id = message.from_user.id
        user_waiting_for_json[user_id] = True
        
        await message.reply_text(
            "📥 **Database Restore Mode**\n\n"
            "Please send me the JSON backup file you want to restore.\n\n"
            "⚠️ **Important:**\n"
            "• This will import data into the current database\n"
            "• Existing data will NOT be deleted\n"
            "• Duplicate entries will be automatically skipped\n"
            "• This operation cannot be undone\n\n"
            "📎 Send the `.json` file now, or use /cancel to abort."
        )