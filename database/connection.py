# ==================== database/connection.py ====================
from motor.motor_asyncio import AsyncIOMotorClient
from config import config

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

async def connect_db():
    """Connect to MongoDB"""
    try:
        db_instance.client = AsyncIOMotorClient(config.MONGODB_URI)
        db_instance.db = db_instance.client[config.MONGODB_DB]
        
        # Test connection
        await db_instance.client.admin.command('ping')
        print(f"[DATABASE] Connected to MongoDB: {config.MONGODB_DB}")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        print(f"[DATABASE] Failed to connect: {e}")
        raise

async def disconnect_db():
    """Disconnect from MongoDB"""
    if db_instance.client:
        db_instance.client.close()
        print("[DATABASE] Disconnected from MongoDB")

async def create_indexes():
    """Create database indexes for performance"""
    try:
        # Folders collection indexes
        await db_instance.db.folders.create_index("folderId", unique=True)
        await db_instance.db.folders.create_index("createdBy")
        await db_instance.db.folders.create_index([("createdBy", 1), ("createdAt", -1)])
        
        # Files collection indexes
        await db_instance.db.files.create_index("fileId", unique=True)
        await db_instance.db.files.create_index("folderId")
        await db_instance.db.files.create_index("telegramFileId")
        await db_instance.db.files.create_index([("folderId", 1), ("uploadedAt", -1)])
        
        print("[DATABASE] Indexes created successfully")
    except Exception as e:
        print(f"[DATABASE] Error creating indexes: {e}")

def get_database():
    """Get database instance"""
    return db_instance.db