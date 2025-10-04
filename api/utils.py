# ==================== api/utils.py ====================
from bot.client import get_bot
from pyrogram.errors import RPCError
from typing import AsyncGenerator

async def stream_file(file_id: str, start: int = 0, end: int = None) -> AsyncGenerator[bytes, None]:
    """
    Stream a file from Telegram in chunks.

    Args:
        file_id (str): Telegram file ID.
        start (int): Start byte.
        end (int | None): End byte (optional).

    Yields:
        bytes: Chunks of the file.
    """
    bot = get_bot()  # get current active bot instance
    try:
        # You may need to adjust based on how you want chunking; here's a generic example
        chunk_size = 1024 * 1024  # 1MB chunks
        offset = start

        while True:
            remaining = (end - offset) if end else chunk_size
            chunk = await bot.download_media(
                file_id,
                in_memory=True,
                file_size=min(chunk_size, remaining)
            )

            if not chunk:
                break

            yield chunk
            offset += len(chunk)
            if end and offset >= end:
                break

    except RPCError as e:
        print(f"[UTILS] Error streaming file {file_id}: {e}")
        raise

async def get_file_size(file_id: str) -> int:
    """
    Get the size of a Telegram file in bytes.

    Args:
        file_id (str): Telegram file ID.

    Returns:
        int: File size in bytes.
    """
    bot = get_bot()
    try:
        msg = await bot.get_messages(chat_id="me", message_ids=file_id)
        if msg and msg.document:
            return msg.document.file_size
        return 0
    except RPCError as e:
        print(f"[UTILS] Error getting file size for {file_id}: {e}")
        return 0
