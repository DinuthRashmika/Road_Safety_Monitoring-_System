async def send_notification_to_owner(
    owner: dict, 
    plate_number: str, 
    violation_type: str, 
    fine_amount: float,
    detection_time: datetime, 
    violation_id: str = None, 
    location: str = "Unknown",
    image_path: str = None # <--- NEW ARGUMENT
):
    """
    Creates an In-App Notification record in the database with detailed violation info.
    """
    try:
        if mongodb.db is None or mongodb.db.db is None:
            logger.error("Database not connected, cannot save notification")
            return False

        database = mongodb.db.db

        message = f"You have been fined LKR {fine_amount} for '{violation_type}' at {location}."
        v_id = violation_id if violation_id else str(ObjectId())

        # Create the notification document
        notification = notification_doc(
            owner_id=str(owner.get('id') or owner.get('_id')), # Handle both id formats
            vehicle_plate=plate_number,
            violation_id=v_id,
            message=message,
            location=location,
            violation_type=violation_type,
            fine_amount=fine_amount,
            violation_image=image_path # <--- Pass the image path
        )

        await database.notifications.insert_one(notification)
        
        logger.info(f"✅ Notification saved with Image: {violation_type} for {plate_number}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to save notification: {e}")
        return False