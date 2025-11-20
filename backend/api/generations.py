from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
import uuid
import json

from services.supabase_client import (
    get_user_from_token,
    get_user_profile,
    get_supabase_client,
    update_user_credits
)
from services.ai_router import ai_router, AIModel
from services.generator import GeneratorService
from prompts.plugin_prompts import get_plugin_prompt, PLUGIN_SYSTEM_PROMPT
from prompts.datapack_prompts import get_datapack_prompt, DATAPACK_SYSTEM_PROMPT
from prompts.texture_prompts import (
    get_texture_prompt, 
    TEXTURE_SYSTEM_PROMPT,
    count_textures,
    get_credits_for_texture_count,
    expand_texture_category,
    TEXTURE_CATEGORIES
)

router = APIRouter()
generator_service = GeneratorService()

# Request models
class PluginRequest(BaseModel):
    prompt: str
    tier: str  # simple, medium, complex
    name: Optional[str] = None

class DatapackRequest(BaseModel):
    prompt: str
    tier: str  # simple, medium, complex
    name: Optional[str] = None

class TexturePackRequest(BaseModel):
    style_description: str
    textures: List[str]  # Can be individual textures or category names like "ores", "swords"
    name: Optional[str] = None

# Pricing
PLUGIN_CREDITS = {"simple": 20, "medium": 35, "complex": 50}
DATAPACK_CREDITS = {"simple": 5, "medium": 10, "complex": 15}

@router.get("/pricing")
async def get_pricing():
    """Get current generation pricing"""
    return {
        "plugin": PLUGIN_CREDITS,
        "datapack": DATAPACK_CREDITS,
        "texture_pack": {
            "1-5 textures": 10,
            "6-15 textures": 25,
            "16-30 textures": 45,
            "31-50 textures": 75,
            "50+ textures": "75 + 2 per additional texture"
        },
        "texture_categories": list(TEXTURE_CATEGORIES.keys())
    }

@router.post("/plugin")
async def generate_plugin(
    request: PluginRequest,
    background_tasks: BackgroundTasks,
    authorization: str = Header(...)
):
    """Generate a Minecraft plugin"""
    try:
        # Validate tier
        if request.tier not in PLUGIN_CREDITS:
            raise HTTPException(status_code=400, detail="Invalid tier. Must be: simple, medium, complex")
        
        # Auth and credits check
        user = await get_user_from_token(authorization)
        profile = await get_user_profile(user.id)
        
        credits_needed = PLUGIN_CREDITS[request.tier]
        if profile["credits"] < credits_needed:
            raise HTTPException(
                status_code=402, 
                detail=f"Insufficient credits. Need {credits_needed}, have {profile['credits']}"
            )
        
        # Create generation record
        supabase = get_supabase_client()
        generation_id = str(uuid.uuid4())
        
        supabase.table("generations").insert({
            "id": generation_id,
            "user_id": user.id,
            "type": "plugin",
            "tier": request.tier,
            "status": "pending",
            "prompt": request.prompt,
            "credits_used": credits_needed,
            "input_params": {"name": request.name}
        }).execute()
        
        # Deduct credits
        await update_user_credits(
            user.id, 
            -credits_needed, 
            "usage", 
            f"Plugin generation ({request.tier})",
            generation_id
        )
        
        # Queue generation
        background_tasks.add_task(
            generator_service.generate_plugin,
            generation_id,
            request.prompt,
            request.tier,
            request.name
        )
        
        return {
            "generation_id": generation_id,
            "status": "pending",
            "credits_used": credits_needed,
            "message": "Plugin generation started. Check status for updates."
        }
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/datapack")
async def generate_datapack(
    request: DatapackRequest,
    background_tasks: BackgroundTasks,
    authorization: str = Header(...)
):
    """Generate a Minecraft datapack"""
    try:
        # Validate tier
        if request.tier not in DATAPACK_CREDITS:
            raise HTTPException(status_code=400, detail="Invalid tier. Must be: simple, medium, complex")
        
        # Auth and credits check
        user = await get_user_from_token(authorization)
        profile = await get_user_profile(user.id)
        
        credits_needed = DATAPACK_CREDITS[request.tier]
        if profile["credits"] < credits_needed:
            raise HTTPException(
                status_code=402, 
                detail=f"Insufficient credits. Need {credits_needed}, have {profile['credits']}"
            )
        
        # Create generation record
        supabase = get_supabase_client()
        generation_id = str(uuid.uuid4())
        
        supabase.table("generations").insert({
            "id": generation_id,
            "user_id": user.id,
            "type": "datapack",
            "tier": request.tier,
            "status": "pending",
            "prompt": request.prompt,
            "credits_used": credits_needed,
            "input_params": {"name": request.name}
        }).execute()
        
        # Deduct credits
        await update_user_credits(
            user.id, 
            -credits_needed, 
            "usage", 
            f"Datapack generation ({request.tier})",
            generation_id
        )
        
        # Queue generation
        background_tasks.add_task(
            generator_service.generate_datapack,
            generation_id,
            request.prompt,
            request.tier,
            request.name
        )
        
        return {
            "generation_id": generation_id,
            "status": "pending",
            "credits_used": credits_needed,
            "message": "Datapack generation started. Check status for updates."
        }
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/texture-pack")
async def generate_texture_pack(
    request: TexturePackRequest,
    background_tasks: BackgroundTasks,
    authorization: str = Header(...)
):
    """Generate custom Minecraft textures"""
    try:
        # Expand categories and count textures
        expanded_textures = []
        for item in request.textures:
            if item.lower() in TEXTURE_CATEGORIES:
                expanded_textures.extend(TEXTURE_CATEGORIES[item.lower()])
            else:
                expanded_textures.append(item)
        
        texture_count = len(expanded_textures)
        
        if texture_count == 0:
            raise HTTPException(status_code=400, detail="No textures specified")
        
        if texture_count > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 textures per request")
        
        credits_needed = get_credits_for_texture_count(texture_count)
        
        # Auth and credits check
        user = await get_user_from_token(authorization)
        profile = await get_user_profile(user.id)
        
        if profile["credits"] < credits_needed:
            raise HTTPException(
                status_code=402, 
                detail=f"Insufficient credits. Need {credits_needed}, have {profile['credits']}"
            )
        
        # Create generation record
        supabase = get_supabase_client()
        generation_id = str(uuid.uuid4())
        
        supabase.table("generations").insert({
            "id": generation_id,
            "user_id": user.id,
            "type": "texture_pack",
            "tier": f"{texture_count}_textures",
            "status": "pending",
            "prompt": request.style_description,
            "credits_used": credits_needed,
            "input_params": {
                "name": request.name,
                "textures": expanded_textures,
                "original_input": request.textures
            }
        }).execute()
        
        # Deduct credits
        await update_user_credits(
            user.id, 
            -credits_needed, 
            "usage", 
            f"Texture pack generation ({texture_count} textures)",
            generation_id
        )
        
        # Queue generation
        background_tasks.add_task(
            generator_service.generate_texture_pack,
            generation_id,
            request.style_description,
            expanded_textures,
            request.name
        )
        
        return {
            "generation_id": generation_id,
            "status": "pending",
            "credits_used": credits_needed,
            "texture_count": texture_count,
            "message": "Texture pack generation started. Check status for updates."
        }
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{generation_id}")
async def get_generation_status(
    generation_id: str,
    authorization: str = Header(...)
):
    """Get status of a generation"""
    try:
        user = await get_user_from_token(authorization)
        supabase = get_supabase_client()
        
        response = supabase.table("generations")\
            .select("*")\
            .eq("id", generation_id)\
            .eq("user_id", user.id)\
            .single()\
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Generation not found")
        
        return response.data
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/estimate")
async def estimate_credits(
    generation_type: str,
    tier: Optional[str] = None,
    textures: Optional[List[str]] = None
):
    """Estimate credits needed for a generation"""
    if generation_type == "plugin":
        if tier not in PLUGIN_CREDITS:
            raise HTTPException(status_code=400, detail="Invalid tier")
        return {"credits": PLUGIN_CREDITS[tier]}
    
    elif generation_type == "datapack":
        if tier not in DATAPACK_CREDITS:
            raise HTTPException(status_code=400, detail="Invalid tier")
        return {"credits": DATAPACK_CREDITS[tier]}
    
    elif generation_type == "texture_pack":
        if not textures:
            raise HTTPException(status_code=400, detail="Textures list required")
        
        # Expand and count
        expanded = []
        for item in textures:
            if item.lower() in TEXTURE_CATEGORIES:
                expanded.extend(TEXTURE_CATEGORIES[item.lower()])
            else:
                expanded.append(item)
        
        return {
            "credits": get_credits_for_texture_count(len(expanded)),
            "texture_count": len(expanded)
        }
    
    else:
        raise HTTPException(status_code=400, detail="Invalid generation type")
