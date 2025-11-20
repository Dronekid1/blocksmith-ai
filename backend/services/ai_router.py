import os
import anthropic
import google.generativeai as genai
from enum import Enum

class AIModel(str, Enum):
    CLAUDE = "claude"
    GEMINI = "gemini"

class AIRouter:
    def __init__(self):
        self.anthropic_client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.gemini_model = genai.GenerativeModel('gemini-pro')
    
    def route_request(self, generation_type: str, tier: str) -> AIModel:
        """
        Determine which AI model to use based on task complexity.
        
        Routing logic:
        - Simple datapacks (JSON only) -> Gemini (cheaper)
        - Complex datapacks -> Claude
        - All plugins -> Claude (Java is complex)
        - Texture pack prompts -> Gemini (just descriptions)
        """
        if generation_type == "datapack":
            if tier == "simple":
                return AIModel.GEMINI
            else:
                return AIModel.CLAUDE
        
        elif generation_type == "plugin":
            # Always use Claude for Java code
            return AIModel.CLAUDE
        
        elif generation_type == "texture_pack":
            # Gemini for generating image prompts
            return AIModel.GEMINI
        
        # Default to Claude for unknown types
        return AIModel.CLAUDE
    
    async def generate(self, prompt: str, system_prompt: str, model: AIModel) -> tuple[str, int]:
        """
        Generate content using the specified AI model.
        Returns (response_text, tokens_used)
        """
        if model == AIModel.CLAUDE:
            return await self._generate_claude(prompt, system_prompt)
        else:
            return await self._generate_gemini(prompt, system_prompt)
    
    async def _generate_claude(self, prompt: str, system_prompt: str) -> tuple[str, int]:
        """Generate using Claude API"""
        response = self.anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        text = response.content[0].text
        tokens = response.usage.input_tokens + response.usage.output_tokens
        
        return text, tokens
    
    async def _generate_gemini(self, prompt: str, system_prompt: str) -> tuple[str, int]:
        """Generate using Gemini API"""
        # Gemini doesn't have a separate system prompt, so we combine them
        full_prompt = f"{system_prompt}\n\n---\n\n{prompt}"
        
        response = self.gemini_model.generate_content(full_prompt)
        
        text = response.text
        # Gemini doesn't return exact token counts easily, estimate
        tokens = len(full_prompt.split()) + len(text.split())
        
        return text, tokens

# Singleton instance
ai_router = AIRouter()
