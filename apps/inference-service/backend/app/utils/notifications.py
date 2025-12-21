import logging
from datetime import datetime
from app.core.config import settings
import app.db.mongodb as mongodb
from app.models.notification_model import notification_doc

logger = logging.getLogger(__name__)

async def send_notification_to_owner(owner: dict, plate_number: str, 
                                     detection_time: datetime, violation_id: str = None, 
                                     location: str = "Unknown"):
    """
    Creates an In-App Notification record in the database.
    The Mobile App will poll/fetch these records.
    """
    try:
        if mongodb.db is None or mongodb.db.db is None:
            logger.error("Database not connected, cannot save notification")
            return False

        database = mongodb.db.db

        # 1. Construct the message for the Mobile App
        short_message = f"Violation detected for {plate_number} at {location}."
        
        # 2. Create the document
        notification = notification_doc(
            owner_id=owner['id'],
            vehicle_plate=plate_number,
            violation_id=violation_id,
            message=short_message,
            location=location
        )

        # 3. Insert into 'notifications' collection
        await database.notifications.insert_one(notification)
        
        logger.info(f"✅ In-App Notification saved for Owner: {owner['name']} (Plate: {plate_number})")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to save notification: {e}")
        return False