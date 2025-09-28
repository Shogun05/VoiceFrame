#!/usr/bin/env python3
"""
InvokeAI Programmatic Image Generation Module
A modular class for background generation and character inpainting using InvokeAI's web API
"""

import os
import sys
import io
from pathlib import Path
from PIL import Image
import uuid
import requests
import json
import time
import random
from typing import List, Optional, Tuple, Union

# Default settings
DEFAULT_NEGATIVE_PROMPT = "blurry, low quality, distorted, artifacts, bad anatomy, watermark, text, (photo)+++. greyscale. solid black. painting"

class InvokeClient:
    """
    A comprehensive client for InvokeAI image generation and inpainting
    
    Usage:
        client = InvokeClient(
            background_prompt="sunny meadow with flowers",
            character_prompts=["cute rabbit", "colorful butterfly"]
        )
        final_image = client.generate_complete_scene()
    """
    
    def __init__(self, background_prompt: str, character_prompts: List[str], 
                 host: str = "localhost", port: int = 9090,
                 negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
                 model_name: str = "dreamshaper xl v2 turbo"):
        """
        Initialize the InvokeAI client
        
        Args:
            background_prompt: Prompt for generating the background
            character_prompts: List of prompts for characters to inpaint
            host: InvokeAI server host
            port: InvokeAI server port
            negative_prompt: Negative prompt for all generations
            model_name: Name of the model to use (case insensitive)
        """
        self.base_url = f"http://{host}:{port}/api/v1" 
        self.queue_id = "default"
        self.background_prompt = background_prompt+", anime++, bold outline, cel-shaded coloring, shounen, seinen"
        self.character_prompts = [i + ", anime++, bold outline, cel-shaded coloring, shounen, seinen" for i in character_prompts]
        self.negative_prompt = negative_prompt
        
        # Fetch model configuration dynamically
        self.model_config = self._fetch_model_config(model_name.lower())
        if not self.model_config:
            raise ValueError(f"Model '{model_name}' not found on InvokeAI server")
        
        print(f"✓ InvokeClient initialized for {self.base_url}")
        print(f"✓ Using model: {self.model_config['name']} (key: {self.model_config['key']})")

    def _fetch_model_config(self, model_name: str) -> Optional[dict]:
        """
        Fetch model configuration from InvokeAI API by matching model name
        
        Args:
            model_name: Name of the model to search for (case insensitive)
            
        Returns:
            Model configuration dictionary or None if not found
        """
        try:
            # Fetch all models from the API
            response = requests.get(f"{self.base_url[:-1]}2/models/", params={"model_type": "main"})
            response.raise_for_status()
            
            models_data = response.json()
            
            # Search for matching model name
            for model in models_data.get("models", []):
                if model.get("name", "").lower() == model_name.lower():
                    # Return the essential model config
                    return {
                        "key": model["key"],
                        "hash": model.get("hash", ""),
                        "name": model["name"],
                        "base": model.get("base", ""),
                        "type": model.get("type", "main")
                    }
            
            print(f"✗ Model '{model_name}' not found. Available models:")
            for model in models_data.get("models", []):
                if model.get("type") == "main":
                    print(f"  - {model.get('name', 'Unknown')}")
            
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching models from InvokeAI API: {e}")
            return None

    def create_background_graph(self, prompt: str, width: int = 1024, height: int = 576) -> dict:
        """Create workflow graph for background generation"""
        
        graph = {
            "nodes": {
                "model_loader": {
                    "id": "model_loader",
                    "type": "sdxl_model_loader",
                    "model": self.model_config
                },
                "positive_compel": {
                    "id": "positive_compel",
                    "type": "sdxl_compel_prompt",
                    "prompt": prompt,
                    "style": prompt,
                },
                "negative_compel": {
                    "id": "negative_compel",
                    "type": "sdxl_compel_prompt",
                    "prompt": self.negative_prompt,
                    "style": self.negative_prompt,
                },
                "noise": {
                    "id": "noise",
                    "type": "noise",
                    "seed": random.randint(0, 2**32 - 1),
                    "width": width,
                    "height": height,
                    "use_cpu": True
                },
                "denoise": {
                    "id": "denoise",
                    "type": "denoise_latents",
                    "steps": 8,
                    "cfg_scale": 2.0,
                    "denoising_start": 0.0,
                    "denoising_end": 1.0,
                    "scheduler": "dpmpp_sde_k",
                },
                "latents_to_img": {
                    "id": "latents_to_img",
                    "type": "l2i",
                    "fp32": True
                }
            },
            "edges": [
                { "source": { "node_id": "model_loader", "field": "unet" }, "destination": { "node_id": "denoise", "field": "unet" } },
                { "source": { "node_id": "model_loader", "field": "clip" }, "destination": { "node_id": "positive_compel", "field": "clip" } },
                { "source": { "node_id": "model_loader", "field": "clip2" }, "destination": { "node_id": "positive_compel", "field": "clip2" } },
                { "source": { "node_id": "model_loader", "field": "clip" }, "destination": { "node_id": "negative_compel", "field": "clip" } },
                { "source": { "node_id": "model_loader", "field": "clip2" }, "destination": { "node_id": "negative_compel", "field": "clip2" } },
                { "source": { "node_id": "model_loader", "field": "vae" }, "destination": { "node_id": "latents_to_img", "field": "vae" } },
                { "source": { "node_id": "positive_compel", "field": "conditioning" }, "destination": { "node_id": "denoise", "field": "positive_conditioning" } },
                { "source": { "node_id": "negative_compel", "field": "conditioning" }, "destination": { "node_id": "denoise", "field": "negative_conditioning" } },
                { "source": { "node_id": "noise", "field": "noise" }, "destination": { "node_id": "denoise", "field": "noise" } },
                { "source": { "node_id": "denoise", "field": "latents" }, "destination": { "node_id": "latents_to_img", "field": "latents" } }
            ]
        }
        return graph

    def create_inpainting_graph(self, input_image_name: str, mask_image_name: str, 
                               prompt: str, image_width: int, image_height: int) -> dict:
        """Create workflow graph for inpainting"""
        
        graph = {
            "nodes": {
                "model_loader": {
                    "id": "model_loader",
                    "type": "sdxl_model_loader",
                    "model": self.model_config
                },
                "positive_compel": {
                    "id": "positive_compel",
                    "type": "sdxl_compel_prompt",
                    "prompt": prompt,
                    "style": prompt,
                },
                "negative_compel": {
                    "id": "negative_compel",
                    "type": "sdxl_compel_prompt",
                    "prompt": self.negative_prompt,
                    "style": self.negative_prompt,
                },
                "input_image": {
                    "id": "input_image",
                    "type": "image",
                    "image": { "image_name": input_image_name }
                },
                "mask_image": {
                    "id": "mask_image",
                    "type": "image",
                    "image": { "image_name": mask_image_name }
                },
                "noise": {
                    "id": "noise",
                    "type": "noise",
                    "seed": random.randint(0, 2**32 - 1),
                    "width": image_width,
                    "height": image_height,
                    "use_cpu": True
                },
                "i2l": {
                    "id": "i2l",
                    "type": "i2l",
                },
                "create_denoise_mask": {
                    "id": "create_denoise_mask",
                    "type": "create_denoise_mask",
                    "fp32": True,
                },
                "denoise": {
                    "id": "denoise",
                    "type": "denoise_latents",
                    "steps": 8,
                    "cfg_scale": 2.0,
                    "denoising_start": 0.0,
                    "denoising_end": 1.0,
                    "scheduler": "dpmpp_sde_k",
                },
                "latents_to_img": {
                    "id": "latents_to_img",
                    "type": "l2i",
                    "fp32": True
                }
            },
            "edges": [
                { "source": { "node_id": "model_loader", "field": "unet" }, "destination": { "node_id": "denoise", "field": "unet" } },
                { "source": { "node_id": "model_loader", "field": "clip" }, "destination": { "node_id": "positive_compel", "field": "clip" } },
                { "source": { "node_id": "model_loader", "field": "clip2" }, "destination": { "node_id": "positive_compel", "field": "clip2" } },
                { "source": { "node_id": "model_loader", "field": "clip" }, "destination": { "node_id": "negative_compel", "field": "clip" } },
                { "source": { "node_id": "model_loader", "field": "clip2" }, "destination": { "node_id": "negative_compel", "field": "clip2" } },
                { "source": { "node_id": "model_loader", "field": "vae" }, "destination": { "node_id": "i2l", "field": "vae" } },
                { "source": { "node_id": "model_loader", "field": "vae" }, "destination": { "node_id": "create_denoise_mask", "field": "vae" } },
                { "source": { "node_id": "model_loader", "field": "vae" }, "destination": { "node_id": "latents_to_img", "field": "vae" } },
                { "source": { "node_id": "positive_compel", "field": "conditioning" }, "destination": { "node_id": "denoise", "field": "positive_conditioning" } },
                { "source": { "node_id": "negative_compel", "field": "conditioning" }, "destination": { "node_id": "denoise", "field": "negative_conditioning" } },
                { "source": { "node_id": "noise", "field": "noise" }, "destination": { "node_id": "denoise", "field": "noise" } },
                { "source": { "node_id": "input_image", "field": "image" }, "destination": { "node_id": "i2l", "field": "image" } },
                { "source": { "node_id": "i2l", "field": "latents" }, "destination": { "node_id": "denoise", "field": "latents" } },
                { "source": { "node_id": "mask_image", "field": "image" }, "destination": { "node_id": "create_denoise_mask", "field": "mask" } },
                { "source": { "node_id": "create_denoise_mask", "field": "denoise_mask" }, "destination": { "node_id": "denoise", "field": "denoise_mask" } },
                { "source": { "node_id": "denoise", "field": "latents" }, "destination": { "node_id": "latents_to_img", "field": "latents" } }
            ]
        }
        return graph

    def upload_image(self, image: Union[str, Image.Image], category: str = "general") -> dict:
        """Upload an image to InvokeAI and return the response"""
        
        if isinstance(image, str):
            # If it's a file path
            with open(image, "rb") as f:
                pil_image = Image.open(f)
                image_format = pil_image.format or "PNG"
                f.seek(0)
                files = {'file': (os.path.basename(image), f, f"image/{image_format.lower()}")}
                
                response = requests.post(
                    f"{self.base_url}/images/upload",
                    params={"image_category": category, "is_intermediate": False},
                    files=files,
                )
        else:
            # If it's a PIL Image
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            files = {'file': ('generated_image.png', img_bytes, 'image/png')}
            response = requests.post(
                f"{self.base_url}/images/upload",
                params={"image_category": category, "is_intermediate": False},
                files=files,
            )
        
        response.raise_for_status()
        return response.json()

    def create_workflow(self, graph: dict, workflow_name: str) -> Optional[dict]:
        """Create a workflow from a graph"""
        
        workflow = {
            "name": f"{workflow_name} {str(uuid.uuid4())[:8]}",
            "author": "InvokeClient",
            "description": f"Automated {workflow_name.lower()} workflow",
            "version": "1.0.0",
            "contact": "",
            "tags": "automation",
            "notes": "Generated programmatically",
            "exposedFields": [],
            "meta": {"version": "1.0.0", "category": "user"},
            "nodes": list(graph.get("nodes", {}).values()),
            "edges": graph.get("edges", []),
            "form": {},
            "is_published": False
        }

        try:
            response = requests.post(f"{self.base_url}/workflows/", json={"workflow": workflow})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"✗ Error creating workflow: {e}")
            return None

    def execute_workflow(self, workflow_data: dict, graph: dict) -> Optional[Image.Image]:
        """Execute a workflow and return the generated image"""
        
        payload = {
            "batch": {
                "graph": {
                    "id": str(uuid.uuid4()),
                    "nodes": graph["nodes"],
                    "edges": graph["edges"]
                },
                "workflow": workflow_data['workflow'],
                "runs": 1,
            }
        }
        
        try:
            # Enqueue workflow
            response = requests.post(f"{self.base_url}/queue/{self.queue_id}/enqueue_batch", json=payload)
            response.raise_for_status()
            enqueue_result = response.json()
            
            # Get queue item ID
            queue_item_id = None
            if 'item_ids' in enqueue_result and enqueue_result['item_ids']:
                queue_item_id = enqueue_result['item_ids'][0] if isinstance(enqueue_result['item_ids'], list) else enqueue_result['item_ids']
            
            if queue_item_id is None:
                print("✗ Unable to get queue item ID")
                return None

            print(f"✓ Workflow enqueued with item ID: {queue_item_id}")

            # Wait for completion
            while True:
                response = requests.get(f"{self.base_url}/queue/{self.queue_id}/i/{queue_item_id}")
                response.raise_for_status()
                status = response.json()
                
                if status['status'] == 'completed':
                    print("✓ Workflow executed successfully")
                    
                    # Get the most recent image using the hack method
                    response = requests.get(f"{self.base_url}/images/")
                    if response.status_code == 200:
                        images_data = response.json()
                        if 'items' in images_data and len(images_data['items']) > 0:
                            image_name = images_data['items'][0]['image_name']
                            
                            # Download the image
                            img_response = requests.get(f"{self.base_url}/images/i/{image_name}/full")
                            img_response.raise_for_status()
                            
                            return Image.open(io.BytesIO(img_response.content))
                    
                    print("✗ Could not retrieve generated image")
                    return None
                    
                elif status['status'] in ['failed', 'canceled']:
                    print(f"✗ Workflow execution failed: {status}")
                    return None
                
                print(f"Workflow status: {status['status']}...")
                time.sleep(2)
                
        except requests.exceptions.RequestException as e:
            print(f"✗ Error executing workflow: {e}")
            return None

    def create_simple_mask(self, width: int, height: int, mask_area: str = "center") -> Image.Image:
        """Create a simple mask for inpainting"""
        
        mask = Image.new('RGB', (width, height), 'black')
        
        if mask_area == "center":
            # Create a centered rectangular mask
            mask_width = width // 3
            mask_height = height // 3
            left = (width - mask_width) // 2
            top = (height - mask_height) // 2
            
            from PIL import ImageDraw
            draw = ImageDraw.Draw(mask)
            draw.rectangle([left, top, left + mask_width, top + mask_height], fill='white')
        
        return mask

    def generate_background(self, width: int = 1024, height: int = 576) -> Optional[Image.Image]:
        """Generate a background image"""
        
        print(f"🎨 Generating background: '{self.background_prompt}'")
        
        # Create background generation workflow
        graph = self.create_background_graph(self.background_prompt, width, height)
        workflow = self.create_workflow(graph, "Background Generation")
        
        if not workflow:
            return None
            
        return self.execute_workflow(workflow, graph)

    def inpaint_character(self, background: Image.Image, character_prompt: str, 
                         mask_path: str) -> Optional[Image.Image]:
        """Inpaint a character onto the background using a predefined mask file"""
        
        print(f"🎭 Inpainting character: '{character_prompt}' with mask: {mask_path}")
        
        # Upload background image
        bg_data = self.upload_image(background, "general")
        bg_image_name = bg_data['image_name']
        
        # Upload the predefined mask
        mask_data = self.upload_image(mask_path, "mask")
        mask_image_name = mask_data['image_name']
        
        # Create inpainting workflow
        graph = self.create_inpainting_graph(
            bg_image_name, mask_image_name, character_prompt, 
            background.width, background.height
        )
        workflow = self.create_workflow(graph, "Character Inpainting")
        
        if not workflow:
            return None
            
        return self.execute_workflow(workflow, graph)

    def generate_complete_scene(self) -> Optional[Image.Image]:
        """
        Main method: Generate background and inpaint all characters
        Returns the final composite image
        """
        
        print("🚀 Starting complete scene generation...")
        
        # Step 1: Generate background
        current_image = self.generate_background()
        if not current_image:
            print("✗ Failed to generate background")
            return None
        
        print("✓ Background generated successfully")
        
        # Step 2: Inpaint each character using predefined masks
        mask_files = ["mask1.png", "mask2.png"]
        
        for i, character_prompt in enumerate(self.character_prompts):
            if i >= len(mask_files):
                print(f"⚠ Warning: No mask file available for character {i+1}, skipping")
                break
                
            print(f"Processing character {i+1}/{len(self.character_prompts)}")
            mask_path = mask_files[i]
            
            current_image = self.inpaint_character(current_image, character_prompt, mask_path)
            if not current_image:
                print(f"✗ Failed to inpaint character: {character_prompt}")
                return None
            
            print(f"✓ Character {i+1} inpainted successfully")
        
        print("🎉 Complete scene generation finished!")
        return current_image


# Example usage and testing
def main():
    """Example usage of the InvokeClient module"""
    
    # Example 1: Generate a scene with background and characters
    client = InvokeClient(
        background_prompt="sunny meadow with flowers and trees, peaceful landscape",
        character_prompts=[
            "cute rabbit sitting and eating a carrot",
            "colorful butterfly flying"
        ]
    )
    
    try:
        final_image = client.generate_complete_scene()
        if final_image:
            output_path = "./complete_scene.png"
            final_image.save(output_path)
            print(f"✓ Final scene saved to: {output_path}")
        else:
            print("✗ Scene generation failed")
            
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    main()