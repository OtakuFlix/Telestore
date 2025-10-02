# ==================== bot/client.py ====================
from pyrogram import Client
from config import config

bot = Client(
    name="telestore_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    workers=8,
    sleep_threshold=10,
)

# Import handlers after client creation
from bot.handlers import commands, callbacks, media