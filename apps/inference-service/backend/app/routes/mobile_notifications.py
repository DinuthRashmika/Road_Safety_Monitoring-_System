from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel
from datetime import datetime
import app.db.mongodb as mongodb
from app.core.deps import get_current_owner

router = APIRouter(prefix="/api/notifications", tags=["Mobile App Notifications"])


# --- Schemas for API Response ---
class NotificationOut(BaseModel):
    id: str
    vehiclePlate: str
    message: str
    location: str
    isRead: bool
    createdAt: datetime
    violationId: str

    # ✅ added fields
    type: Optional[str] = None
    violationType: Optional[str] = None
    fineAmount: Optional[float] = None
    violationImage: Optional[str] = None


# --- Endpoints ---

@router.get("/", response_model=List[NotificationOut])
async def get_my_notifications(
    current_user=Depends(get_current_owner),
    limit: int = 20
):
    """
    Mobile App: Fetch notifications for the logged-in owner.
    Sorts by newest first.
    """
    if mongodb.db is None or mongodb.db.db is None:
        raise HTTPException(500, "Database error")

    database = mongodb.db.db
    notifications = []

    try:
        # Find notifications where ownerId matches the logged-in user
        cursor = database.notifications.find(
            {"ownerId": current_user["_id"]}
        ).sort("createdAt", -1).limit(limit)

        async for notif in cursor:
            notifications.append({
                "id": str(notif["_id"]),
                "vehiclePlate": notif.get("vehiclePlate", ""),
                "message": notif.get("message", ""),
                "location": notif.get("location", "Unknown"),
                "isRead": notif.get("isRead", False),
                "createdAt": notif.get("createdAt"),
                "violationId": str(notif.get("violationId", "")),

                # ✅ added fields for violation details page
                "type": notif.get("type", ""),
                "violationType": notif.get("violationType"),
                "fineAmount": float(notif["fineAmount"]) if notif.get("fineAmount") is not None else None,
                "violationImage": notif.get("violationImage"),
            })
    except Exception as e:
        raise HTTPException(500, f"Error retrieving notifications: {str(e)}")

    return notifications


@router.put("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user=Depends(get_current_owner)
):
    """
    Mobile App: Call this when user taps the notification to mark it as 'Read'.
    """
    if mongodb.db is None or mongodb.db.db is None:
        raise HTTPException(500, "Database error")

    database = mongodb.db.db

    try:
        result = await database.notifications.update_one(
            {
                "_id": ObjectId(notification_id),
                "ownerId": current_user["_id"]  # Security: ensure owner owns this notif
            },
            {"$set": {"isRead": True}}
        )

        if result.modified_count == 0:
            # Check if it exists but just belongs to someone else
            doc = await database.notifications.find_one({"_id": ObjectId(notification_id)})
            if not doc:
                raise HTTPException(404, "Notification not found")
            if doc["ownerId"] != current_user["_id"]:
                raise HTTPException(403, "Not authorized to access this notification")

        return {"success": True}
    except Exception as e:
        raise HTTPException(400, f"Invalid request: {str(e)}")