# ==================== database/connection.py ====================
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import OperationFailure
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
        # Drop legacy unique index that referenced the deprecated fileId field
        try:
            await db_instance.db.files.drop_index("fileId_1")
            print("[DATABASE] Dropped legacy fileId index")
        except OperationFailure as drop_error:
            if "index not found" not in str(drop_error):
                print(f"[DATABASE] Unexpected error dropping fileId index: {drop_error}")
                raise
        except Exception as drop_error:
            print(f"[DATABASE] Error dropping legacy indexes: {drop_error}")
            raise
        
        # Folders collection indexes
        await db_instance.db.folders.create_index("folderId", unique=True)
        await db_instance.db.folders.create_index("createdBy")
        await db_instance.db.folders.create_index([("createdBy", 1), ("createdAt", -1)])
        
        # Files collection indexes
        await db_instance.db.files.create_index([("folderId", 1), ("telegramFileUniqueId", 1)], unique=True)
        await db_instance.db.files.create_index("folderId")
        await db_instance.db.files.create_index("telegramFileId")
        await db_instance.db.files.create_index([("folderId", 1), ("uploadedAt", -1)])
        
        # ==================== New Indexes ====================
        # Quality folder indexes
        await db_instance.db.folders.create_index([("parentFolderId", 1), ("isQualityFolder", 1), ("quality", 1)])
        
        # Base name and quality group indexes
        await db_instance.db.files.create_index("baseName")
        await db_instance.db.files.create_index([("folderId", 1), ("baseName", 1)])
        await db_instance.db.files.create_index([("baseName", 1), ("quality", 1)])
        
        print("[DATABASE] Indexes created successfully")
    except Exception as e:
        print(f"[DATABASE] Error creating indexes: {e}")

def get_database():
    """Get database instance"""
    return db_instance.db
