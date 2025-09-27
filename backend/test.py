"""
Testing script for VoiceFrame Video Generator
Tests video generation with various configurations and parameter adjustments
"""

import os
import json
from pathlib import Path
from video_gen import VoiceFrameVideoGenerator, generate_video_from_scene_data, ImprovedTextRenderer

# Test configurations for different scenarios
TEST_CONFIGS = {
    "basic_test": {
        "font_size": 20,
        "font_color": "gold",
        "character_positions": {
            "Scorpion": {"side": "left", "max_width": 400, "tail_side": "left"},
            "Frog": {"side": "right", "max_width": 400, "tail_side": "right"}
        }
    },
    "large_text": {
        "font_size": 24,
        "font_color": "white",
        "character_positions": {
            "Scorpion": {"side": "left", "max_width": 500, "tail_side": "left"},
            "Frog": {"side": "right", "max_width": 500, "tail_side": "right"}
        }
    },
    "small_text": {
        "font_size": 16,
        "font_color": "gold",
        "character_positions": {
            "Scorpion": {"side": "left", "max_width": 350, "tail_side": "left"},
            "Frog": {"side": "right", "max_width": 350, "tail_side": "right"}
        }
    },
    "center_positioning": {
        "font_size": 18,
        "font_color": "red",
        "character_positions": {
            "Narrator": {"side": "center", "max_width": 600}
        }
    }
}


def load_scene_data(base_dir: str) -> dict:
    """Load scene data from scene_data.json file"""
    scene_data_path = Path(base_dir) / "scene_data.json"
    
    if not scene_data_path.exists():
        print(f"Error: scene_data.json not found at {scene_data_path}")
        print("Please ensure the scene_data.json file exists in your base directory")
        return {}
    
    try:
        with open(scene_data_path, 'r', encoding='utf-8') as f:
            scene_data = json.load(f)
        print(f"✓ Successfully loaded scene data from {scene_data_path}")
        return scene_data
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in scene_data.json: {e}")
        return {}
    except Exception as e:
        print(f"Error reading scene_data.json: {e}")
        return {}


def check_directory_structure(base_dir: str) -> bool:
    """Check if required directories and files exist"""
    base_path = Path(base_dir)
    
    print(f"Checking directory structure at: {base_path.absolute()}")
    
    # Check base directory
    if not base_path.exists():
        print(f"❌ Base directory doesn't exist: {base_path}")
        return False
    
    # Check for scene_data.json
    scene_data_path = base_path / "scene_data.json"
    if scene_data_path.exists():
        print(f"✓ Found scene_data.json")
    else:
        print(f"❌ Missing scene_data.json")
        return False
    
    # Check images directory
    images_dir = base_path / "images"
    if images_dir.exists():
        image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.jpeg")) + list(images_dir.glob("*.png"))
        image_files += list(images_dir.glob("*.JPG")) + list(images_dir.glob("*.JPEG")) + list(images_dir.glob("*.PNG"))
        
        if image_files:
            print(f"✓ Found images directory with {len(image_files)} image(s)")
            for img in image_files[:5]:  # Show first 5 images
                print(f"  - {img.name}")
            if len(image_files) > 5:
                print(f"  ... and {len(image_files) - 5} more")
        else:
            print(f"❌ Images directory exists but contains no image files")
            return False
    else:
        print(f"❌ Missing images directory")
        return False
    
    # Check audio directory (optional)
    audio_dir = base_path / "audio"
    if audio_dir.exists():
        audio_files = list(audio_dir.glob("*.wav")) + list(audio_dir.glob("*.mp3")) + list(audio_dir.glob("*.m4a"))
        audio_files += list(audio_dir.glob("*.WAV")) + list(audio_dir.glob("*.MP3")) + list(audio_dir.glob("*.M4A"))
        
        if audio_files:
            print(f"✓ Found audio directory with {len(audio_files)} audio file(s)")
            for audio in audio_files[:3]:  # Show first 3 audio files
                print(f"  - {audio.name}")
            if len(audio_files) > 3:
                print(f"  ... and {len(audio_files) - 3} more")
        else:
            print(f"⚠ Audio directory exists but contains no audio files")
    else:
        print(f"⚠ No audio directory found (video will be generated without audio)")
    
    print(f"✓ Directory structure check passed")
    return True


def test_text_rendering(base_dir: str):
    """Test different text rendering configurations"""
    print("\n" + "="*60)
    print("TESTING TEXT RENDERING CONFIGURATIONS")
    print("="*60)
    
    # Initialize text renderer with different configs
    renderers = {
        "small": ImprovedTextRenderer(font_size=16, font_color='gold'),
        "medium": ImprovedTextRenderer(font_size=24, font_color='white'),
        "large": ImprovedTextRenderer(font_size=32, font_color='red'),
        "extra_large": ImprovedTextRenderer(font_size=48, font_color='blue')
    }
    
    test_text = "This is a sample dialogue text that will be rendered with different configurations."
    base_path = Path(base_dir)
    
    for name, renderer in renderers.items():
        try:
            print(f"\nTesting {name} text renderer (size: {renderer.font_size}, color: {renderer.font_color})")
            text_img = renderer.create_text_image(test_text, max_width=400)
            
            # Save test image
            test_img_path = base_path / f"test_text_{name}.png"
            text_img.save(test_img_path)
            print(f"✓ Saved test image: {test_img_path}")
            print(f"  Image size: {text_img.width}x{text_img.height}")
            
        except Exception as e:
            print(f"❌ Error with {name} renderer: {e}")


def run_video_test(base_dir: str, config_name: str, config: dict):
    """Run a single video generation test with given configuration"""
    print(f"\n" + "-"*50)
    print(f"TESTING: {config_name.upper()}")
    print(f"Font Size: {config['font_size']}")
    print(f"Font Color: {config['font_color']}")
    print(f"Character Positions: {config['character_positions']}")
    print("-"*50)
    
    try:
        # Load scene data
        scene_data = load_scene_data(base_dir)
        if not scene_data:
            print(f"❌ Cannot run test without scene data")
            return False
        
        # Create generator
        generator = VoiceFrameVideoGenerator(base_dir)
        
        # Set output path for this test
        base_path = Path(base_dir)
        test_output = base_path / f"test_video_{config_name}.mp4"
        generator.output_path = test_output
        
        # Generate video with custom configuration
        success = generator.generate_video_with_dialogues(
            scene_data=scene_data,
            character_positions=config['character_positions'],
            font_size=config['font_size'],
            font_color=config['font_color']
        )
        
        if success:
            print(f"✓ Successfully generated: {test_output}")
            if test_output.exists():
                print(f"  Video size: {test_output.stat().st_size / (1024*1024):.2f} MB")
            return True
        else:
            print(f"❌ Failed to generate video with {config_name} configuration")
            return False
            
    except Exception as e:
        print(f"❌ Error during {config_name} test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main testing function"""
    print("VoiceFrame Video Generator - Testing Suite")
    print("="*60)
    
    # Get base directory from user or use current directory
    import sys
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = input("Enter the base directory path (or press Enter for current directory): ").strip()
        if not base_dir:
            base_dir = "."
    
    base_dir = os.path.abspath(base_dir)
    print(f"Using base directory: {base_dir}")
    
    # Check directory structure
    if not check_directory_structure(base_dir):
        print("\n❌ Directory structure check failed. Please fix the issues above.")
        return
    
    # Test text rendering
    test_text_rendering(base_dir)
    
    # Load and display scene data info
    scene_data = load_scene_data(base_dir)
    if scene_data and 'scene' in scene_data:
        scene = scene_data['scene']
        dialogues = scene.get('dialogues', [])
        print(f"\n📊 Scene Data Summary:")
        print(f"  Title: {scene.get('title', 'N/A')}")
        print(f"  Number of dialogues: {len(dialogues)}")
        if dialogues:
            characters = set(d.get('character', 'Unknown') for d in dialogues)
            print(f"  Characters: {', '.join(characters)}")
    
    # Ask user which tests to run
    print(f"\n🎬 Available Test Configurations:")
    for i, (name, config) in enumerate(TEST_CONFIGS.items(), 1):
        print(f"  {i}. {name} - Font: {config['font_size']}px {config['font_color']}")
    
    print(f"  {len(TEST_CONFIGS) + 1}. Run all tests")
    print(f"  0. Exit")
    
    while True:
        try:
            choice = input(f"\nSelect test to run (0-{len(TEST_CONFIGS) + 1}): ").strip()
            
            if choice == "0":
                print("Exiting...")
                break
            elif choice == str(len(TEST_CONFIGS) + 1):
                # Run all tests
                print(f"\n🚀 Running all {len(TEST_CONFIGS)} test configurations...")
                success_count = 0
                
                for config_name, config in TEST_CONFIGS.items():
                    if run_video_test(base_dir, config_name, config):
                        success_count += 1
                
                print(f"\n📈 Test Results: {success_count}/{len(TEST_CONFIGS)} tests passed")
                break
            else:
                # Run specific test
                config_names = list(TEST_CONFIGS.keys())
                config_index = int(choice) - 1
                
                if 0 <= config_index < len(config_names):
                    config_name = config_names[config_index]
                    config = TEST_CONFIGS[config_name]
                    run_video_test(base_dir, config_name, config)
                else:
                    print("Invalid choice. Please try again.")
                    continue
            
            # Ask if user wants to run another test
            another = input("\nRun another test? (y/n): ").strip().lower()
            if another != 'y':
                break
                
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()