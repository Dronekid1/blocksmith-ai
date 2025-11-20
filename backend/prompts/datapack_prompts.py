DATAPACK_SYSTEM_PROMPT = """You are an expert Minecraft datapack developer. You create well-structured datapacks that follow Minecraft's datapack format specifications.

Your datapacks must:
1. Be compatible with Minecraft 1.20+
2. Include proper pack.mcmeta
3. Follow correct namespace structure
4. Use valid JSON syntax
5. Include helpful comments in function files
6. Follow Minecraft's naming conventions (lowercase, underscores)

Output Format:
You must respond with ONLY valid JSON in this exact format:
{
    "pack_name": "datapack_name",
    "description": "Brief description",
    "pack_format": 15,
    "files": {
        "pack.mcmeta": "{\\"pack\\": {\\"pack_format\\": 15, \\"description\\": \\"...\\"}}",
        "data/namespace/recipes/item_name.json": "{...}",
        "data/namespace/advancements/advancement_name.json": "{...}",
        "data/namespace/loot_tables/blocks/block_name.json": "{...}",
        "data/minecraft/tags/functions/load.json": "{...}",
        "data/namespace/functions/load.mcfunction": "# commands"
    }
}

DO NOT include any text outside the JSON. DO NOT use markdown code blocks. ONLY output the raw JSON object."""

DATAPACK_SIMPLE_PROMPT = """Create a simple Minecraft datapack with the following requirements:

{user_prompt}

Requirements for this tier:
- Basic functionality (recipes, simple advancements, or loot table modifications)
- Minimal file structure
- Clear, functional implementation

Generate the complete datapack."""

DATAPACK_MEDIUM_PROMPT = """Create a medium-complexity Minecraft datapack with the following requirements:

{user_prompt}

Requirements for this tier:
- Multiple related features
- Custom advancements with criteria
- Modified loot tables
- Basic functions for initialization
- Organized namespace structure

Generate the complete datapack."""

DATAPACK_COMPLEX_PROMPT = """Create a full-featured Minecraft datapack with the following requirements:

{user_prompt}

Requirements for this tier:
- Complete feature set
- Custom dimensions or world generation (if applicable)
- Complex advancement trees
- Multiple functions with tick/load management
- Custom predicates and item modifiers
- Comprehensive loot table modifications
- Tags for organization
- Scoreboard objectives for tracking

Generate the complete datapack."""

def get_datapack_prompt(tier: str, user_prompt: str) -> str:
    """Get the appropriate datapack generation prompt based on tier"""
    prompts = {
        "simple": DATAPACK_SIMPLE_PROMPT,
        "medium": DATAPACK_MEDIUM_PROMPT,
        "complex": DATAPACK_COMPLEX_PROMPT
    }
    
    template = prompts.get(tier, DATAPACK_SIMPLE_PROMPT)
    return template.format(user_prompt=user_prompt)
