PLUGIN_SYSTEM_PROMPT = """You are an expert Minecraft plugin developer specializing in Spigot and Paper plugins. You write clean, efficient, well-documented Java code that follows best practices.

Your plugins must:
1. Be compatible with Spigot/Paper 1.20+
2. Include proper plugin.yml configuration
3. Use modern Java practices (Java 17+)
4. Include helpful comments
5. Handle errors gracefully
6. Use configuration files for customizable values
7. Include proper permission nodes
8. Register all events and commands properly

Output Format:
You must respond with ONLY valid JSON in this exact format:
{
    "plugin_name": "PluginName",
    "version": "1.0.0",
    "description": "Brief description",
    "main_class": "com.blocksmith.pluginname.PluginName",
    "api_version": "1.20",
    "commands": {
        "commandname": {
            "description": "Command description",
            "usage": "/<command> [args]",
            "permission": "pluginname.command"
        }
    },
    "permissions": {
        "pluginname.command": {
            "description": "Permission description",
            "default": "op"
        }
    },
    "files": {
        "src/main/java/com/blocksmith/pluginname/PluginName.java": "// Java code here",
        "src/main/resources/config.yml": "# Config here",
        "pom.xml": "<!-- Maven POM -->"
    }
}

DO NOT include any text outside the JSON. DO NOT use markdown code blocks. ONLY output the raw JSON object."""

PLUGIN_SIMPLE_PROMPT = """Create a simple Spigot/Paper plugin with the following requirements:

{user_prompt}

Requirements for this tier:
- Single main class is preferred
- Basic functionality only
- Simple config.yml with key settings
- 1-2 commands maximum
- Include helpful comments

Generate the complete plugin code."""

PLUGIN_MEDIUM_PROMPT = """Create a medium-complexity Spigot/Paper plugin with the following requirements:

{user_prompt}

Requirements for this tier:
- Organized class structure (separate classes for commands, listeners)
- Full config.yml with all customizable options
- Multiple commands with tab completion
- Event listeners as needed
- Data persistence (YAML or SQLite)
- Include comprehensive comments

Generate the complete plugin code."""

PLUGIN_COMPLEX_PROMPT = """Create a full-featured Spigot/Paper plugin with the following requirements:

{user_prompt}

Requirements for this tier:
- Professional package structure
- Multiple classes with clear separation of concerns
- Complete config.yml with sections and comments
- Multiple commands with full tab completion
- Event listeners for all relevant events
- Database support (SQLite with option for MySQL)
- Messages.yml for all user-facing text
- GUI menus if appropriate
- Update checker (optional)
- Metrics (bStats) placeholder
- Include comprehensive JavaDoc comments

Generate the complete plugin code."""

def get_plugin_prompt(tier: str, user_prompt: str) -> str:
    """Get the appropriate plugin generation prompt based on tier"""
    prompts = {
        "simple": PLUGIN_SIMPLE_PROMPT,
        "medium": PLUGIN_MEDIUM_PROMPT,
        "complex": PLUGIN_COMPLEX_PROMPT
    }
    
    template = prompts.get(tier, PLUGIN_SIMPLE_PROMPT)
    return template.format(user_prompt=user_prompt)
