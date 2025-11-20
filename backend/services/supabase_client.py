import os
from supabase import create_client, Client
from functools import lru_cache

@lru_cache()
def get_supabase_client() -> Client:
    """Get Supabase client instance (cached)"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    
    return create_client(url, key)

async def get_user_from_token(authorization: str) -> dict:
    """Verify JWT token and get user data"""
    if not authorization or not authorization.startswith("Bearer "):
        raise ValueError("Invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    supabase = get_supabase_client()
    
    # Verify the token with Supabase
    user_response = supabase.auth.get_user(token)
    
    if not user_response or not user_response.user:
        raise ValueError("Invalid token")
    
    return user_response.user

async def get_user_profile(user_id: str) -> dict:
    """Get user profile with credits"""
    supabase = get_supabase_client()
    
    response = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
    
    if not response.data:
        raise ValueError("User profile not found")
    
    return response.data

async def update_user_credits(user_id: str, amount: int, transaction_type: str, description: str, generation_id: str = None, stripe_payment_id: str = None):
    """Update user credits and create transaction record"""
    supabase = get_supabase_client()
    
    # Get current credits
    profile = await get_user_profile(user_id)
    new_credits = profile["credits"] + amount
    
    if new_credits < 0:
        raise ValueError("Insufficient credits")
    
    # Update credits
    supabase.table("profiles").update({
        "credits": new_credits
    }).eq("id", user_id).execute()
    
    # Create transaction record
    transaction_data = {
        "user_id": user_id,
        "amount": amount,
        "type": transaction_type,
        "description": description,
    }
    
    if generation_id:
        transaction_data["generation_id"] = generation_id
    if stripe_payment_id:
        transaction_data["stripe_payment_id"] = stripe_payment_id
    
    supabase.table("credit_transactions").insert(transaction_data).execute()
    
    return new_credits
