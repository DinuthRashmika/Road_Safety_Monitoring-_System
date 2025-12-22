import stripe
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.core.config import settings
from app.db.mongodb import get_database
from bson import ObjectId

router = APIRouter(prefix="/api/payments", tags=["Payments"])

# Initialize Stripe (Get this key from dashboard.stripe.com)
stripe.api_key = "sk_test_51ShA9KBSOx34RK9GAbFBNMBbjdyg1CgKDRtmwoE9iVBI1Lqx6Lc1WVhPa2soy6CzQiSElJTekcvOBg6vLGHPopeg00yvcmcmF9" # REPLACE WITH YOUR STRIPE SECRET KEY

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
        # Stripe expects amounts in the smallest currency unit (cents/rupee cents)
        # e.g., 100.00 LKR becomes 10000
        amount_in_cents = int(data.amount * 100)

        intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency=data.currency,
            payment_method_types=["card"],
        )
        
        return {"clientSecret": intent['client_secret']}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/confirm-violation-payment/{violation_id}")
async def confirm_violation_payment(violation_id: str):
    """
    Updates the violation status to PAID in the database.
    """
    db = get_database()
    try:
        # Update Violation Collection
        await db.violations.update_one(
            {"_id": ObjectId(violation_id)},
            {"$set": {"isPaid": True, "paidAt": datetime.utcnow()}}
        )
        
        # Also Update Notification to mark as processed/paid
        # (Optional, depending on your logic)
        
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))