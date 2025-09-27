"""
Unified testing script for VoiceFrame Video Generator with Speech Bubbles
"""

import os
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Optional, Tuple

try:
    from video_gen import generate_video_from_scene_data, VoiceFrameVideoGenerator, SPEECH_BUBBLE_CONFIGS
except ImportError:
    print("Warning: Could not import video_gen. Make sure video_gen.py is in the same directory.")
    generate_video_from_scene_data = None
    VoiceFrameVideoGenerator = None
    SPEECH_BUBBLE_CONFIGS = {}

# Test configurations that match the structure expected by video_gen.py
TEST_CONFIGS = {
    "modern_bubbles": {
        "font_size": 22,
        "font_color": "white",
        "character_positions": {
            "Scorpion": {"side": "left", "max_width": 450, "tail_side": "left"},
            "Frog": {"side": "right", "max_width": 450, "tail_side": "right"}
        }
    },
    "compact_bubbles": {
        "font_size": 18,
        "font_color": "gold",
        "character_positions": {
            "Scorpion": {"side": "left", "max_width": 350, "tail_side": "left"},
            "Frog": {"side": "right", "max_width": 350, "tail_side": "right"}
        }
    },
    "large_bubbles": {
        "font_size": 26,
        "font_color": "cyan",
        "character_positions": {
            "Scorpion": {"side": "left", "max_width": 500, "tail_side": "left"},
            "Frog": {"side": "right", "max_width": 500, "tail_side": "right"}
        }
    },
    "classic_style": {
        "font_size": 20,
        "font_color": "white",
        "character_positions": {
            "Scorpion": {"side": "left", "max_width": 400, "tail_side": "left"},
            "Frog": {"side": "right", "max_width": 400, "tail_side": "right"}
        }
    }
}


def load_scene_data(base_dir: str) -> dict:
    """Load scene data from scene_data.json file"""
    scene_data_path = Path(base_dir) / "scene_data.json"
    
    if not scene_data_path.exists():
        print(f"Error: scene_data.json not found at {scene_data_path}")
        return {}
    
    try:
        with open(scene_data_path, 'r', encoding='utf-8') as f:
            scene_data = json.load(f)
        print(f"Successfully loaded scene data from {scene_data_path}")
        return scene_data
    except Exception as e:
        print(f"Error reading scene_data.json: {e}")
        return {}


def check_directory_structure(base_dir: str) -> bool:
    """Check if required directories and files exist"""
    base_path = Path(base_dir)
    
    print(f"Checking directory structure at: {base_path.absolute()}")
    
    if not base_path.exists():
        print(f"Base directory doesn't exist: {base_path}")
        return False
    
    scene_data_path = base_path / "scene_data.json"
    if not scene_data_path.exists():
        print("Missing scene_data.json")
        return False
    
    images_dir = base_path / "images"
    if not images_dir.exists():
        print("Missing images directory")
        return False
    
    image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.jpeg")) + list(images_dir.glob("*.png"))
    if not image_files:
        print("No image files found in images directory")
        return False
    
    print(f"Found {len(image_files)} image(s)")
    
    audio_dir = base_path / "audio"
    if audio_dir.exists():
        audio_files = list(audio_dir.glob("*.wav")) + list(audio_dir.glob("*.mp3")) + list(audio_dir.glob("*.m4a"))
        if audio_files:
            print(f"Found {len(audio_files)} audio file(s)")
        else:
            print("Audio directory exists but no audio files found")
    else:
        print("No audio directory found (video will be without audio)")
    
    return True


def run_video_generation_test(base_dir: str, config_name: str, config: dict):
    """Run video generation test using video_gen.py"""
    print(f"\n{'='*50}")
    print(f"TESTING: {config_name.upper()}")
    print(f"Font: {config['font_size']}px {config['font_color']}")
    print(f"Character positions: {list(config['character_positions'].keys())}")
    print('='*50)
    
    try:
        # Load scene data
        scene_data = load_scene_data(base_dir)
        if not scene_data:
            print("Cannot run test without scene data")
            return False
        
        # Create a custom output path for this test
        base_path = Path(base_dir)
        original_output = base_path / "video.mp4"
        test_output = base_path / f"test_video_{config_name}.mp4"
        
        # Temporarily rename any existing video.mp4
        backup_needed = False
        if original_output.exists():
            backup_path = base_path / "video_backup.mp4"
            original_output.rename(backup_path)
            backup_needed = True
        
        try:
            print(f"Calling generate_video_from_scene_data with scene data...")
            print(f"Scene contains {len(scene_data.get('scene', {}).get('dialogues', []))} dialogues")
            
            success = generate_video_from_scene_data(
                base_dir=base_dir,
                scene_data=scene_data,
                character_positions=config['character_positions']
            )
            
            if success and original_output.exists():
                # Move the generated video to test-specific name
                original_output.rename(test_output)
                print(f"Successfully generated: {test_output}")
                if test_output.exists():
                    print(f"Video size: {test_output.stat().st_size / (1024*1024):.2f} MB")
                return True
            else:
                print(f"Failed to generate video with {config_name} configuration")
                return False
                
        finally:
            # Restore backup if needed
            if backup_needed:
                backup_path = base_path / "video_backup.mp4"
                if backup_path.exists():
                    if not original_output.exists():  # Only restore if no new video was created
                        backup_path.rename(original_output)
                    else:
                        backup_path.unlink()  # Remove backup if new video exists
            
    except Exception as e:
        print(f"Error during {config_name} test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_audio_sync_functionality(base_dir: str):
    """Test audio synchronization functionality (core feature of main.py)"""
    print(f"\n{'='*60}")
    print("TESTING AUDIO SYNCHRONIZATION (main.py feature)")
    print('='*60)
    
    try:
        scene_data = load_scene_data(base_dir)
        if not scene_data:
            print("Cannot test audio sync without scene data")
            return False
        
        base_path = Path(base_dir)
        audio_dir = base_path / "audio"
        
        if not audio_dir.exists():
            print("No audio directory found - skipping audio sync test")
            return False
        
        audio_files = list(audio_dir.glob("*.wav")) + list(audio_dir.glob("*.mp3"))
        dialogues = scene_data.get('scene', {}).get('dialogues', [])
        
        print(f"Found {len(audio_files)} audio files for {len(dialogues)} dialogues")
        
        if len(audio_files) < len(dialogues):
            print("Not enough audio files for all dialogues - test may not be complete")
        
        generator = VoiceFrameVideoGenerator(base_dir)
        generator.output_path = base_path / "audio_sync_test.mp4"
        
        success = generator.generate_video_with_dialogues(
            scene_data=scene_data,
            character_positions=None,  # Use defaults
            font_size=20,
            font_color='gold'
        )
        
        if success:
            print("Audio synchronization test successful!")
            return True
        else:
            print("Audio synchronization test failed")
            return False
            
    except Exception as e:
        print(f"Error during audio sync test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("VoiceFrame Video Generator - Testing with video_gen.py module")
    print("="*70)
    
    if not generate_video_from_scene_data or not VoiceFrameVideoGenerator:
        print("Error: Could not import video_gen module. Please check that video_gen.py exists.")
        return
    
    # Get base directory
    import sys
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = input("Enter base directory path (or press Enter for current): ").strip()
        if not base_dir:
            base_dir = "."
    
    base_dir = os.path.abspath(base_dir)
    print(f"Using base directory: {base_dir}")
    
    # Check directory structure
    if not check_directory_structure(base_dir):
        print("\nDirectory structure check failed. Please fix the issues above.")
        return
    
    # Load and display scene data info
    scene_data = load_scene_data(base_dir)
    if scene_data and 'scene' in scene_data:
        scene = scene_data['scene']
        dialogues = scene.get('dialogues', [])
        print(f"\nScene Data Summary:")
        print(f"  Title: {scene.get('title', 'N/A')}")
        print(f"  Number of dialogues: {len(dialogues)}")
        if dialogues:
            characters = set(d.get('character', 'Unknown') for d in dialogues)
            print(f"  Characters: {', '.join(characters)}")
    
    print(f"\nRunning all {len(TEST_CONFIGS)} standard video generation tests...")
    success_count = 0
    
    for config_name, config in TEST_CONFIGS.items():
        if run_video_generation_test(base_dir, config_name, config):
            success_count += 1
    
    print(f"\nStandard Test Results: {success_count}/{len(TEST_CONFIGS)} tests passed")
    
    print("\nTesting completed!")


if __name__ == "__main__":
    main()