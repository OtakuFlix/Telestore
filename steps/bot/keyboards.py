# ==================== bot/keyboards.py ====================
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_kb():
    """Main menu keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 My Folders", callback_data="folders:1")],
        [InlineKeyboardButton("➕ New Folder", callback_data="new_folder")],
        [InlineKeyboardButton("📊 Statistics", callback_data="stats")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
    ])

def folders_kb(folders: list, page: int, total_pages: int):
    """Folders list keyboard with pagination"""
    buttons = []
    
    for folder in folders:
        name = folder['name']
        folder_id = folder['folderId']
        file_count = folder.get('fileCount', 0)
        buttons.append([
            InlineKeyboardButton(
                f"📁 {name} ({file_count} files)",
                callback_data=f"folder:{folder_id}:1"
            )
        ])
    
    # Pagination
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"folders:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"folders:{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(buttons)

def folder_view_kb(folder_id: str, files: list, page: int, total_pages: int):
    """Folder contents keyboard"""
    buttons = []
    
    for file in files:
        file_id = file['fileId']
        name = file.get('fileName', 'Unnamed')
        size = file.get('size', 0)
        size_mb = size / (1024 * 1024) if size else 0
        
        buttons.append([
            InlineKeyboardButton(
                f"🎬 {name} ({size_mb:.1f}MB)",
                callback_data=f"file:{file_id}"
            )
        ])
    
    # Pagination
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"folder:{folder_id}:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"folder:{folder_id}:{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([
        InlineKeyboardButton("➕ Add Files", callback_data=f"add_files:{folder_id}"),
        InlineKeyboardButton("✏️ Rename", callback_data=f"rename_folder:{folder_id}")
    ])
    buttons.append([
        InlineKeyboardButton("🗑 Delete Folder", callback_data=f"delete_folder:{folder_id}"),
        InlineKeyboardButton("⬅️ Back", callback_data="folders:1")
    ])
    
    return InlineKeyboardMarkup(buttons)

def file_actions_kb(file_id: str, folder_id: str):
    """File actions keyboard"""
    from config import config
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Watch Online", url=f"{config.BASE_APP_URL}/{file_id}")],
        [InlineKeyboardButton("⬇️ Download", url=f"{config.BASE_APP_URL}/dl/{file_id}")],
        [
            InlineKeyboardButton("✏️ Rename", callback_data=f"rename_file:{file_id}"),
            InlineKeyboardButton("🗑 Delete", callback_data=f"delete_file:{file_id}:{folder_id}")
        ],
        [InlineKeyboardButton("⬅️ Back to Folder", callback_data=f"folder:{folder_id}:1")]
    ])

def confirm_delete_kb(item_type: str, item_id: str, folder_id: str = None):
    """Confirmation keyboard for delete actions"""
    if item_type == "file":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes, Delete", callback_data=f"confirm_delete_file:{item_id}:{folder_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"file:{item_id}")]
        ])
    else:  # folder
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes, Delete All", callback_data=f"confirm_delete_folder:{item_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"folder:{item_id}:1")]
        ])