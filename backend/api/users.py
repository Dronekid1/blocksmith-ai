from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from services.supabase_client import (
    get_user_from_token,
    get_user_profile,
    get_supabase_client
)

router = APIRouter()

class UserProfile(BaseModel):
    id: str
    discord_username: Optional[str]
    avatar_url: Optional[str]
    credits: int
    total_spent: float
    created_at: str

@router.get("/me", response_model=UserProfile)
async def get_current_user(authorization: str = Header(...)):
    """Get current user's profile"""
    try:
        user = await get_user_from_token(authorization)
        profile = await get_user_profile(user.id)
        return profile
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me/generations")
async def get_user_generations(
    authorization: str = Header(...),
    limit: int = 20,
    offset: int = 0
):
    """Get user's generation history"""
    try:
        user = await get_user_from_token(authorization)
        supabase = get_supabase_client()
        
        response = supabase.table("generations")\
            .select("*")\
            .eq("user_id", user.id)\
            .order("created_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        return {
            "generations": response.data,
            "limit": limit,
            "offset": offset
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me/transactions")
async def get_user_transactions(
    authorization: str = Header(...),
    limit: int = 50,
    offset: int = 0
):
    """Get user's credit transaction history"""
    try:
        user = await get_user_from_token(authorization)
        supabase = get_supabase_client()
        
        response = supabase.table("credit_transactions")\
            .select("*")\
            .eq("user_id", user.id)\
            .order("created_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        return {
            "transactions": response.data,
            "limit": limit,
            "offset": offset
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
