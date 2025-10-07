# ==================== bot/handlers/callbacks.py ====================
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards import (
    main_menu_kb, folders_kb, folder_view_kb,
    file_actions_kb, confirm_delete_kb
)
from database.operations import (
    get_user_folders, get_folder_files, get_file_by_id,
    delete_file, delete_folder, get_folder_by_id, get_stats,
    count_user_folders, count_folder_files
)
from bot.handlers.helpers import show_folders_page, show_folder_contents
import math

PAGE_SIZE = 8

def register_callback_handlers(bot):
    """Register all callback query handlers"""

    @bot.on_callback_query(filters.regex(r"^main_menu$"))
    async def main_menu_callback(bot_instance, callback: CallbackQuery):
        await callback.message.edit_text(
            "🏠 **Main Menu**\n\nChoose an option below:",
            reply_markup=main_menu_kb()
        )
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^folders:\d+$"))
    async def folders_callback(bot_instance, callback: CallbackQuery):
        page = int(callback.data.split(":")[1])
        user_id = callback.from_user.id if callback.from_user else None
        await show_folders_page(callback.message, page, edit=True, user_id=user_id)
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^folder:\w+:\d+$"))
    async def folder_view_callback(bot_instance, callback: CallbackQuery):
        parts = callback.data.split(":")
        folder_id = parts[1]
        page = int(parts[2])
        user_id = callback.from_user.id if callback.from_user else None
        await show_folder_contents(callback.message, folder_id, page, edit=True, user_id=user_id)
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^file:[a-f0-9]{24}$"))
    async def file_view_callback(bot_instance, callback: CallbackQuery):
        """Handle file view - file_id is MongoDB ObjectId (24 hex chars)"""
        file_id = callback.data.split(":")[1]
        
        file_data = await get_file_by_id(file_id)
        if not file_data:
            await callback.answer("❌ File not found!", show_alert=True)
            return
        
        from config import config
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
        info += f"\n▶️ Watch: {config.BASE_APP_URL}/watch/{file_id}"
        info += f"\n⬇️ Download: {config.BASE_APP_URL}/dl/{file_id}"
        
        await callback.message.edit_text(
            info,
            reply_markup=file_actions_kb(file_id, file_data['folderId'])
        )
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^delete_file:[a-f0-9]{24}:\w+$"))
    async def delete_file_confirm_callback(bot_instance, callback: CallbackQuery):
        parts = callback.data.split(":")
        file_id = parts[1]
        folder_id = parts[2]
        
        await callback.message.edit_text(
            "⚠️ **Delete File?**\n\n"
            "Are you sure you want to delete this file?\nThis action cannot be undone.",
            reply_markup=confirm_delete_kb("file", file_id, folder_id)
        )
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^confirm_delete_file:[a-f0-9]{24}:\w+$"))
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

    @bot.on_callback_query(filters.regex(r"^delete_folder:\w+$"))
    async def delete_folder_confirm_callback(bot_instance, callback: CallbackQuery):
        folder_id = callback.data.split(":")[1]
        
        folder = await get_folder_by_id(folder_id)
        if not folder:
            await callback.answer("❌ Folder not found!", show_alert=True)
            return
        
        await callback.message.edit_text(
            f"⚠️ **Delete Folder?**\n\n📁 **{folder['name']}**\n\n"
            f"This will delete the folder and ALL files inside it.\n"
            f"This action cannot be undone!",
            reply_markup=confirm_delete_kb("folder", folder_id)
        )
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^confirm_delete_folder:\w+$"))
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

    @bot.on_callback_query(filters.regex(r"^help$"))
    async def help_callback(bot_instance, callback: CallbackQuery):
        help_text = """
📖 **Quick Guide:**

**Folders:** Organize your files
**Add Files:** Send videos to any folder
**Links:** Get instant streaming links
**Embed:** Use links in any website

Use /help for detailed instructions.
"""
        await callback.message.edit_text(help_text, reply_markup=main_menu_kb())
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^new_folder$"))
    async def new_folder_callback(bot_instance, callback: CallbackQuery):
        await callback.message.edit_text(
            "📁 **Create New Folder**\n\nSend the folder name using:\n"
            "`/newfolder Folder Name`\n\nExample: `/newfolder My Movies`",
            reply_markup=main_menu_kb()
        )
        await callback.answer()

    @bot.on_callback_query(filters.regex(r"^add_files:\w+$"))
    async def add_files_callback(bot_instance, callback: CallbackQuery):
        from bot.handlers.media import set_user_folder_context
        folder_id = callback.data.split(":")[1]
        set_user_folder_context(callback.from_user.id, folder_id)
        folder = await get_folder_by_id(folder_id)
        await callback.message.edit_text(
            f"📤 **Add Files to: {folder['name']}**\n\n"
            f"Send me any video or document files.\n"
            f"I'll automatically add them to this folder.\n\n"
            f"Supported formats: MP4, MKV, AVI, MOV, etc.\n\n"
            f"When done, use /done",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                "⬅️ Back to Folder", callback_data=f"folder:{folder_id}:1"
            )]])
        )
        await callback.answer("✅ Now send me your files!")

    @bot.on_callback_query(filters.regex(r"^noop$"))
    async def noop_callback(bot_instance, callback: CallbackQuery):
        await callback.answer()
