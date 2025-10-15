# ==================== check_webhook.py ====================
# Run this to check if your bot has a webhook set
# Usage: python check_webhook.py

import asyncio
from pyrogram import Client
from config import config

async def check_bot():
    bot = Client(
        name="temp_check",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN,
    )
    
    async with bot:
        # Get bot info
        me = await bot.get_me()
        print(f"✅ Bot: @{me.username}")
        print(f"✅ Bot ID: {me.id}")
        print(f"✅ Bot Name: {me.first_name}")
        
        # Try to get webhook info using raw API
        try:
            result = await bot.invoke(
                {"_": "getWebhookInfo"}
            )
            print(f"\n📡 Webhook Info:")
            print(f"URL: {result.get('url', 'None')}")
            print(f"Has Custom Certificate: {result.get('has_custom_certificate', False)}")
            print(f"Pending Update Count: {result.get('pending_update_count', 0)}")
            
            if result.get('url'):
                print(f"\n⚠️ WARNING: Webhook is set! This prevents long polling.")
                print(f"To delete webhook, run:")
                print(f"curl https://api.telegram.org/bot{config.BOT_TOKEN}/deleteWebhook")
        except Exception as e:
            print(f"ℹ️ Could not get webhook info: {e}")
            print(f"This is normal - bot is using long polling")
        
        # Test sending a message to yourself
        print(f"\n🧪 Testing message sending...")
        try:
            # Send test message to "Saved Messages"
            await bot.send_message("me", "✅ Bot is working! Send /start to your bot now.")
            print(f"✅ Successfully sent test message to your Saved Messages")
        except Exception as e:
            print(f"❌ Error sending message: {e}")

if __name__ == "__main__":
    asyncio.run(check_bot())