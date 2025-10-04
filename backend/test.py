"""
Test script for video generation
Reads scene_data.json and passes to video generation module
"""

import os
import json
from video_gen import generate_video_from_scene_data, SPEECH_BUBBLE_CONFIGS

# Get the current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    print("=" * 60)
    print("VIDEO GENERATION TEST")
    print("=" * 60)
    
    # Load scene data
    scene_json_path = os.path.join(BASE_DIR, "scene_data.json")
    print(f"\nLoading scene data from: {scene_json_path}")
    
    with open(scene_json_path, 'r') as f:
        scene_data = json.load(f)
    
    # Extract characters to create dynamic positions
    scene_info = scene_data.get('scene', {})
    characters = scene_info.get('characters', [])
    dialogues = scene_info.get('dialogues', [])
    
    print(f"Found {len(characters)} characters")
    print(f"Found {len(dialogues)} dialogues")
    
    # Create character positions dynamically
    # Map characters to their visual position in the generated image
    character_positions = {}
    
    # Check character order and assign positions based on actual visual layout
    for i, character in enumerate(characters):
        char_name = character.get('name', f'Character_{i+1}')
        
        # Manually assign based on character name to match image layout
        # Adjust these based on where characters actually appear in your image
        if char_name == "Scorpion":
            side = "left"  # Scorpion appears on left in image
        elif char_name == "Frog":
            side = "right"  # Frog appears on right in image
        else:
            # Fallback: alternate for any other characters
            side = "left" if i % 2 == 0 else "right"
        
        character_positions[char_name] = {
            "side": side,
            "max_width": 450,
            "tail_side": side
        }
        print(f"  - {char_name}: {side} side")
    
    # Generate video with copyright watermark
    print(f"\nGenerating video...")
    print(f"Images folder: {os.path.join(BASE_DIR, 'images')}")
    print(f"Audio folder: {os.path.join(BASE_DIR, 'audio')}")
    print(f"Output: {os.path.join(BASE_DIR, 'video.mp4')}")
    print(f"Copyright: © 2025 All Rights Reserved")
    
    success = generate_video_from_scene_data(
        base_dir=BASE_DIR,
        scene_data=scene_data,
        character_positions=character_positions,
        copyright_text="© 2025 All Rights Reserved"  # Optional: customize this
    )
    
    if success:
        print("\n" + "=" * 60)
        print("✓ VIDEO GENERATION SUCCESSFUL!")
        print(f"Output saved to: {os.path.join(BASE_DIR, 'video.mp4')}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ VIDEO GENERATION FAILED")
        print("=" * 60)

if __name__ == "__main__":
    main()