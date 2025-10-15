from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📁 My Folders", callback_data="folders:1"),
            InlineKeyboardButton("➕ New Folder", callback_data="new_folder")
        ],
        [
            InlineKeyboardButton("📊 My Statistics", callback_data="stats"),
            InlineKeyboardButton("💾 Backup DB", callback_data="backup_menu")
        ],
        [
            InlineKeyboardButton("ℹ️ Help & Guide", callback_data="help"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings")
        ],
    ])

def folders_kb(folders: list, page: int, total_pages: int):
    buttons = []
    
    for folder in folders:
        name = folder['name']
        folder_id = folder['folderId']
        file_count = folder.get('fileCount', 0)
        subfolder_count = folder.get('subfolderCount', 0)
        
        label = f"📁 {name} ({file_count} files"
        if subfolder_count > 0:
            label += f", {subfolder_count} subfolders"
        label += ")"
        
        buttons.append([
            InlineKeyboardButton(label, callback_data=f"folder:{folder_id}:1")
        ])
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"folders:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"folders:{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(buttons)

def quality_selection_kb(folder_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 4K Ultra", callback_data=f"select_quality:{folder_id}:4K"),
            InlineKeyboardButton("📺 1080p HD", callback_data=f"select_quality:{folder_id}:1080p")
        ],
        [
            InlineKeyboardButton("📱 720p", callback_data=f"select_quality:{folder_id}:720p"),
            InlineKeyboardButton("💿 480p", callback_data=f"select_quality:{folder_id}:480p")
        ],
        [InlineKeyboardButton("📼 360p", callback_data=f"select_quality:{folder_id}:360p")],
        [InlineKeyboardButton("⬅️ Back to Folder", callback_data=f"folder:{folder_id}:1")]
    ])

def quality_folder_view_kb(parent_folder_id, quality_folders: list):
    buttons = []
    
    for qf in quality_folders:
        quality = qf['quality']
        file_count = qf.get('fileCount', 0)
        buttons.append([
            InlineKeyboardButton(
                f"🎥 {quality} ({file_count} files)",
                callback_data=f"quality_folder:{qf['folderId']}:1"
            )
        ])
    
    # New buttons for bulk links
    buttons.append([
        InlineKeyboardButton("🔗 All Embed Links", callback_data=f"all_embeds:{parent_folder_id}"),
    ])
    buttons.append([
        InlineKeyboardButton("⬇️ All Download Links", callback_data=f"all_downloads:{parent_folder_id}"),
    ])
    buttons.append([
        InlineKeyboardButton("▶️ All Watch Links", callback_data=f"all_watch:{parent_folder_id}"),
    ])
    
    buttons.append([
        InlineKeyboardButton("➕ Add Files", callback_data=f"add_files:{parent_folder_id}"),
        InlineKeyboardButton("✏️ Rename", callback_data=f"rename_folder:{parent_folder_id}")
    ])
    buttons.append([
        InlineKeyboardButton("🗑 Delete Folder", callback_data=f"delete_folder:{parent_folder_id}"),
        InlineKeyboardButton("⬅️ Back", callback_data="folders:1")
    ])
    
    return InlineKeyboardMarkup(buttons)

def folder_view_kb(folder_id, files: list, page: int, total_pages: int):
    buttons = []
    
    for file in files:
        file_id = file['fileId']
        name = file.get('fileName', 'Unnamed')
        size = file.get('size', 0)
        size_mb = size / (1024 * 1024) if size else 0
        quality = file.get('quality', 'Unknown')
        
        buttons.append([
            InlineKeyboardButton(
                f"🎬 {name} [{quality}] ({size_mb:.1f}MB)",
                callback_data=f"file:{file_id}"
            )
        ])
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"quality_folder:{folder_id}:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"quality_folder:{folder_id}:{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton("⬅️ Back to Parent", callback_data=f"folder:parent:1")])
    
    return InlineKeyboardMarkup(buttons)

def simplified_file_list_kb(folder_id, file_groups: list):
    buttons = []
    
    for group in file_groups:
        base_name = group['baseName']
        qualities = group.get('qualities', [])
        file_count = group.get('fileCount', 0)
        total_size = group.get('totalSize', 0)
        size_mb = total_size / (1024 * 1024)
        
        quality_str = ", ".join(sorted(qualities))
        
        buttons.append([
            InlineKeyboardButton(
                f"📦 {base_name} [{quality_str}] ({size_mb:.1f}MB)",
                callback_data=f"basename:{folder_id}:{base_name}"
            )
        ])
    
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data=f"folder:{folder_id}:1")])
    
    return InlineKeyboardMarkup(buttons)

def files_by_basename_kb(folder_id, base_name: str, files: list):
    buttons = []
    
    for file in files:
        file_id = file['fileId']
        quality = file.get('quality', 'Unknown')
        size = file.get('size', 0)
        size_mb = size / (1024 * 1024) if size else 0
        
        buttons.append([
            InlineKeyboardButton(
                f"🎥 {quality} ({size_mb:.1f}MB)",
                callback_data=f"file:{file_id}"
            )
        ])
    
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data=f"quality_folder:{folder_id}:1")])
    
    return InlineKeyboardMarkup(buttons)

def file_actions_kb(file_id: str, folder_id):
    from config import config
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Watch Online", url=f"{config.BASE_APP_URL}/watch/{file_id}")],
        [InlineKeyboardButton("⬇️ Download File", url=f"{config.BASE_APP_URL}/dl/{file_id}")],
        [InlineKeyboardButton("📋 Embed Link", url=f"{config.BASE_APP_URL}/{file_id}")],
        [
            InlineKeyboardButton("✏️ Rename", callback_data=f"rename_file:{file_id}"),
            InlineKeyboardButton("🗑 Delete", callback_data=f"delete_file:{file_id}:{folder_id}")
        ],
        [InlineKeyboardButton("⬅️ Back to Folder", callback_data=f"quality_folder:{folder_id}:1")]
    ])

def confirm_delete_kb(item_type: str, item_id: str, folder_id = None):
    if item_type == "file":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes, Delete", callback_data=f"confirm_delete_file:{item_id}:{folder_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"file:{item_id}")]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes, Delete All", callback_data=f"confirm_delete_folder:{item_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"folder:{item_id}:1")]
        ])