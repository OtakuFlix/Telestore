# ==================== bot/client.py ====================
from pyrogram import Client
from config import config

# Global bot variable (will be set by main.py)
bot = None

def create_bot():
    """Create and return bot client instance"""
    return Client(
        name="telestore_bot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN,
        workdir=".",
        sleep_threshold=60,
    )

def set_bot(client):
    """Set the global bot instance"""
    global bot
    bot = client
    print("[BOT] Client instance set globally")

def get_bot():
    """Get the global bot instance"""
    if bot is None:
        raise RuntimeError("Bot not initialized. Call set_bot() first.")
    return bot