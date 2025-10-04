# ==================== bot/handlers/helpers.py ====================
import math
from pyrogram.types import Message
from bot.keyboards import folders_kb, folder_view_kb, main_menu_kb
from database.operations import (
    count_user_folders,
    get_user_folders,
    count_folder_files,
    get_folder_files,
    get_folder_by_id,
)

PAGE_SIZE = 8

async def show_folders_page(message: Message, page: int = 1, edit: bool = False, user_id: int = None):
    """
    Show a paginated list of folders for a user.
    Accepts an optional user_id (for callbacks). If not provided, falls back to message.from_user.id.
    """
    # Resolve user id (callback may provide user_id explicitly)
    if user_id is None:
        # message can be from a channel or bot; fallback carefully
        if hasattr(message, "from_user") and message.from_user:
            user_id = message.from_user.id
        else:
            # best-effort fallback
            try:
                user_id = message.chat.id
            except Exception:
                user_id = None

    # Debug print (remove in production)
    print(f"[HELPERS] show_folders_page: user_id={user_id}, page={page}, edit={edit}")

    if user_id is None:
        # Unable to resolve user -> show generic message
        text = "❌ Cannot determine user. Try the command directly (/myfolders)."
        if edit:
            await message.edit_text(text, reply_markup=main_menu_kb())
        else:
            await message.reply_text(text, reply_markup=main_menu_kb())
        return

    total = await count_user_folders(user_id)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    page = min(max(1, page), total_pages)
    folders = await get_user_folders(user_id, page=page, page_size=PAGE_SIZE)

    text = f"📁 **Your Folders** (Page {page}/{total_pages})\n\n"
    if not folders:
        text += "No folders yet. Create one to get started!"
    else:
        text += f"Total: {total} folders"

    if edit:
        await message.edit_text(text, reply_markup=folders_kb(folders, page, total_pages))
    else:
        await message.reply_text(text, reply_markup=folders_kb(folders, page, total_pages))


async def show_folder_contents(message: Message, folder_id: str, page: int = 1, edit: bool = False, user_id: int = None):
    """
    Show files inside a folder.
    Accepts optional user_id (for callbacks) but will work without it.
    """
    # Resolve user id if needed (not strictly required here but kept for consistency)
    if user_id is None:
        if hasattr(message, "from_user") and message.from_user:
            user_id = message.from_user.id
        else:
            try:
                user_id = message.chat.id
            except Exception:
                user_id = None

    folder = await get_folder_by_id(folder_id)
    if not folder:
        if edit:
            await message.edit_text("❌ Folder not found!", reply_markup=main_menu_kb())
        else:
            await message.reply_text("❌ Folder not found!", reply_markup=main_menu_kb())
        return

    total = await count_folder_files(folder_id)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    page = min(max(1, page), total_pages)
    files = await get_folder_files(folder_id, page=page, page_size=PAGE_SIZE)

    text = f"📁 **{folder['name']}**\n\n"
    if not files:
        text += "No files in this folder yet.\nClick 'Add Files' to upload."
    else:
        text += f"Total: {total} files (Page {page}/{total_pages})"

    if edit:
        await message.edit_text(text, reply_markup=folder_view_kb(folder_id, files, page, total_pages))
    else:
        await message.reply_text(text, reply_markup=folder_view_kb(folder_id, files, page, total_pages))
