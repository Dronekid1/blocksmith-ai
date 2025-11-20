from fastapi import APIRouter, HTTPException, Request, Header
import os
import stripe

from services.supabase_client import get_supabase_client, update_user_credits

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

@router.post("/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        await handle_successful_payment(session)
    
    elif event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        print(f"Payment failed: {payment_intent['id']}")
    
    return {"status": "success"}

async def handle_successful_payment(session: dict):
    """Process successful payment and add credits"""
    metadata = session.get("metadata", {})
    
    user_id = metadata.get("user_id")
    package_id = metadata.get("package_id")
    credits = int(metadata.get("credits", 0))
    bonus_credits = int(metadata.get("bonus_credits", 0))
    
    if not user_id or credits == 0:
        print(f"Invalid payment metadata: {metadata}")
        return
    
    total_credits = credits + bonus_credits
    
    # Add credits to user
    supabase = get_supabase_client()
    
    # Get package name for description
    package_response = supabase.table("credit_packages")\
        .select("name")\
        .eq("id", package_id)\
        .single()\
        .execute()
    
    package_name = package_response.data["name"] if package_response.data else "Credit Package"
    
    # Update credits
    await update_user_credits(
        user_id,
        total_credits,
        "purchase",
        f"{package_name} - {total_credits} credits",
        stripe_payment_id=session["payment_intent"]
    )
    
    # Update total spent
    amount_paid = session["amount_total"] / 100  # Convert from cents
    
    profile_response = supabase.table("profiles")\
        .select("total_spent")\
        .eq("id", user_id)\
        .single()\
        .execute()
    
    current_spent = profile_response.data["total_spent"] if profile_response.data else 0
    
    supabase.table("profiles").update({
        "total_spent": current_spent + amount_paid
    }).eq("id", user_id).execute()
    
    print(f"Added {total_credits} credits to user {user_id}")
