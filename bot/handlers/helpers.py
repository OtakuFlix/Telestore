import math
from pyrogram.types import Message
from bot.keyboards import (
    folders_kb, folder_view_kb, main_menu_kb, 
    quality_folder_view_kb, simplified_file_list_kb, files_by_basename_kb
)
from database.operations import (
    count_user_folders,
    get_user_folders,
    count_folder_files,
    get_folder_files,
    get_folder_by_id,
    get_quality_folders,
    get_simplified_file_list,
    get_files_by_basename
)

PAGE_SIZE = 8

async def show_folders_page(message: Message, page: int = 1, edit: bool = False, user_id: int = None):
    if user_id is None:
        if hasattr(message, "from_user") and message.from_user:
            user_id = message.from_user.id
        else:
            try:
                user_id = message.chat.id
            except Exception:
                user_id = None

    print(f"[HELPERS] show_folders_page: user_id={user_id}, page={page}, edit={edit}")

    if user_id is None:
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
        text += "No folders yet. Create one to get started!\n\n"
        text += "**Auto Upload Format:**\n`<Folder><File><Quality><Size>`"
    else:
        text += f"Total: {total} folders"

    if edit:
        await message.edit_text(text, reply_markup=folders_kb(folders, page, total_pages))
    else:
        await message.reply_text(text, reply_markup=folders_kb(folders, page, total_pages))


async def show_quality_folders(message: Message, folder_id: str, edit: bool = False, user_id: int = None):
    folder = await get_folder_by_id(folder_id)
    if not folder:
        if edit:
            await message.edit_text("❌ Folder not found!", reply_markup=main_menu_kb())
        else:
            await message.reply_text("❌ Folder not found!", reply_markup=main_menu_kb())
        return
    
    quality_folders = await get_quality_folders(folder_id)
    
    text = f"📁 **{folder['name']}**\n\n"
    if not quality_folders:
        text += "No quality folders yet.\nClick 'Add Files' to upload and auto-create quality folders."
    else:
        text += f"Available qualities: {len(quality_folders)}"
    
    if edit:
        await message.edit_text(text, reply_markup=quality_folder_view_kb(folder_id, quality_folders))
    else:
        await message.reply_text(text, reply_markup=quality_folder_view_kb(folder_id, quality_folders))


async def show_folder_contents(message: Message, folder_id: str, page: int = 1, edit: bool = False, user_id: int = None):
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

    text = f"📁 **{folder['name']}**\n"
    if folder.get('quality'):
        text += f"🎥 **Quality: {folder['quality']}**\n"
    text += "\n"
    
    if not files:
        text += "No files in this folder yet.\nUpload files to this quality folder."
    else:
        text += f"Total: {total} files (Page {page}/{total_pages})"

    if edit:
        await message.edit_text(text, reply_markup=folder_view_kb(folder_id, files, page, total_pages))
    else:
        await message.reply_text(text, reply_markup=folder_view_kb(folder_id, files, page, total_pages))


async def show_simplified_file_list(message: Message, folder_id: str, edit: bool = False):
    folder = await get_folder_by_id(folder_id)
    if not folder:
        if edit:
            await message.edit_text("❌ Folder not found!", reply_markup=main_menu_kb())
        else:
            await message.reply_text("❌ Folder not found!", reply_markup=main_menu_kb())
        return
    
    file_groups = await get_simplified_file_list(folder_id)
    
    text = f"📁 **{folder['name']}**\n\n"
    if not file_groups:
        text += "No files in this folder yet."
    else:
        text += f"Total: {len(file_groups)} unique files"
    
    if edit:
        await message.edit_text(text, reply_markup=simplified_file_list_kb(folder_id, file_groups))
    else:
        await message.reply_text(text, reply_markup=simplified_file_list_kb(folder_id, file_groups))


async def show_files_by_basename(message: Message, folder_id: str, base_name: str, edit: bool = False):
    files = await get_files_by_basename(folder_id, base_name)
    
    text = f"📦 **{base_name}**\n\n"
    if not files:
        text += "No files found."
    else:
        text += f"Available in {len(files)} qualities:"
    
    if edit:
        await message.edit_text(text, reply_markup=files_by_basename_kb(folder_id, base_name, files))
    else:
        await message.reply_text(text, reply_markup=files_by_basename_kb(folder_id, base_name, files))