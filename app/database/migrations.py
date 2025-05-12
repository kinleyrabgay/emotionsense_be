import logging
from app.database.database import create_indexes_sync, sync_db, USERS_COLLECTION

logger = logging.getLogger(__name__)

def run_migrations():
    """
    Run MongoDB migrations to ensure proper setup
    """
    logger.info("Running MongoDB migrations")
    
    try:
        # Create indexes
        create_indexes_sync()
        
        # Ensure users have all the required fields
        update_user_schema()
        
        logger.info("MongoDB migrations completed successfully")
    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}")
        raise

def update_user_schema():
    """Update user documents to ensure they have all required fields"""
    try:
        # Set default values for any missing fields
        sync_db[USERS_COLLECTION].update_many(
            {"currentEmotion": {"$exists": False}},
            {"$set": {"currentEmotion": 4}}  # 4 = NEUTRAL in the enum
        )
        
        sync_db[USERS_COLLECTION].update_many(
            {"isFaceAuthEnabled": {"$exists": False}},
            {"$set": {"isFaceAuthEnabled": False}}
        )
        
        sync_db[USERS_COLLECTION].update_many(
            {"role": {"$exists": False}},
            {"$set": {"role": "employee"}}
        )
        
        sync_db[USERS_COLLECTION].update_many(
            {"emotionHistory": {"$exists": False}},
            {"$set": {"emotionHistory": []}}
        )
        
        # Convert any existing face_encoding fields
        users_with_face_encoding = sync_db[USERS_COLLECTION].find(
            {"face_encoding": {"$exists": True}}
        )
        
        for user in users_with_face_encoding:
            if user.get("face_encoding") and not user.get("isFaceAuthEnabled", False):
                sync_db[USERS_COLLECTION].update_one(
                    {"_id": user["_id"]},
                    {"$set": {"isFaceAuthEnabled": True}}
                )
        
        logger.info("User schema updated successfully")
    except Exception as e:
        logger.error(f"Error updating user schema: {str(e)}")
        raise 