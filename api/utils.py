# ==================== api/utils.py ====================
from bot.client import bot
from pyrogram.errors import RPCError
from typing import AsyncGenerator

async def stream_file(file_id: str, start: int = 0, end: int = None) -> AsyncGenerator[bytes, None]:
    """Stream file from Telegram in chunks"""
    try:
        async for chunk in bot.stream_media(file_id, offset=start, limit=end):
            yield chunk
    except RPCError as e:
        print(f"Error streaming file: {e}")
        raise

async def get_file_size(file_id: str) -> int:
    """Get file size from Telegram"""
    try:
        file = await bot.get_messages(chat_id="me", message_ids=1)
        # This is a placeholder - actual implementation depends on how you store message_id
        return 0
    except Exception as e:
        print(f"Error getting file size: {e}")
        return 0