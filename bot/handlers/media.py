from pyrogram import filters
from pyrogram.types import Message
from bot.client import get_bot
from database.operations import add_file_to_folder, get_folder_by_id
from config import config
import re
import secrets
import string

# ---------------------- USER FOLDER CONTEXT ----------------------
user_folder_context = {}

def set_user_folder_context(user_id: int, folder_id: str):
    user_folder_context[user_id] = folder_id

def clear_user_folder_context(user_id: int):
    user_folder_context.pop(user_id, None)

def get_user_folder_context(user_id: int) -> str:
    return user_folder_context.get(user_id)

# ---------------------- HELPER FUNCTIONS ----------------------
def extract_quality(filename: str) -> str:
    quality_patterns = [
        r'\b(4320p|2160p|1440p|1080p|720p|480p|360p|240p)\b',
        r'\b(4K|2K|HD|FHD|UHD|8K)\b',
    ]
    for pattern in quality_patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return None

def extract_language(filename: str) -> str:
    language_patterns = {
        r'\b(Hindi|Tamil|Telugu|Malayalam|Kannada|Bengali|Marathi|Gujarati|Punjabi)\b': lambda m: m.group(1),
        r'\b(English|Eng)\b': lambda m: 'English',
        r'\b(Dual Audio|Multi Audio)\b': lambda m: 'Multi Audio',
    }
    for pattern, extractor in language_patterns.items():
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            return extractor(match)
    return None

# ---------------------- MEDIA HANDLERS ----------------------
async def handle_media(client, message: Message):
    user_id = message.from_user.id
    folder_id = get_user_folder_context(user_id)
    
    if not folder_id:
        await message.reply_text(
            "📤 To save this file:\n\n"
            "1. First create a folder: /newfolder <name>\n"
            "2. Open the folder from /myfolders\n"
            "3. Click 'Add Files'\n"
            "4. Send your media files"
        )
        return
    
    try:
        # Video
        if message.video:
            media = message.video
            file_name = media.file_name or "video.mp4"
            file_id = media.file_id
            file_unique_id = media.file_unique_id
            mime_type = media.mime_type
            file_size = media.file_size
            duration = media.duration
            thumbnail = media.thumbs[0].file_id if media.thumbs else None
        # Document
        elif message.document:
            media = message.document
            file_name = media.file_name or "document"
            file_id = media.file_id
            file_unique_id = media.file_unique_id
            mime_type = media.mime_type
            file_size = media.file_size
            duration = None
            thumbnail = None
        else:
            await message.reply_text("❌ Unsupported file type.")
            return
        
        quality = extract_quality(file_name)
        language = extract_language(file_name)
        file_unique_id = media.file_unique_id
        
        file_doc = {
            'fileId': file_unique_id,
            'telegramFileId': file_id,
            'telegramFileUniqueId': file_unique_id,
            'fileName': file_name,
            'mimeType': mime_type,
            'size': file_size,
            'folderId': folder_id,
            'caption': message.caption,
            'quality': quality,
            'language': language,
            'duration': duration,
            'thumbnail': thumbnail,
        }
        
        inserted = await add_file_to_folder(file_doc, user_id)
        if not inserted:
            await message.reply_text("⚠️ This file is already saved in the selected folder.")
            return
        
        size_mb = file_size / (1024 * 1024) if file_size else 0
        stream_url = f"{config.BASE_APP_URL}/{file_unique_id}"
        download_url = f"{config.BASE_APP_URL}/dl/{file_unique_id}"
        
        response = (
            f"✅ **File Added Successfully!**\n\n"
            f"📄 **Name:** {file_name}\n"
            f"💾 **Size:** {size_mb:.2f} MB\n"
        )
        if quality:
            response += f"🎥 **Quality:** {quality}\n"
        if language:
            response += f"🗣 **Language:** {language}\n"
        if duration:
            mins, secs = divmod(duration, 60)
            response += f"⏱ **Duration:** {mins}m {secs}s\n"
        
        response += (
            f"\n🔗 **Links:**\n"
            f"▶️ Watch: `{stream_url}`\n"
            f"⬇️ Download: `{download_url}`\n\n"
            f"Send more files or use /done when finished."
        )
        
        await message.reply_text(response)
        
    except Exception as e:
        print(f"Error handling media: {e}")
        await message.reply_text("❌ Failed to save file. Please try again.")

async def done_adding_files(client, message: Message):
    user_id = message.from_user.id
    folder_id = user_folder_context.pop(user_id, None)
    
    if folder_id:
        folder = await get_folder_by_id(folder_id)
        await message.reply_text(
            f"✅ Finished adding files to **{folder['name']}**\n\n"
            f"Use /myfolders to view your folders."
        )
    else:
        await message.reply_text("You weren't adding files to any folder.")

# ---------------------- HANDLER REGISTRATION ----------------------
def register_media_handlers(bot):
    """Register media handlers on the bot instance"""
    bot.on_message(filters.private & (filters.video | filters.document))(handle_media)
    bot.on_message(filters.private & filters.command("done"))(done_adding_files)
