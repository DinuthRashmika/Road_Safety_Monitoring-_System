# app/utils/protective_alerts.py

import logging
from typing import Optional
import app.db.mongodb as mongodb
from app.models.protective_notification_model import protective_notification_doc

logger = logging.getLogger(__name__)

async def send_protective_alert_to_owner(
    *,
    owner: dict,
    near_plate: str,
    location: str,
    violation_id: Optional[str],
    violation_type: str,
    violation_image: Optional[str] = None,
) -> bool:
    """
    Save ONLY protective alerts into NEW collection: protective_alerts
    (NOT into notifications)
    """
    try:
        if mongodb.db is None or mongodb.db.db is None:
            logger.error("DB not connected, cannot save protective alert")
            return False

        database = mongodb.db.db

        owner_id = str(owner.get("id") or owner.get("_id"))
        if not owner_id:
            return False

        message = (
            f"Protective Alert: A traffic violation was detected near your vehicle at {location}. "
            f"Please drive carefully."
        )

        doc = protective_notification_doc(
            owner_id=owner_id,
            vehicle_plate=near_plate,          # ✅ nearby vehicle plate ONLY
            message=message,
            location=location,
            violation_id=violation_id,         # ✅ link to violation
            violation_type=violation_type,
            violation_image=violation_image,
        )

        # ✅ IMPORTANT: Insert into new collection ONLY
        await database.protective_alerts.insert_one(doc)

        logger.info(f"✅ Protective alert saved in protective_alerts for owner={owner_id} plate={near_plate}")
        return True

    except Exception as e:
        logger.error(f"❌ Protective alert failed: {e}")
        return False