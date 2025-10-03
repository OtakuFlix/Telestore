# ==================== bot/client.py ====================
from pyrogram import Client
from config import config

# Create bot client - handlers will be registered when imported
bot = Client(
    name="telestore_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    workdir=".",
)

print("[BOT] Client instance created")