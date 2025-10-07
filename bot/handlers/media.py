# ==================== bot/handlers/media.py ====================
from pyrogram import filters
from pyrogram.types import Message
from bot.client import get_bot
from database.operations import add_file_to_folder, get_folder_by_id
from config import config
import re

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
    """Handle incoming media files"""
    user_id = message.from_user.id
    folder_id = get_user_folder_context(user_id)
    
    if not folder_id:
        await message.reply_text(
            "📤 To save this file:\n\n"
            "1. First create a folder: /newfolder <n>\n"
            "2. Open the folder from /myfolders\n"
            "3. Click 'Add Files'\n"
            "4. Send your media files"
        )
        return
    
    try:
        # Get folder info
        folder = await get_folder_by_id(folder_id)
        if not folder:
            await message.reply_text("❌ Folder not found!")
            return
        
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
        
        # Extract metadata
        quality = extract_quality(file_name)
        language = extract_language(file_name)
        
        # Prepare file document (NO custom fileId - MongoDB will generate _id)
        file_doc = {
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
        
        # Save to database - returns dict with documentId and inserted flag
        insert_result = await add_file_to_folder(file_doc, user_id)
        if not insert_result:
            await message.reply_text("⚠️ Failed to save file.")
            return
        
        if not insert_result.get('inserted', False):
            await message.reply_text("⚠️ This file already exists in this folder.")
            return
        
        mongo_id = insert_result.get('documentId')
        if not mongo_id:
            await message.reply_text("⚠️ Failed to save file.")
            return
        
        # Forward to backup channel with metadata caption
        try:
            bot = get_bot()
            
            # Create detailed caption for channel
            channel_caption = (
                f"📁 **Folder:** {folder['name']}\n"
                f"🆔 **Folder ID:** `{folder_id}`\n"
                f"🎬 **File ID:** `{mongo_id}`\n"
                f"📄 **File Name:** {file_name}\n"
            )
            
            if quality:
                channel_caption += f"🎥 **Quality:** {quality}\n"
            if language:
                channel_caption += f"🗣️ **Language:** {language}\n"
            if file_size:
                size_mb = file_size / (1024 * 1024)
                channel_caption += f"💾 **Size:** {size_mb:.2f} MB\n"
            if duration:
                mins = duration // 60
                secs = duration % 60
                channel_caption += f"⏱️ **Duration:** {mins}m {secs}s\n"
            
            # Add streaming links
            watch_url = f"{config.BASE_APP_URL}/watch/{mongo_id}"
            stream_url = f"{config.BASE_APP_URL}/{mongo_id}"
            download_url = f"{config.BASE_APP_URL}/dl/{mongo_id}"
            
            channel_caption += (
                f"\n🔗 **Links:**\n"
                f"▶️ Watch: {watch_url}\n"
                f"📥 Stream: {stream_url}\n"
                f"⬇️ Download: {download_url}\n"
                f"\n👤 **Uploaded by:** {message.from_user.first_name} ({user_id})"
            )
            
            # Forward message to channel
            await bot.copy_message(
                chat_id=config.CHANNEL_ID,
                from_chat_id=message.chat.id,
                message_id=message.id,
                caption=channel_caption
            )
            
            print(f"[MEDIA] File forwarded to channel: {file_name}")
            
        except Exception as e:
            print(f"[MEDIA] Error forwarding to channel: {e}")
            # Don't fail the upload if channel forward fails
        
        # Generate URLs for user (using MongoDB _id)
        watch_url = f"{config.BASE_APP_URL}/watch/{mongo_id}"
        stream_url = f"{config.BASE_APP_URL}/{mongo_id}"
        download_url = f"{config.BASE_APP_URL}/dl/{mongo_id}"
        
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
            f"📥 Stream: `{stream_url}`\n"
            f"⬇️ Download: `{download_url}`\n\n"
            f"Send more files or use /done when finished."
        )
        
        await message.reply_text(response)
        
    except Exception as e:
        print(f"[MEDIA] Error handling media: {e}")
        await message.reply_text("❌ Failed to save file. Please try again.")

async def done_adding_files(client, message: Message):
    """Exit add files mode"""
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