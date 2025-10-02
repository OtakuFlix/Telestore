from pyrogram import filters
from pyrogram.types import Message
from bot.client import bot
from database.operations import add_file_to_folder, get_folder_by_id
from config import config
import re

# Store temporary folder context (in production, use Redis or similar)
user_folder_context = {}

@bot.on_message(filters.private & (filters.video | filters.document))
async def handle_media(client, message: Message):
    """Handle incoming media files"""
    user_id = message.from_user.id
    
    # Check if user is in "add files" mode
    folder_id = user_folder_context.get(user_id)
    
    if not folder_id:
        await message.reply_text(
            "📤 To save this file:\n\n"
            "1. First create a folder: /newfolder <n>\n"
            "2. Open the folder from /myfolders\n"
            "3. Click 'Add Files'\n"
            "4. Send your media files"
        )
        return
    
    # Process the media
    try:
        # Extract file information
        if message.video:
            media = message.video
            file_id = media.file_id
            file_unique_id = media.file_unique_id
            file_name = media.file_name or "video.mp4"
            mime_type = media.mime_type
            file_size = media.file_size
            duration = media.duration
            width = media.width
            height = media.height
            thumbnail = media.thumbs[0].file_id if media.thumbs else None
            
        elif message.document:
            media = message.document
            file_id = media.file_id
            file_unique_id = media.file_unique_id
            file_name = media.file_name or "document"
            mime_type = media.mime_type
            file_size = media.file_size
            thumbnail = media.thumbs[0].file_id if media.thumbs else None
            duration = None
            width = None
            height = None
        else:
            await message.reply_text("❌ Unsupported file type.")
            return
        
        # Extract quality from filename if present
        quality = extract_quality(file_name)
        
        # Extract language from filename if present
        language = extract_language(file_name)
        
        # Generate unique file ID (12 characters alphanumeric)
        import secrets
        import string
        unique_file_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        # Save to database
        file_doc = {
            'fileId': unique_file_id,  # Our unique ID for URLs
            'telegramFileId': file_id,  # Telegram's file_id for downloading
            'telegramFileUniqueId': file_unique_id,
            'fileName': file_name,
            'mimeType': mime_type,
            'size': file_size,
            'folderId': folder_id,
            'caption': message.caption,
            'quality': quality,
            'language': language,
            'duration': duration,
            'width': width,
            'height': height,
            'thumbnail': thumbnail,
        }
        
        await add_file_to_folder(file_doc, user_id)
        
        # Generate URLs
        watch_url = f"{config.BASE_APP_URL}/{unique_file_id}"
        download_url = f"{config.BASE_APP_URL}/dl/{unique_file_id}"
        
        size_mb = file_size / (1024 * 1024) if file_size else 0
        
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
            mins = duration // 60
            secs = duration % 60
            response += f"⏱ **Duration:** {mins}m {secs}s\n"
        
        response += (
            f"\n🔗 **Links:**\n"
            f"▶️ Watch: `{watch_url}`\n"
            f"⬇️ Download: `{download_url}`\n\n"
            f"Send more files or use /done when finished."
        )
        
        await message.reply_text(response)
        
    except Exception as e:
        print(f"Error handling media: {e}")
        await message.reply_text(
            "❌ Failed to save file. Please try again.",
        )

@bot.on_message(filters.command("done") & filters.private)
async def done_adding_files(client, message: Message):
    """Exit add files mode"""
    user_id = message.from_user.id
    
    if user_id in user_folder_context:
        folder_id = user_folder_context.pop(user_id)
        folder = await get_folder_by_id(folder_id)
        
        await message.reply_text(
            f"✅ Finished adding files to **{folder['name']}**\n\n"
            f"Use /myfolders to view your folders."
        )
    else:
        await message.reply_text("You weren't adding files to any folder.")

def extract_quality(filename: str) -> str:
    """Extract video quality from filename"""
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
    """Extract language from filename"""
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

# Context manager functions
def set_user_folder_context(user_id: int, folder_id: str):
    """Set folder context for user"""
    user_folder_context[user_id] = folder_id

def clear_user_folder_context(user_id: int):
    """Clear folder context for user"""
    user_folder_context.pop(user_id, None)

def get_user_folder_context(user_id: int) -> str:
    """Get folder context for user"""
    return user_folder_context.get(user_id)