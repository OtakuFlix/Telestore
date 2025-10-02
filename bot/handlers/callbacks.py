# ==================== bot/handlers/callbacks.py ====================
from pyrogram import filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.client import bot
from bot.keyboards import (
    main_menu_kb, folders_kb, folder_view_kb, 
    file_actions_kb, confirm_delete_kb
)
from database.operations import (
    get_user_folders, get_folder_files, get_file_by_id,
    delete_file, delete_folder, get_folder_by_id, get_stats,
    count_user_folders, count_folder_files
)
import math

PAGE_SIZE = 8

@bot.on_callback_query(filters.regex("^main_menu$"))
async def main_menu_callback(client, callback: CallbackQuery):
    """Handle main menu callback"""
    await callback.message.edit_text(
        "🏠 **Main Menu**\n\n"
        "Choose an option below:",
        reply_markup=main_menu_kb()
    )
    await callback.answer()

@bot.on_callback_query(filters.regex(r"^folders:(\d+)$"))
async def folders_callback(client, callback: CallbackQuery):
    """Handle folders list callback"""
    page = int(callback.data.split(":")[1])
    await show_folders_page(callback.message, page, edit=True)
    await callback.answer()

@bot.on_callback_query(filters.regex(r"^folder:([^:]+):(\d+)$"))
async def folder_view_callback(client, callback: CallbackQuery):
    """Handle folder view callback"""
    parts = callback.data.split(":")
    folder_id = parts[1]
    page = int(parts[2])
    
    await show_folder_contents(callback.message, folder_id, page, edit=True)
    await callback.answer()

@bot.on_callback_query(filters.regex("^file:([^:]+)$"))
async def file_view_callback(client, callback: CallbackQuery):
    """Handle file view callback"""
    file_id = callback.data.split(":")[1]
    
    file_data = await get_file_by_id(file_id)
    if not file_data:
        await callback.answer("❌ File not found!", show_alert=True)
        return
    
    from config import config
    
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

@bot.on_callback_query(filters.regex("^delete_file:([^:]+):([^:]+)$"))
async def delete_file_confirm_callback(client, callback: CallbackQuery):
    """Handle delete file confirmation"""
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

@bot.on_callback_query(filters.regex("^confirm_delete_file:([^:]+):([^:]+)$"))
async def confirm_delete_file_callback(client, callback: CallbackQuery):
    """Handle confirmed file deletion"""
    parts = callback.data.split(":")
    file_id = parts[1]
    folder_id = parts[2]
    
    success = await delete_file(file_id)
    
    if success:
        await callback.answer("✅ File deleted successfully!", show_alert=True)
        await show_folder_contents(callback.message, folder_id, 1, edit=True)
    else:
        await callback.answer("❌ Failed to delete file!", show_alert=True)

@bot.on_callback_query(filters.regex("^delete_folder:([^:]+)$"))
async def delete_folder_confirm_callback(client, callback: CallbackQuery):
    """Handle delete folder confirmation"""
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

@bot.on_callback_query(filters.regex("^confirm_delete_folder:([^:]+)$"))
async def confirm_delete_folder_callback(client, callback: CallbackQuery):
    """Handle confirmed folder deletion"""
    folder_id = callback.data.split(":")[1]
    
    success = await delete_folder(folder_id, callback.from_user.id)
    
    if success:
        await callback.answer("✅ Folder deleted successfully!", show_alert=True)
        await show_folders_page(callback.message, 1, edit=True)
    else:
        await callback.answer("❌ Failed to delete folder!", show_alert=True)

@bot.on_callback_query(filters.regex("^stats$"))
async def stats_callback(client, callback: CallbackQuery):
    """Handle stats callback"""
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

@bot.on_callback_query(filters.regex("^help$"))
async def help_callback(client, callback: CallbackQuery):
    """Handle help callback"""
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

@bot.on_callback_query(filters.regex("^new_folder$"))
async def new_folder_callback(client, callback: CallbackQuery):
    """Handle new folder callback"""
    await callback.message.edit_text(
        "📁 **Create New Folder**\n\n"
        "Send the folder name using:\n"
        "`/newfolder Folder Name`\n\n"
        "Example: `/newfolder My Movies`",
        reply_markup=main_menu_kb()
    )
    await callback.answer()

@bot.on_callback_query(filters.regex("^add_files:([^:]+)$"))
async def add_files_callback(client, callback: CallbackQuery):
    """Handle add files callback"""
    folder_id = callback.data.split(":")[1]
    
    # Import media handler functions
    from bot.handlers.media import set_user_folder_context
    
    # Set folder context for user
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

@bot.on_callback_query(filters.regex("^noop$"))
async def noop_callback(client, callback: CallbackQuery):
    """Handle no-operation callback (for page indicators)"""
    await callback.answer()

# Helper functions
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