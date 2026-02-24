from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None
    connected = False

db = Database()

async def connect_to_mongo():
    """Connect to MongoDB"""
    logger.info("Connecting to MongoDB...")
    try:
        # Connect to MongoDB
        db.client = AsyncIOMotorClient(settings.MONGODB_URI)
        db.db = db.client.get_database(settings.MONGODB_DB)
        db.connected = True
        
        # Test connection
        await db.client.admin.command('ping')
        
        logger.info(f"Connected to MongoDB database: {settings.MONGODB_DB}")
        
        # Get collections to verify
        collections = await db.db.list_collection_names()
        logger.info(f"Available collections: {collections}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        db.connected = False
        return False

async def close_mongo_connection():
    """Close MongoDB connection"""
    logger.info("Closing MongoDB connection...")
    if db.client:
        db.client.close()
        db.connected = False
        logger.info("MongoDB connection closed")

def get_database():
    """Get database instance"""
    return db.db

def is_connected():
    """Check if database is connected"""
    return db.connected