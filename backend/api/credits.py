from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import os
import stripe

from services.supabase_client import (
    get_user_from_token,
    get_user_profile,
    get_supabase_client
)

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class CheckoutRequest(BaseModel):
    package_id: str
    success_url: str
    cancel_url: str

@router.get("/packages")
async def get_credit_packages():
    """Get available credit packages"""
    supabase = get_supabase_client()
    
    response = supabase.table("credit_packages")\
        .select("*")\
        .eq("is_active", True)\
        .order("sort_order")\
        .execute()
    
    return {"packages": response.data}

@router.get("/balance")
async def get_credit_balance(authorization: str = Header(...)):
    """Get user's current credit balance"""
    try:
        user = await get_user_from_token(authorization)
        profile = await get_user_profile(user.id)
        
        return {
            "credits": profile["credits"],
            "total_spent": profile["total_spent"]
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/checkout")
async def create_checkout_session(
    request: CheckoutRequest,
    authorization: str = Header(...)
):
    """Create Stripe checkout session for credit purchase"""
    try:
        user = await get_user_from_token(authorization)
        supabase = get_supabase_client()
        
        # Get package details
        package_response = supabase.table("credit_packages")\
            .select("*")\
            .eq("id", request.package_id)\
            .eq("is_active", True)\
            .single()\
            .execute()
        
        if not package_response.data:
            raise HTTPException(status_code=404, detail="Package not found")
        
        package = package_response.data
        
        # Get or create Stripe customer
        customer_response = supabase.table("stripe_customers")\
            .select("stripe_customer_id")\
            .eq("user_id", user.id)\
            .single()\
            .execute()
        
        if customer_response.data:
            customer_id = customer_response.data["stripe_customer_id"]
        else:
            # Create new Stripe customer
            profile = await get_user_profile(user.id)
            customer = stripe.Customer.create(
                metadata={
                    "user_id": user.id,
                    "discord_username": profile.get("discord_username", "")
                }
            )
            customer_id = customer.id
            
            # Save to database
            supabase.table("stripe_customers").insert({
                "user_id": user.id,
                "stripe_customer_id": customer_id
            }).execute()
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"{package['name']} - {package['credits'] + package['bonus_credits']} Credits",
                        "description": f"BlockSmith AI Credits Package"
                    },
                    "unit_amount": package["price_cents"]
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                "user_id": user.id,
                "package_id": request.package_id,
                "credits": package["credits"],
                "bonus_credits": package["bonus_credits"]
            }
        )
        
        return {
            "checkout_url": session.url,
            "session_id": session.id
        }
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_purchase_history(
    authorization: str = Header(...),
    limit: int = 20
):
    """Get user's credit purchase history"""
    try:
        user = await get_user_from_token(authorization)
        supabase = get_supabase_client()
        
        response = supabase.table("credit_transactions")\
            .select("*")\
            .eq("user_id", user.id)\
            .eq("type", "purchase")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return {"purchases": response.data}
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
