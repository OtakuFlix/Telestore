from pyrogram import filters
from database.operations import get_or_create_quality_folder
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards import (
    main_menu_kb, folders_kb, folder_view_kb,
    file_actions_kb, confirm_delete_kb, quality_selection_kb,
    quality_folder_view_kb, files_by_basename_kb
)
from database.operations import (
    get_user_folders, get_folder_files, get_file_by_id,
    delete_file, delete_folder, get_folder_by_id, get_stats,
    count_user_folders, count_folder_files, get_quality_folders,
    get_simplified_file_list, get_files_by_basename, get_all_folder_files
)
from bot.handlers.helpers import show_folders_page, show_folder_contents, show_quality_folders, show_files_by_basename
from config import config
import math

PAGE_SIZE = 8

def register_callback_handlers(bot):

    @bot.on_callback_query(filters.regex(r"^main_menu$"))
    async def main_menu_callback(bot_instance, callback: CallbackQuery):
        welcome_text = f"""
╔═══════════════════════════╗
║   🎬 **TeleStore Bot** 🎬   ║
╚═══════════════════════════╝

👋 **Welcome back {callback.from_user.first_name}!**

Choose an option below to continue:
"""
        await callback.message.edit_text(
            welcome_text,
            reply_markup=main_menu_kb()
        )
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^folders:\d+$"))
    async def folders_callback(bot_instance, callback: CallbackQuery):
        page = int(callback.data.split(":")[1])
        user_id = callback.from_user.id if callback.from_user else None
        await show_folders_page(callback.message, page, edit=True, user_id=user_id)
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^folder:[\w]+:\d+$"))
    async def folder_view_callback(bot_instance, callback: CallbackQuery):
        parts = callback.data.split(":")
        folder_id = parts[1]
        page = int(parts[2])
        user_id = callback.from_user.id if callback.from_user else None
        await show_quality_folders(callback.message, folder_id, edit=True, user_id=user_id)
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^quality_folder:[\w]+:\d+$"))
    async def quality_folder_callback(bot_instance, callback: CallbackQuery):
        parts = callback.data.split(":")
        quality_folder_id = parts[1]
        page = int(parts[2])
        user_id = callback.from_user.id if callback.from_user else None
        await show_folder_contents(callback.message, quality_folder_id, page, edit=True, user_id=user_id)
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^basename:[\w]+:"))
    async def basename_view_callback(bot_instance, callback: CallbackQuery):
        parts = callback.data.split(":", 2)
        folder_id = parts[1]
        base_name = parts[2]
        await show_files_by_basename(callback.message, folder_id, base_name, edit=True)
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^all_embeds:[\w]+$"))
    async def all_embeds_callback(bot_instance, callback: CallbackQuery):
        folder_id = callback.data.split(":")[1]
        
        folder = await get_folder_by_id(folder_id)
        if not folder:
            await callback.answer("❌ Folder not found!", show_alert=True)
            return
        
        await callback.answer("🔄 Generating embed links...", show_alert=False)
        
        # Get all quality folders
        quality_folders = await get_quality_folders(folder_id)
        
        all_files = []
        for qf in quality_folders:
            files = await get_all_folder_files(qf['folderId'])
            all_files.extend(files)
        
        if not all_files:
            await callback.message.reply_text("❌ No files found in this folder!")
            return
        
        # Group files by masterGroupId
        master_groups = {}
        for file in all_files:
            master_id = file.get('masterGroupId')
            if not master_id:
                continue
            
            if master_id not in master_groups:
                master_groups[master_id] = {
                    'fileName': file.get('fileName', 'Unnamed'),
                    'baseName': file.get('baseName', 'Unknown'),
                    'masterGroupId': master_id,
                    'qualities': []
                }
            master_groups[master_id]['qualities'].append(file.get('quality', 'Unknown'))
        
        if not master_groups:
            await callback.message.reply_text("❌ No master group IDs found!")
            return
        
        message_text = f"🔗 **All Embed Links - {folder['name']}**\n\n"
        message_text += f"📁 Total Groups: {len(master_groups)}\n"
        message_text += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for idx, (master_id, data) in enumerate(sorted(master_groups.items()), 1):
            file_name = data['fileName']
            qualities = ', '.join(sorted(set(data['qualities'])))
            embed_link = f"{config.BASE_APP_URL}/embed/{master_id}"
            
            message_text += f"{idx}. **{file_name}**\n"
            message_text += f"   Qualities: [{qualities}]\n"
            message_text += f"   {embed_link}\n\n"
            
            # Telegram message limit ~4096 chars
            if len(message_text) > 3500:
                await callback.message.reply_text(message_text)
                message_text = ""
        
        if message_text:
            await callback.message.reply_text(message_text)
        
        await callback.message.reply_text(
            f"✅ Generated {len(master_groups)} embed links!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Folder", callback_data=f"folder:{folder_id}:1")
            ]])
        )

    @bot.on_callback_query(filters.regex(r"^all_downloads:[\w]+$"))
    async def all_downloads_callback(bot_instance, callback: CallbackQuery):
        folder_id = callback.data.split(":")[1]
        
        folder = await get_folder_by_id(folder_id)
        if not folder:
            await callback.answer("❌ Folder not found!", show_alert=True)
            return
        
        await callback.answer("🔄 Generating download links...", show_alert=False)
        
        quality_folders = await get_quality_folders(folder_id)
        
        all_files = []
        for qf in quality_folders:
            files = await get_all_folder_files(qf['folderId'])
            all_files.extend(files)
        
        if not all_files:
            await callback.message.reply_text("❌ No files found in this folder!")
            return
        
        message_text = f"⬇️ **All Download Links - {folder['name']}**\n\n"
        message_text += f"📁 Total Files: {len(all_files)}\n"
        message_text += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for idx, file in enumerate(all_files, 1):
            file_id = file['fileId']
            file_name = file.get('fileName', 'Unnamed')
            quality = file.get('quality', 'Unknown')
            size = file.get('size', 0)
            size_mb = size / (1024 * 1024) if size else 0
            download_link = f"{config.BASE_APP_URL}/dl/{file_id}"
            
            message_text += f"{idx}. **{file_name}** [{quality}] ({size_mb:.1f}MB)\n"
            message_text += f"   {download_link}\n\n"
            
            if len(message_text) > 3500:
                await callback.message.reply_text(message_text)
                message_text = ""
        
        if message_text:
            await callback.message.reply_text(message_text)
        
        await callback.message.reply_text(
            f"✅ Generated {len(all_files)} download links!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Folder", callback_data=f"folder:{folder_id}:1")
            ]])
        )

    @bot.on_callback_query(filters.regex(r"^all_watch:[\w]+$"))
    async def all_watch_callback(bot_instance, callback: CallbackQuery):
        folder_id = callback.data.split(":")[1]
        
        folder = await get_folder_by_id(folder_id)
        if not folder:
            await callback.answer("❌ Folder not found!", show_alert=True)
            return
        
        await callback.answer("🔄 Generating watch links...", show_alert=False)
        
        quality_folders = await get_quality_folders(folder_id)
        
        all_files = []
        for qf in quality_folders:
            files = await get_all_folder_files(qf['folderId'])
            all_files.extend(files)
        
        if not all_files:
            await callback.message.reply_text("❌ No files found in this folder!")
            return
        
        # Group by masterGroupId for watch links
        master_groups = {}
        for file in all_files:
            master_id = file.get('masterGroupId')
            if not master_id:
                continue
            
            if master_id not in master_groups:
                master_groups[master_id] = {
                    'fileName': file.get('fileName', 'Unnamed'),
                    'baseName': file.get('baseName', 'Unknown'),
                    'masterGroupId': master_id,
                    'qualities': []
                }
            master_groups[master_id]['qualities'].append(file.get('quality', 'Unknown'))
        
        if not master_groups:
            await callback.message.reply_text("❌ No master group IDs found!")
            return
        
        message_text = f"▶️ **All Watch Links - {folder['name']}**\n\n"
        message_text += f"📁 Total Groups: {len(master_groups)}\n"
        message_text += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for idx, (master_id, data) in enumerate(sorted(master_groups.items()), 1):
            file_name = data['fileName']
            qualities = ', '.join(sorted(set(data['qualities'])))
            watch_link = f"{config.BASE_APP_URL}/watch/{master_id}"
            
            message_text += f"{idx}. **{file_name}**\n"
            message_text += f"   Qualities: [{qualities}]\n"
            message_text += f"   {watch_link}\n\n"
            
            if len(message_text) > 3500:
                await callback.message.reply_text(message_text)
                message_text = ""
        
        if message_text:
            await callback.message.reply_text(message_text)
        
        await callback.message.reply_text(
            f"✅ Generated {len(master_groups)} watch links!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Folder", callback_data=f"folder:{folder_id}:1")
            ]])
        )

    @bot.on_callback_query(filters.regex(r"^file:[a-f0-9]{24}$"))
    async def file_view_callback(bot_instance, callback: CallbackQuery):
        file_id = callback.data.split(":")[1]
        
        file_data = await get_file_by_id(file_id)
        if not file_data:
            await callback.answer("❌ File not found!", show_alert=True)
            return
        
        info = f"🎬 **{file_data.get('fileName', 'Unnamed')}**\n\n"
        
        if file_data.get('baseName'):
            info += f"📦 **Base Name:** {file_data['baseName']}\n"
        
        if file_data.get('masterGroupId'):
            info += f"🔗 **Master ID:** `{file_data['masterGroupId']}`\n"
        
        if file_data.get('size'):
            size_mb = file_data['size'] / (1024 * 1024)
            info += f"💾 **Size:** {size_mb:.2f} MB\n"
        
        if file_data.get('mimeType'):
            info += f"📄 **Type:** {file_data['mimeType']}\n"
        
        if file_data.get('quality'):
            info += f"🎥 **Quality:** {file_data['quality']}\n"
        
        if file_data.get('language'):
            info += f"🗣 **Language:** {file_data['language']}\n"
        
        if file_data.get('duration'):
            mins = file_data['duration'] // 60
            secs = file_data['duration'] % 60
            info += f"⏱ **Duration:** {mins}m {secs}s\n"
        
        if file_data.get('caption'):
            info += f"\n📝 {file_data['caption']}\n"
        
        info += f"\n🔗 **Quick Links:**"
        info += f"\n▶️ Watch: {config.BASE_APP_URL}/watch/{file_id}"
        info += f"\n📥 Stream: {config.BASE_APP_URL}/{file_id}"
        info += f"\n⬇️ Download: {config.BASE_APP_URL}/dl/{file_id}"
        
        # Add master group embed link if available
        if file_data.get('masterGroupId'):
            info += f"\n🔗 Embed: {config.BASE_APP_URL}/embed/{file_data['masterGroupId']}"
        
        await callback.message.edit_text(
            info,
            reply_markup=file_actions_kb(file_id, file_data['folderId'])
        )
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^delete_file:[a-f0-9]{24}:[\w]+$"))
    async def delete_file_confirm_callback(bot_instance, callback: CallbackQuery):
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

    @bot.on_callback_query(filters.regex(r"^confirm_delete_file:[a-f0-9]{24}:[\w]+$"))
    async def confirm_delete_file_callback(bot_instance, callback: CallbackQuery):
        parts = callback.data.split(":")
        file_id = parts[1]
        folder_id = parts[2]
        
        success = await delete_file(file_id)
        
        if success:
            await callback.answer("✅ File deleted successfully!", show_alert=True)
            await show_folder_contents(callback.message, folder_id, 1, edit=True)
        else:
            await callback.answer("❌ Failed to delete file!", show_alert=True)

    @bot.on_callback_query(filters.regex(r"^delete_folder:[\w]+$"))
    async def delete_folder_confirm_callback(bot_instance, callback: CallbackQuery):
        folder_id = callback.data.split(":")[1]
        
        folder = await get_folder_by_id(folder_id)
        if not folder:
            await callback.answer("❌ Folder not found!", show_alert=True)
            return
        
        await callback.message.edit_text(
            f"⚠️ **Delete Folder?**\n\n📁 **{folder['name']}**\n\n"
            f"This will delete the folder and ALL files/subfolders inside it.\n"
            f"This action cannot be undone!",
            reply_markup=confirm_delete_kb("folder", folder_id)
        )
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^confirm_delete_folder:[\w]+$"))
    async def confirm_delete_folder_callback(bot_instance, callback: CallbackQuery):
        folder_id = callback.data.split(":")[1]
        
        success = await delete_folder(folder_id, callback.from_user.id)
        
        if success:
            await callback.answer("✅ Folder deleted successfully!", show_alert=True)
            await show_folders_page(callback.message, 1, edit=True)
        else:
            await callback.answer("❌ Failed to delete folder!", show_alert=True)

    @bot.on_callback_query(filters.regex(r"^stats$"))
    async def stats_callback(bot_instance, callback: CallbackQuery):
        stats = await get_stats(callback.from_user.id)
        
        stats_text = f"""
📊 **Your Storage Statistics**

**━━━━━━━━━━━━━━━━━━━━**

📁 **Folders:** {stats['folders']}
🎬 **Total Files:** {stats['files']}
💾 **Storage Used:** {stats['total_size_mb']:.2f} MB
👁️ **Total Views:** {stats.get('views', 0):,}
⬇️ **Total Downloads:** {stats.get('downloads', 0):,}

**━━━━━━━━━━━━━━━━━━━━**

💡 **Keep uploading to grow your library!**
"""
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=main_menu_kb()
        )
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^help$"))
    async def help_callback(bot_instance, callback: CallbackQuery):
        help_text = """
📖 **Quick Guide:**

**Auto Upload Format:**
`<Folder><File><Quality><Size>`

**Example:**
`<Naruto><01.mp4><1080p><234MB>`

**Manual Upload:**
1. Create folder → Select quality → Upload

**Features:**
• Multi-quality support (4K-360p)
• Nested folder structure
• Auto-organize files
• Quality switching in player
• Bulk link generation

Use /help for detailed instructions.
"""
        await callback.message.edit_text(help_text, reply_markup=main_menu_kb())
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^backup_menu$"))
    async def backup_menu_callback(bot_instance, callback: CallbackQuery):
        backup_text = """
💾 **Database Backup & Restore**

**━━━━━━━━━━━━━━━━━━━━**

**Export Database:**
Use `/vanish` to create a complete backup of your database.

**Restore Database:**
Use `/retrieve` to restore from a backup file.

**What's Included:**
• All folders and subfolders
• All file metadata
• Quality mappings
• Statistics data
• Master group IDs

**━━━━━━━━━━━━━━━━━━━━**

⚠️ **Important:** Keep backup files secure!
"""
        await callback.message.edit_text(backup_text, reply_markup=main_menu_kb())
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^settings$"))
    async def settings_callback(bot_instance, callback: CallbackQuery):
        settings_text = """
⚙️ **Bot Settings**

**━━━━━━━━━━━━━━━━━━━━**

**Current Configuration:**
• Auto-numbering: ✅ Enabled
• Quality Detection: ✅ Enabled
• Language Detection: ✅ Enabled
• Master Grouping: ✅ Enabled

**Available Commands:**
• `/newfolder` - Create new folder
• `/myfolders` - View all folders
• `/stats` - View statistics
• `/vanish` - Export database
• `/retrieve` - Restore database
• `/help` - Detailed guide

**━━━━━━━━━━━━━━━━━━━━**

💡 All features are optimized!
"""
        await callback.message.edit_text(settings_text, reply_markup=main_menu_kb())
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^new_folder$"))
    async def new_folder_callback(bot_instance, callback: CallbackQuery):
        await callback.message.edit_text(
            "📁 **Create New Folder**\n\n"
            "**━━━━━━━━━━━━━━━━━━━━**\n\n"
            "Use the command below to create a folder:\n"
            "`/newfolder <folder name>`\n\n"
            "**Examples:**\n"
            "• `/newfolder My Movies`\n"
            "• `/newfolder TV Series 2024`\n"
            "• `/newfolder Anime Collection`\n\n"
            "**━━━━━━━━━━━━━━━━━━━━**\n\n"
            "💡 Folders get auto-numbered IDs (1, 2, 3...)",
            reply_markup=main_menu_kb()
        )
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^add_files:[\w]+$"))
    async def add_files_callback(bot_instance, callback: CallbackQuery):
        folder_id = callback.data.split(":")[1]
        folder = await get_folder_by_id(folder_id)
        
        await callback.message.edit_text(
            f"📤 **Add Files to: {folder['name']}**\n\n"
            f"**Select Quality:**",
            reply_markup=quality_selection_kb(folder_id)
        )
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^select_quality:[\w]+:\w+$"))
    async def select_quality_callback(bot_instance, callback: CallbackQuery):
        from bot.handlers.media import set_user_folder_context, set_user_quality_context
        
        parts = callback.data.split(":")
        parent_folder_id = parts[1]
        quality = parts[2]
        
        quality_folder_id = await get_or_create_quality_folder(
            parent_folder_id, 
            quality, 
            callback.from_user.id
        )
        
        set_user_folder_context(callback.from_user.id, quality_folder_id)
        set_user_quality_context(callback.from_user.id, quality)
        
        folder = await get_folder_by_id(parent_folder_id)
        
        await callback.message.edit_text(
            f"📤 **Adding Files to: {folder['name']}**\n"
            f"🎥 **Quality: {quality}**\n\n"
            f"**━━━━━━━━━━━━━━━━━━━━**\n\n"
            f"Send me any video or document files.\n"
            f"They'll be saved in the {quality} quality folder.\n\n"
            f"**Supported formats:**\n"
            f"MP4, MKV, AVI, MOV, WMV, FLV, WEBM, and more!\n\n"
            f"**━━━━━━━━━━━━━━━━━━━━**\n\n"
            f"When done, use /done",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                "⬅️ Back to Folder", callback_data=f"folder:{parent_folder_id}:1"
            )]])
        )
        await callback.answer(f"✅ Selected {quality} quality")

    @bot.on_callback_query(filters.regex(r"^noop$"))
    async def noop_callback(bot_instance, callback: CallbackQuery):
        await callback.answer()