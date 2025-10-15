from pyrogram import filters
from pyrogram.types import Message
from database.backup import export_database, import_database, log_change
from database.connection import get_database
from config import config
import os

user_waiting_for_json = {}

def register_backup_handlers(bot):
    
    @bot.on_message(filters.command("vanish") & filters.private)
    async def vanish_command(client, message: Message):
        user_id = message.from_user.id
        status_msg = await message.reply_text("🔄 **Exporting database...**")

        try:
            json_file = await export_database()
            if not os.path.exists(json_file):
                await status_msg.edit_text("❌ Failed to create backup file.")
                return

            file_size = os.path.getsize(json_file) / (1024 * 1024)

            await status_msg.edit_text(f"📤 **Uploading backup...**\n💾 Size: {file_size:.2f} MB")

            caption = (
                f"📦 **Database Backup**\n"
                f"📅 Date: {status_msg.date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"💾 Size: {file_size:.2f} MB\n"
                f"👤 Requested by: {message.from_user.first_name} ({user_id})\n\n"
                f"Use `/retrieve` to restore this backup later."
            )

            # Send backup to main channel if defined
            if config.CHANNEL_ID:
                await client.send_document(
                    chat_id=config.CHANNEL_ID,
                    document=json_file,
                    caption=caption
                )

            # Send backup to user personally
            await client.send_document(
                chat_id=message.chat.id,
                document=json_file,
                caption="✅ **Backup created successfully!**\n\n"
                        "📁 File saved.\n\n"
                        "⚠️ The database will now be **wiped clean**.\n"
                        "You can restore anytime using `/retrieve`."
            )

            # Proceed to database cleanup
            await status_msg.edit_text("⚠️ **Formatting database... Please wait...**")

            db = get_database()
            collections = await db.list_collection_names()

            for collection_name in collections:
                collection = db[collection_name]
                delete_result = await collection.delete_many({})
                print(f"[VANISH] Cleared {delete_result.deleted_count} documents from '{collection_name}'")

            await status_msg.edit_text("🧹 **Database has been wiped clean!**\n\n✅ Backup was sent to you.")
            print("[VANISH] Database successfully formatted.")

            os.remove(json_file)
            print(f"[BACKUP] Backup file deleted: {json_file}")

        except Exception as e:
            print(f"[VANISH] Error: {e}")
            await status_msg.edit_text(f"❌ Error during vanish: {str(e)}")

    @bot.on_message(filters.command("retrieve") & filters.private)
    async def retrieve_command(client, message: Message):
        user_id = message.from_user.id
        user_waiting_for_json[user_id] = True
        
        await message.reply_text(
            "📥 **Database Restore**\n\n"
            "Please send me the JSON backup file.\n\n"
            "⚠️ **Warning:** This will import data into the current database.\n"
            "Existing data will not be deleted, but duplicates will be skipped.\n\n"
            "Send /cancel to abort."
        )
    
    @bot.on_message(filters.command("cancel") & filters.private)
    async def cancel_command(client, message: Message):
        user_id = message.from_user.id
        if user_id in user_waiting_for_json:
            del user_waiting_for_json[user_id]
            await message.reply_text("❌ Operation cancelled.")
        else:
            await message.reply_text("No operation to cancel.")
    
    @bot.on_message(filters.document & filters.private, group=1)
    async def handle_json_upload(client, message: Message):
        user_id = message.from_user.id
        
        if user_id not in user_waiting_for_json:
            return
        
        message.continue_propagation = False
        
        document = message.document
        
        if not document.file_name.endswith('.json'):
            await message.reply_text("❌ Please send a valid JSON file.")
            return
        
        status_msg = await message.reply_text("📥 **Downloading backup file...**")
        
        try:
            file_path = await message.download()
            
            await status_msg.edit_text("🔄 **Importing database...**")
            
            result = await import_database(file_path)
            
            if result['success']:
                response = (
                    f"✅ **Database Import Complete!**\n\n"
                    f"📁 Folders imported: {result['folders_imported']}\n"
                    f"📁 Folders skipped: {result['folders_skipped']}\n"
                    f"🎬 Files imported: {result['files_imported']}\n"
                    f"🎬 Files skipped: {result['files_skipped']}\n\n"
                    f"Total: {result['total_folders']} folders, {result['total_files']} files"
                )
                
                if config.LOGS_CHANNEL_ID:
                    log_file = await log_change(
                        operation='restore',
                        collection='database',
                        data=result
                    )
                    
                    if os.path.exists(log_file):
                        await client.send_document(
                            chat_id=config.LOGS_CHANNEL_ID,
                            document=log_file,
                            caption=f"📝 Database restore by {message.from_user.first_name} ({user_id})"
                        )
                        os.remove(log_file)
                
                await status_msg.edit_text(response)
            else:
                await status_msg.edit_text("❌ Import failed. Check logs for details.")
            
            os.remove(file_path)
            print(f"[BACKUP] Downloaded file deleted: {file_path}")
            
            del user_waiting_for_json[user_id]
            
        except Exception as e:
            print(f"[BACKUP] Import error: {e}")
            await status_msg.edit_text(f"❌ Error importing database: {str(e)}")
            
            if user_id in user_waiting_for_json:
                del user_waiting_for_json[user_id]