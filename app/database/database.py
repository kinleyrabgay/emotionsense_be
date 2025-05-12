import os
from dotenv import load_dotenv
import motor.motor_asyncio
from pymongo import MongoClient
import logging
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Get database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017/emotion_detection")

# Set default database name if not in connection string
def get_database_name(connection_string):
    """Extract database name from connection string or use default"""
    parsed_url = urlparse(connection_string)
    path = parsed_url.path.strip('/')
    
    # If no database name in URL, use a default
    if not path:
        return "emotionsense"
    
    return path

# Get database name
DB_NAME = get_database_name(DATABASE_URL)
logger.info(f"Using database: {DB_NAME}")

# MongoDB connection settings with SSL certificate verification disabled
# This is for development only - use proper certificate verification in production
mongo_settings = {
    "tlsAllowInvalidCertificates": True,  # Disable SSL certificate verification
    "retryWrites": True,
    "w": "majority"
}

# MongoDB clients
client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URL, **mongo_settings)
db = client[DB_NAME]

# Sync client for non-async operations
sync_client = MongoClient(DATABASE_URL, **mongo_settings)
sync_db = sync_client[DB_NAME]

# Collection names
USERS_COLLECTION = "users"
EMOTIONS_COLLECTION = "emotions"

async def create_indexes():
    """Create indexes for MongoDB collections"""
    try:
        # Create indexes for users collection
        await db[USERS_COLLECTION].create_index("email", unique=True)
        
        # Create indexes for emotions collection
        await db[EMOTIONS_COLLECTION].create_index("userId")
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {str(e)}")

def create_indexes_sync():
    """Create indexes for MongoDB collections (sync version)"""
    try:
        # Create indexes for users collection
        sync_db[USERS_COLLECTION].create_index("email", unique=True)
        
        # Create indexes for emotions collection
        sync_db[EMOTIONS_COLLECTION].create_index("userId")
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {str(e)}")

def create_tables():
    """Legacy function that now ensures MongoDB indexes are created"""
    create_indexes_sync()

# Helper functions for database operations
async def find_one(collection, query):
    """Find a single document in the specified collection"""
    return await db[collection].find_one(query)

async def find(collection, query, projection=None, sort=None, limit=None):
    """Find documents in the specified collection"""
    cursor = db[collection].find(query, projection)
    
    if sort:
        cursor = cursor.sort(sort)
    
    if limit:
        cursor = cursor.limit(limit)
    
    return await cursor.to_list(length=None)

async def insert_one(collection, document):
    """Insert a document into the specified collection"""
    result = await db[collection].insert_one(document)
    return result.inserted_id

async def update_one(collection, query, update):
    """Update a document in the specified collection"""
    result = await db[collection].update_one(query, update)
    return result

async def delete_one(collection, query):
    """Delete a document from the specified collection"""
    result = await db[collection].delete_one(query)
    return result

# Legacy method for backward compatibility
def get_db():
    """Legacy function for SQLAlchemy dependency injection pattern"""
    logger.warning("get_db() is deprecated with MongoDB. Use direct database functions instead.")
    return None