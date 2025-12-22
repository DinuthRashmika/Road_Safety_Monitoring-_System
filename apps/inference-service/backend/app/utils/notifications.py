import logging
from datetime import datetime
import app.db.mongodb as mongodb
from app.models.notification_model import notification_doc
from bson import ObjectId

logger = logging.getLogger(__name__)

async def send_notification_to_owner(owner: dict, plate_number: str, 
                                     violation_type: str, fine_amount: float,
                                     detection_time: datetime, violation_id: str = None, 
                                     location: str = "Unknown"):
    """
    Creates an In-App Notification record in the database with detailed violation info.
    """
    try:
        # Check database connection
        if mongodb.db is None or mongodb.db.db is None:
            logger.error("Database not connected, cannot save notification")
            return False

        database = mongodb.db.db

        # 1. Construct a detailed message for the Mobile App
        message = f"You have been fined LKR {fine_amount} for '{violation_type}' at {location}."
        
        # Ensure violation_id is valid (create dummy if missing for some reason)
        v_id = violation_id if violation_id else str(ObjectId())

        # 2. Create the notification document
        notification = notification_doc(
            owner_id=owner['id'],
            vehicle_plate=plate_number,
            violation_id=v_id,
            message=message,
            location=location,
            violation_type=violation_type, # New field
            fine_amount=fine_amount        # New field
        )

        # 3. Insert into 'notifications' collection
        await database.notifications.insert_one(notification)
        
        logger.info(f"✅ Notification saved: {violation_type} (LKR {fine_amount}) for {plate_number}")
        
        # (Optional) Placeholders for future Email/SMS integration
        # await send_email(...) 
        
        return True

    except Exception as e:
        logger.error(f"❌ Failed to save notification: {e}")
        return False

# Placeholder functions to prevent import errors if referenced elsewhere
async def send_sms(phone_number: str, message: str) -> bool:
    pass

async def send_email(email: str, subject: str, message: str, attachment_base64: str = None) -> bool:
    pass