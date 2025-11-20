import os
import json
import zipfile
import tempfile
import subprocess
import shutil
from datetime import datetime, timedelta
import replicate
import boto3
from botocore.config import Config

from services.supabase_client import get_supabase_client
from services.ai_router import ai_router
from prompts.plugin_prompts import get_plugin_prompt, PLUGIN_SYSTEM_PROMPT
from prompts.datapack_prompts import get_datapack_prompt, DATAPACK_SYSTEM_PROMPT
from prompts.texture_prompts import get_texture_prompt, TEXTURE_SYSTEM_PROMPT

class GeneratorService:
    def __init__(self):
        self.supabase = get_supabase_client()
        
        # Initialize R2 client
        self.r2_client = boto3.client(
            's3',
            endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
            aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
            config=Config(signature_version='s3v4')
        )
        self.r2_bucket = os.getenv('R2_BUCKET_NAME')
    
    def _update_generation(self, generation_id: str, updates: dict):
        """Update generation record in database"""
        self.supabase.table("generations").update(updates).eq("id", generation_id).execute()
    
    def _upload_to_r2(self, file_path: str, key: str) -> str:
        """Upload file to R2 and return public URL"""
        with open(file_path, 'rb') as f:
            self.r2_client.upload_fileobj(f, self.r2_bucket, key)
        
        # Return public URL (configure R2 bucket for public access or use presigned URLs)
        return f"https://{self.r2_bucket}.r2.dev/{key}"
    
    async def generate_plugin(self, generation_id: str, prompt: str, tier: str, name: str = None):
        """Generate a Minecraft plugin"""
        try:
            self._update_generation(generation_id, {"status": "processing"})
            
            # Get the appropriate prompt
            full_prompt = get_plugin_prompt(tier, prompt)
            
            # Route to AI
            model = ai_router.route_request("plugin", tier)
            response_text, tokens = await ai_router.generate(full_prompt, PLUGIN_SYSTEM_PROMPT, model)
            
            # Parse JSON response
            try:
                plugin_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                # Try to extract JSON from response
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start != -1 and end > start:
                    plugin_data = json.loads(response_text[start:end])
                else:
                    raise ValueError(f"Failed to parse AI response as JSON: {e}")
            
            # Create plugin files and compile
            plugin_name = name or plugin_data.get("plugin_name", "GeneratedPlugin")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write all files
                for file_path, content in plugin_data.get("files", {}).items():
                    full_path = os.path.join(temp_dir, file_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, 'w') as f:
                        f.write(content)
                
                # Create plugin.yml
                plugin_yml = self._create_plugin_yml(plugin_data)
                yml_path = os.path.join(temp_dir, "src/main/resources/plugin.yml")
                os.makedirs(os.path.dirname(yml_path), exist_ok=True)
                with open(yml_path, 'w') as f:
                    f.write(plugin_yml)
                
                # Compile with Maven
                jar_path = await self._compile_plugin(temp_dir, plugin_name)
                
                if jar_path and os.path.exists(jar_path):
                    # Upload to R2
                    key = f"plugins/{generation_id}/{plugin_name}.jar"
                    file_url = self._upload_to_r2(jar_path, key)
                    file_size = os.path.getsize(jar_path)
                    
                    self._update_generation(generation_id, {
                        "status": "completed",
                        "file_url": file_url,
                        "file_name": f"{plugin_name}.jar",
                        "file_size": file_size,
                        "ai_model_used": model.value,
                        "ai_tokens_used": tokens,
                        "completed_at": datetime.utcnow().isoformat(),
                        "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                        "output_metadata": {
                            "plugin_name": plugin_name,
                            "version": plugin_data.get("version", "1.0.0"),
                            "commands": list(plugin_data.get("commands", {}).keys())
                        }
                    })
                else:
                    # Compilation failed, provide source code as zip
                    zip_path = os.path.join(temp_dir, f"{plugin_name}_source.zip")
                    self._create_zip(temp_dir, zip_path, exclude=[f"{plugin_name}_source.zip"])
                    
                    key = f"plugins/{generation_id}/{plugin_name}_source.zip"
                    file_url = self._upload_to_r2(zip_path, key)
                    
                    self._update_generation(generation_id, {
                        "status": "completed",
                        "file_url": file_url,
                        "file_name": f"{plugin_name}_source.zip",
                        "file_size": os.path.getsize(zip_path),
                        "ai_model_used": model.value,
                        "ai_tokens_used": tokens,
                        "completed_at": datetime.utcnow().isoformat(),
                        "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                        "output_metadata": {
                            "plugin_name": plugin_name,
                            "note": "Compilation failed. Source code provided for manual compilation."
                        }
                    })
                    
        except Exception as e:
            self._update_generation(generation_id, {
                "status": "failed",
                "error_message": str(e)
            })
    
    async def generate_datapack(self, generation_id: str, prompt: str, tier: str, name: str = None):
        """Generate a Minecraft datapack"""
        try:
            self._update_generation(generation_id, {"status": "processing"})
            
            # Get the appropriate prompt
            full_prompt = get_datapack_prompt(tier, prompt)
            
            # Route to AI
            model = ai_router.route_request("datapack", tier)
            response_text, tokens = await ai_router.generate(full_prompt, DATAPACK_SYSTEM_PROMPT, model)
            
            # Parse JSON response
            try:
                datapack_data = json.loads(response_text)
            except json.JSONDecodeError:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start != -1 and end > start:
                    datapack_data = json.loads(response_text[start:end])
                else:
                    raise ValueError("Failed to parse AI response as JSON")
            
            pack_name = name or datapack_data.get("pack_name", "generated_datapack")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                pack_dir = os.path.join(temp_dir, pack_name)
                os.makedirs(pack_dir)
                
                # Write all files
                for file_path, content in datapack_data.get("files", {}).items():
                    full_path = os.path.join(pack_dir, file_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    
                    # Handle JSON content
                    if file_path.endswith('.json'):
                        if isinstance(content, str):
                            # Try to parse and reformat
                            try:
                                content = json.dumps(json.loads(content), indent=2)
                            except:
                                pass
                        else:
                            content = json.dumps(content, indent=2)
                    
                    with open(full_path, 'w') as f:
                        f.write(content)
                
                # Create zip
                zip_path = os.path.join(temp_dir, f"{pack_name}.zip")
                self._create_zip(pack_dir, zip_path)
                
                # Upload to R2
                key = f"datapacks/{generation_id}/{pack_name}.zip"
                file_url = self._upload_to_r2(zip_path, key)
                
                self._update_generation(generation_id, {
                    "status": "completed",
                    "file_url": file_url,
                    "file_name": f"{pack_name}.zip",
                    "file_size": os.path.getsize(zip_path),
                    "ai_model_used": model.value,
                    "ai_tokens_used": tokens,
                    "completed_at": datetime.utcnow().isoformat(),
                    "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                    "output_metadata": {
                        "pack_name": pack_name,
                        "description": datapack_data.get("description", "")
                    }
                })
                
        except Exception as e:
            self._update_generation(generation_id, {
                "status": "failed",
                "error_message": str(e)
            })
    
    async def generate_texture_pack(self, generation_id: str, style_description: str, textures: list, name: str = None):
        """Generate custom Minecraft textures"""
        try:
            self._update_generation(generation_id, {"status": "processing"})
            
            # Generate prompts for each texture using AI
            full_prompt = get_texture_prompt(style_description, textures)
            
            model = ai_router.route_request("texture_pack", "standard")
            response_text, tokens = await ai_router.generate(full_prompt, TEXTURE_SYSTEM_PROMPT, model)
            
            # Parse texture prompts
            try:
                texture_data = json.loads(response_text)
            except json.JSONDecodeError:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start != -1 and end > start:
                    texture_data = json.loads(response_text[start:end])
                else:
                    raise ValueError("Failed to parse AI response as JSON")
            
            pack_name = name or texture_data.get("pack_name", "custom_textures")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                pack_dir = os.path.join(temp_dir, pack_name)
                os.makedirs(pack_dir)
                
                # Create pack.mcmeta
                pack_mcmeta = {
                    "pack": {
                        "pack_format": 15,
                        "description": texture_data.get("description", f"Custom textures: {style_description}")
                    }
                }
                with open(os.path.join(pack_dir, "pack.mcmeta"), 'w') as f:
                    json.dump(pack_mcmeta, f, indent=2)
                
                # Generate each texture with Stable Diffusion
                generated_count = 0
                for texture_path, texture_info in texture_data.get("textures", {}).items():
                    try:
                        image_data = await self._generate_texture_image(
                            texture_info.get("prompt", ""),
                            texture_info.get("negative_prompt", "")
                        )
                        
                        if image_data:
                            # Save texture
                            full_path = os.path.join(pack_dir, texture_path)
                            os.makedirs(os.path.dirname(full_path), exist_ok=True)
                            
                            with open(full_path, 'wb') as f:
                                f.write(image_data)
                            
                            generated_count += 1
                    except Exception as e:
                        print(f"Failed to generate texture {texture_path}: {e}")
                        continue
                
                # Create zip
                zip_path = os.path.join(temp_dir, f"{pack_name}.zip")
                self._create_zip(pack_dir, zip_path)
                
                # Upload to R2
                key = f"textures/{generation_id}/{pack_name}.zip"
                file_url = self._upload_to_r2(zip_path, key)
                
                self._update_generation(generation_id, {
                    "status": "completed",
                    "file_url": file_url,
                    "file_name": f"{pack_name}.zip",
                    "file_size": os.path.getsize(zip_path),
                    "ai_model_used": model.value,
                    "ai_tokens_used": tokens,
                    "completed_at": datetime.utcnow().isoformat(),
                    "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                    "output_metadata": {
                        "pack_name": pack_name,
                        "textures_requested": len(textures),
                        "textures_generated": generated_count,
                        "style": style_description
                    }
                })
                
        except Exception as e:
            self._update_generation(generation_id, {
                "status": "failed",
                "error_message": str(e)
            })
    
    async def _generate_texture_image(self, prompt: str, negative_prompt: str) -> bytes:
        """Generate a single texture using Stable Diffusion via Replicate"""
        # Use a pixel art focused model
        output = replicate.run(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={
                "prompt": f"minecraft texture, pixel art, 16x16, game asset, {prompt}",
                "negative_prompt": f"blurry, realistic, photograph, 3d render, {negative_prompt}",
                "width": 64,  # Generate larger, then downscale for quality
                "height": 64,
                "num_outputs": 1,
                "guidance_scale": 7.5,
                "num_inference_steps": 25
            }
        )
        
        if output and len(output) > 0:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(output[0])
                return response.content
        
        return None
    
    async def _compile_plugin(self, project_dir: str, plugin_name: str) -> str:
        """Compile plugin with Maven"""
        try:
            # Run Maven build
            result = subprocess.run(
                ["mvn", "package", "-q"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                # Find the jar file
                target_dir = os.path.join(project_dir, "target")
                if os.path.exists(target_dir):
                    for file in os.listdir(target_dir):
                        if file.endswith(".jar") and not file.endswith("-sources.jar"):
                            return os.path.join(target_dir, file)
            
            return None
        except Exception as e:
            print(f"Compilation error: {e}")
            return None
    
    def _create_plugin_yml(self, plugin_data: dict) -> str:
        """Create plugin.yml content from plugin data"""
        yml_content = f"""name: {plugin_data.get('plugin_name', 'GeneratedPlugin')}
version: {plugin_data.get('version', '1.0.0')}
main: {plugin_data.get('main_class', 'com.blocksmith.plugin.Main')}
api-version: {plugin_data.get('api_version', '1.20')}
description: {plugin_data.get('description', 'Generated by BlockSmith AI')}
author: BlockSmith AI

"""
        
        # Add commands
        commands = plugin_data.get('commands', {})
        if commands:
            yml_content += "commands:\n"
            for cmd_name, cmd_data in commands.items():
                yml_content += f"  {cmd_name}:\n"
                yml_content += f"    description: {cmd_data.get('description', '')}\n"
                yml_content += f"    usage: {cmd_data.get('usage', f'/{cmd_name}')}\n"
                if 'permission' in cmd_data:
                    yml_content += f"    permission: {cmd_data['permission']}\n"
        
        # Add permissions
        permissions = plugin_data.get('permissions', {})
        if permissions:
            yml_content += "\npermissions:\n"
            for perm_name, perm_data in permissions.items():
                yml_content += f"  {perm_name}:\n"
                yml_content += f"    description: {perm_data.get('description', '')}\n"
                yml_content += f"    default: {perm_data.get('default', 'op')}\n"
        
        return yml_content
    
    def _create_zip(self, source_dir: str, zip_path: str, exclude: list = None):
        """Create a zip file from a directory"""
        exclude = exclude or []
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    if file not in exclude:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, arcname)
