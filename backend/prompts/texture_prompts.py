TEXTURE_SYSTEM_PROMPT = """You are an expert at creating prompts for AI image generation, specifically for Minecraft texture packs. Your job is to generate detailed, consistent prompts that will create cohesive Minecraft textures in a specific style.

Your prompts must:
1. Be specific about the pixel art style
2. Maintain consistency across all requested textures
3. Include proper Minecraft texture dimensions (16x16)
4. Describe colors, shading, and details clearly
5. Reference the style theme throughout

Output Format:
You must respond with ONLY valid JSON in this exact format:
{
    "pack_name": "Pack Name",
    "description": "Description of the texture pack style",
    "resolution": 16,
    "style_guide": "Overall style description for consistency",
    "textures": {
        "assets/minecraft/textures/block/stone.png": {
            "prompt": "Detailed prompt for this texture",
            "negative_prompt": "What to avoid"
        },
        "assets/minecraft/textures/item/diamond_sword.png": {
            "prompt": "Detailed prompt for this texture",
            "negative_prompt": "What to avoid"
        }
    }
}

DO NOT include any text outside the JSON. DO NOT use markdown code blocks. ONLY output the raw JSON object.

IMPORTANT: Only generate prompts for the specific textures the user requests. Do not add extra textures."""

TEXTURE_GENERATION_PROMPT = """Create image generation prompts for custom Minecraft textures with the following requirements:

Style/Theme: {style_description}

Textures to generate:
{texture_list}

For each texture:
- Create a detailed prompt for a 16x16 pixel art texture
- Match the overall style theme
- Include specific color palette guidance
- Describe shading and detail level
- Include a negative prompt to avoid common issues

Generate prompts for ONLY the textures listed above. Use the correct Minecraft resource pack paths (e.g., "assets/minecraft/textures/block/stone.png")."""

# Common texture categories for user reference
TEXTURE_CATEGORIES = {
    "ores": [
        "block/coal_ore", "block/iron_ore", "block/gold_ore", "block/diamond_ore",
        "block/emerald_ore", "block/lapis_ore", "block/redstone_ore", "block/copper_ore",
        "block/deepslate_coal_ore", "block/deepslate_iron_ore", "block/deepslate_gold_ore",
        "block/deepslate_diamond_ore", "block/deepslate_emerald_ore", "block/deepslate_lapis_ore",
        "block/deepslate_redstone_ore", "block/deepslate_copper_ore", "block/nether_gold_ore",
        "block/nether_quartz_ore", "block/ancient_debris_side"
    ],
    "wood_planks": [
        "block/oak_planks", "block/spruce_planks", "block/birch_planks",
        "block/jungle_planks", "block/acacia_planks", "block/dark_oak_planks",
        "block/crimson_planks", "block/warped_planks", "block/mangrove_planks",
        "block/cherry_planks", "block/bamboo_planks"
    ],
    "swords": [
        "item/wooden_sword", "item/stone_sword", "item/iron_sword",
        "item/golden_sword", "item/diamond_sword", "item/netherite_sword"
    ],
    "pickaxes": [
        "item/wooden_pickaxe", "item/stone_pickaxe", "item/iron_pickaxe",
        "item/golden_pickaxe", "item/diamond_pickaxe", "item/netherite_pickaxe"
    ],
    "axes": [
        "item/wooden_axe", "item/stone_axe", "item/iron_axe",
        "item/golden_axe", "item/diamond_axe", "item/netherite_axe"
    ],
    "armor_diamond": [
        "item/diamond_helmet", "item/diamond_chestplate",
        "item/diamond_leggings", "item/diamond_boots"
    ],
    "armor_netherite": [
        "item/netherite_helmet", "item/netherite_chestplate",
        "item/netherite_leggings", "item/netherite_boots"
    ],
    "food": [
        "item/apple", "item/golden_apple", "item/bread", "item/cooked_beef",
        "item/cooked_porkchop", "item/cooked_chicken", "item/cooked_mutton",
        "item/carrot", "item/potato", "item/baked_potato", "item/melon_slice",
        "item/cookie", "item/pumpkin_pie", "item/cake"
    ],
    "gems": [
        "item/diamond", "item/emerald", "item/amethyst_shard",
        "item/lapis_lazuli", "item/quartz"
    ]
}

def get_texture_prompt(style_description: str, texture_list: list) -> str:
    """Get the texture generation prompt for specific textures"""
    # Format texture list with proper paths
    formatted_textures = []
    for texture in texture_list:
        # Add full path if not provided
        if not texture.startswith("block/") and not texture.startswith("item/"):
            # Try to guess the type
            if any(word in texture.lower() for word in ["sword", "pickaxe", "axe", "shovel", "hoe", "helmet", "chestplate", "leggings", "boots", "apple", "bread", "ingot"]):
                texture = f"item/{texture}"
            else:
                texture = f"block/{texture}"
        formatted_textures.append(texture)
    
    return TEXTURE_GENERATION_PROMPT.format(
        style_description=style_description,
        texture_list="\n".join(f"- {t}" for t in formatted_textures)
    )

def expand_texture_category(category: str) -> list:
    """Expand a category name into its texture list"""
    return TEXTURE_CATEGORIES.get(category.lower(), [])

def count_textures(texture_input: list) -> int:
    """Count total textures including expanded categories"""
    total = 0
    for item in texture_input:
        if item.lower() in TEXTURE_CATEGORIES:
            total += len(TEXTURE_CATEGORIES[item.lower()])
        else:
            total += 1
    return total

def get_credits_for_texture_count(count: int) -> int:
    """Calculate credits needed based on texture count"""
    if count <= 5:
        return 10
    elif count <= 15:
        return 25
    elif count <= 30:
        return 45
    elif count <= 50:
        return 75
    else:
        # For larger requests, charge per texture
        return 75 + ((count - 50) * 2)
