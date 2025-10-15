from pyrogram import filters
from pyrogram.types import Message
from bot.keyboards import main_menu_kb
<<<<<<< HEAD
from database.operations import get_stats, create_folder, generate_next_folder_id
=======
from database.operations import get_stats, create_folder
>>>>>>> origin/main
import secrets
import string

from bot.handlers.helpers import show_folders_page, show_folder_contents


def register_command_handlers(bot):
    """Register all command handlers on the given bot instance"""

    @bot.on_message(filters.command(["start", "menu"]) & filters.private)
    async def start_command(client, message: Message):
        """Handle /start and /menu commands"""
        user = message.from_user
<<<<<<< HEAD
        
        welcome_text = f"""
╔═══════════════════════════╗
║   🎬 **TeleStore Bot** 🎬   ║
╚═══════════════════════════╝

👋 **Welcome {user.first_name}!**

🌟 **Your Personal Cloud Storage Solution**

**✨ Key Features:**
• 📁 Organize files in folders & subfolders
• 🎥 Multi-quality support (4K to 360p)
• 🔗 Instant streaming links
• ⬇️ Direct download support
• 🌐 Embeddable video player
• 💾 Database backup & restore
• 📊 Detailed statistics tracking

**🚀 Quick Start:**
1️⃣ Create a folder with /newfolder
2️⃣ Upload files with quality tags
3️⃣ Get shareable links instantly

**💡 Auto Upload Format:**
`<Folder><File><Quality><Size>`

**Example:** 
`<My Movies><Movie.mp4><1080p><2.5GB>`

Use the buttons below to get started! 👇
"""
        
        await message.reply_text(
            welcome_text,
=======
        await message.reply_text(
            f"👋 Welcome {user.first_name}!\n\n"
            f"🎬 **TeleStore Bot** - Your personal cloud storage for videos.\n\n"
            f"📁 Organize files in folders\n"
            f"🔗 Get instant streaming links\n"
            f"⬇️ Direct download support\n"
            f"🌐 Embed videos anywhere\n\n"
            f"Use the menu below to get started:",
>>>>>>> origin/main
            reply_markup=main_menu_kb()
        )

    @bot.on_message(filters.command("help") & filters.private)
    async def help_command(client, message: Message):
        """Handle /help command"""
        help_text = """
<<<<<<< HEAD
📖 **TeleStore Bot - Complete Guide**

**━━━━━━━━━━━━━━━━━━━━**

**📁 CREATING FOLDERS**
• Command: `/newfolder <name>`
• Example: `/newfolder My Movies`
• Folders get auto-numbered IDs (1, 2, 3...)

**📤 UPLOADING FILES**

**Method 1: Auto Upload (Recommended)**
Send file with caption in this format:
`<Folder><Filename><Quality><Size>`

Example:
`<Action Movies><Avengers.mp4><1080p><2.5GB>`

**Method 2: Manual Upload**
1. Open folder from menu
2. Click "Add Files"
3. Select quality (4K/1080p/720p/480p/360p)
4. Send your files
5. Use /done when finished

**🔗 GETTING LINKS**
• Click any file to get:
  - ▶️ Watch Link (streaming player)
  - ⬇️ Download Link (direct download)
  - 📋 Embed Link (for websites)

**📊 BULK OPERATIONS**
From any folder, get all links at once:
• 🔗 All Embed Links
• ⬇️ All Download Links
• ▶️ All Watch Links

**💾 DATABASE MANAGEMENT**
• `/vanish` - Export full database backup
• `/retrieve` - Restore from backup JSON

**🎥 SUPPORTED FORMATS**
MP4, MKV, AVI, MOV, WMV, FLV, WEBM, and more!

**🔧 FEATURES**
• Auto quality detection
• Language detection
• Metadata extraction
• Master group linking
• Real-time statistics
• Multi-quality support

**━━━━━━━━━━━━━━━━━━━━**

💬 Need help? Contact support!
=======
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
>>>>>>> origin/main
        """
        await message.reply_text(help_text, reply_markup=main_menu_kb())

    @bot.on_message(filters.command("newfolder") & filters.private)
    async def newfolder_command(client, message: Message):
        """Handle /newfolder command"""
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply_text(
<<<<<<< HEAD
                "❌ **Missing folder name!**\n\n"
                "**Usage:** `/newfolder <name>`\n\n"
                "**Examples:**\n"
                "• `/newfolder My Movies`\n"
                "• `/newfolder TV Shows 2024`\n"
                "• `/newfolder Anime Collection`"
=======
                "❌ Please provide a folder name.\n\n**Usage:** `/newfolder My Movies`"
>>>>>>> origin/main
            )
            return

        folder_name = parts[1].strip()
        if len(folder_name) < 2:
            await message.reply_text("❌ Folder name must be at least 2 characters long.")
            return

<<<<<<< HEAD
        folder_id = await generate_next_folder_id()
=======
        folder_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
>>>>>>> origin/main

        await create_folder(folder_id=folder_id, name=folder_name, created_by=message.from_user.id)

        await message.reply_text(
<<<<<<< HEAD
            f"✅ **Folder created successfully!**\n\n"
            f"📁 **Name:** {folder_name}\n"
            f"🆔 **Folder ID:** `{folder_id}`\n"
            f"📊 **Status:** Ready for uploads\n\n"
            f"**Next Steps:**\n"
            f"1. Open folder from /myfolders\n"
            f"2. Click 'Add Files'\n"
            f"3. Select quality and upload\n\n"
            f"Or use auto-upload format:\n"
            f"`<{folder_name}><filename><quality><size>`",
=======
            f"✅ Folder created successfully!\n\n"
            f"📁 **Name:** {folder_name}\n"
            f"🆔 **ID:** `{folder_id}`\n\n"
            f"Now you can add files to this folder.",
>>>>>>> origin/main
            reply_markup=main_menu_kb()
        )

    @bot.on_message(filters.command("stats") & filters.private)
    async def stats_command(client, message: Message):
        """Handle /stats command"""
        stats = await get_stats(message.from_user.id)
<<<<<<< HEAD
        
        stats_text = f"""
📊 **Your Storage Statistics**

**━━━━━━━━━━━━━━━━━━━━**

📁 **Folders:** {stats['folders']}
🎬 **Total Files:** {stats['files']}
💾 **Storage Used:** {stats['total_size_mb']:.2f} MB
👁️ **Total Views:** {stats.get('views', 0):,}
⬇️ **Total Downloads:** {stats.get('downloads', 0):,}

**━━━━━━━━━━━━━━━━━━━━**

💡 **Tip:** Keep uploading to expand your library!
"""
        
        await message.reply_text(
            stats_text,
=======
        await message.reply_text(
            f"📊 **Your Statistics:**\n\n"
            f"📁 Total Folders: {stats['folders']}\n"
            f"🎬 Total Files: {stats['files']}\n"
            f"💾 Total Storage: {stats['total_size_mb']:.2f} MB\n"
            f"🔗 Total Views: {stats.get('views', 0)}\n"
            f"⬇️ Total Downloads: {stats.get('downloads', 0)}",
>>>>>>> origin/main
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
        
<<<<<<< HEAD
        status_msg = await message.reply_text(
            "🔄 **Exporting database...**\n\n"
            "⏳ This may take a moment...\n"
            "📦 Packaging all your data..."
        )
=======
        status_msg = await message.reply_text("🔄 **Exporting database...**\n\nThis may take a moment...")
>>>>>>> origin/main
        
        try:
            json_file = await export_database()
            
            if not os.path.exists(json_file):
                await status_msg.edit_text("❌ Failed to create backup file.")
                return
            
            file_size = os.path.getsize(json_file) / (1024 * 1024)
            
<<<<<<< HEAD
            await status_msg.edit_text(
                f"📤 **Uploading backup...**\n\n"
                f"💾 Size: {file_size:.2f} MB\n"
                f"📊 Processing complete..."
            )
=======
            await status_msg.edit_text(f"📤 **Uploading backup...**\n💾 Size: {file_size:.2f} MB")
>>>>>>> origin/main
            
            from datetime import datetime
            backup_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            
            caption = (
<<<<<<< HEAD
                f"📦 **Database Backup Export**\n\n"
                f"📅 **Date:** {backup_time}\n"
                f"💾 **Size:** {file_size:.2f} MB\n"
                f"👤 **Requested by:** {message.from_user.first_name} ({user_id})\n\n"
                f"⚠️ **Security Notice:**\n"
                f"• Keep this file in a secure location\n"
                f"• Don't share with unauthorized users\n"
                f"• Contains all your folder/file data\n\n"
                f"🔄 Use `/retrieve` to restore this backup"
=======
                f"📦 **Database Backup**\n\n"
                f"📅 Date: {backup_time}\n"
                f"💾 Size: {file_size:.2f} MB\n"
                f"👤 Requested by: {message.from_user.first_name} ({user_id})\n\n"
                f"⚠️ **Keep this file safe!**\n"
                f"Use /retrieve to restore this backup"
>>>>>>> origin/main
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
<<<<<<< HEAD
                caption="✅ **Backup created successfully!**\n\n"
                        "📥 **Save this file safely!**\n"
                        "🔒 Keep it in a secure location\n"
                        "🔄 Use /retrieve to restore when needed\n\n"
                        "💡 Backup includes:\n"
                        "• All folders and subfolders\n"
                        "• All file metadata\n"
                        "• Quality mappings\n"
                        "• Statistics data"
=======
                caption="✅ **Database backup created successfully!**\n\n"
                        "📥 Keep this file safe in a secure location.\n"
                        "🔄 Use /retrieve to restore it when needed."
>>>>>>> origin/main
            )
            
            await status_msg.delete()
            
            os.remove(json_file)
            print(f"[VANISH] Backup file deleted from server: {json_file}")
            
        except Exception as e:
            print(f"[VANISH] Error: {e}")
<<<<<<< HEAD
            await status_msg.edit_text(
                f"❌ **Error creating backup:**\n\n"
                f"```{str(e)}```\n\n"
                f"Please try again or contact support."
            )
=======
            await status_msg.edit_text(f"❌ Error creating backup:\n`{str(e)}`")
>>>>>>> origin/main

    @bot.on_message(filters.command("retrieve") & filters.private)
    async def retrieve_command(client, message: Message):
        """Handle /retrieve command - Prompt for backup file"""
        from bot.handlers.backup_handlers import user_waiting_for_json
        
        user_id = message.from_user.id
        user_waiting_for_json[user_id] = True
        
        await message.reply_text(
<<<<<<< HEAD
            "📥 **Database Restore Mode Activated**\n\n"
            "**━━━━━━━━━━━━━━━━━━━━**\n\n"
            "Please send me the JSON backup file you want to restore.\n\n"
            "⚠️ **Important Information:**\n\n"
            "✓ Data will be imported into current database\n"
            "✓ Existing data will NOT be deleted\n"
            "✓ Duplicate entries will be skipped\n"
            "✗ This operation cannot be undone\n\n"
            "**━━━━━━━━━━━━━━━━━━━━**\n\n"
            "📎 **Send the `.json` file now**\n"
            "🚫 Or use /cancel to abort\n\n"
            "💡 Make sure it's the correct backup file!"
=======
            "📥 **Database Restore Mode**\n\n"
            "Please send me the JSON backup file you want to restore.\n\n"
            "⚠️ **Important:**\n"
            "• This will import data into the current database\n"
            "• Existing data will NOT be deleted\n"
            "• Duplicate entries will be automatically skipped\n"
            "• This operation cannot be undone\n\n"
            "📎 Send the `.json` file now, or use /cancel to abort."
>>>>>>> origin/main
        )