from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.core.config import settings
from app.db.mongodb import get_database
from bson import ObjectId
from datetime import datetime

try:
    import stripe
except ImportError:
    stripe = None

router = APIRouter(prefix="/api/payments", tags=["Payments"])

if stripe and settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentIntentRequest(BaseModel):
    amount: float
    currency: str = "lkr"

@router.post("/create-payment-intent")
async def create_payment_intent(data: PaymentIntentRequest):
    """
    Creates a PaymentIntent on Stripe servers and returns the client_secret
    to the Flutter app.
    """
    try:
        if stripe is None:
            raise HTTPException(
                status_code=503,
                detail="Stripe package is not installed. Run: pip install stripe",
            )
        if not settings.STRIPE_SECRET_KEY:
            raise HTTPException(
                status_code=503,
                detail="STRIPE_SECRET_KEY is not configured.",
            )

        # Stripe expects amounts in the smallest currency unit (e.g., cents).
        # For LKR, we multiply by 100.
        amount_in_cents = int(data.amount * 100)

        intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency=data.currency,
            # 'automatic_payment_methods' enabled is usually recommended for mobile sheets
            automatic_payment_methods={"enabled": True},
        )
        
        return {"clientSecret": intent['client_secret']}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Stripe Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/confirm-violation-payment/{violation_id}")
async def confirm_violation_payment(violation_id: str):
    """
    Updates the violation status to PAID in the database.
    """
    db = get_database()
    try:
        # Update Violation Collection
        result = await db.violations.update_one(
            {"_id": ObjectId(violation_id)},
            {"$set": {"isPaid": True, "paidAt": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
             print(f"Warning: Violation {violation_id} matched no documents or was already paid.")

        return {"success": True}
    except Exception as e:
        print(f"DB Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
