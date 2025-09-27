"""
Testing script for improved speech bubble text renderer
This tests the new speech bubble styling before integrating into video_gen.py
"""

import os
import json
from pathlib import Path
from PIL import Image

# Import the improved renderer
from video_gen import ImprovedTextRenderer, SPEECH_BUBBLE_CONFIGS

def test_speech_bubbles(base_dir: str = "."):
    """Test different speech bubble configurations"""
    base_path = Path(base_dir)
    
    # Test texts
    test_texts = [
        "Hello there! How are you doing today?",
        "This is a longer message that should wrap to multiple lines when rendered in the speech bubble.",
        "Short text",
        "Why would I help you cross the river? You'll sting me and we'll both drown!",
        "I couldn't help it. It's my nature."
    ]
    
    print("Testing Speech Bubble Configurations...")
    print("="*50)
    
    for config_name, config in SPEECH_BUBBLE_CONFIGS.items():
        print(f"\nTesting: {config_name}")
        print(f"Font size: {config['font_size']}, Color: {config['font_color']}")
        
        # Create renderer
        renderer = ImprovedTextRenderer(
            font_size=config['font_size'],
            font_color=config['font_color']
        )
        
        # Test each text sample
        for i, text in enumerate(test_texts):
            for char_name, char_config in config['character_positions'].items():
                try:
                    # Create speech bubble
                    bubble_img = renderer.create_speech_bubble(
                        text=f"{char_name}: {text}",
                        max_width=char_config['max_width'],
                        padding=config['padding'],
                        corner_radius=config['corner_radius'],
                        add_tail=True,
                        tail_side=char_config['tail_side']
                    )
                    
                    # Save test image
                    output_name = f"bubble_test_{config_name}_{char_name}_{i+1}.png"
                    output_path = base_path / output_name
                    bubble_img.save(output_path)
                    
                    print(f"  ✓ Saved: {output_name} ({bubble_img.width}x{bubble_img.height})")
                    
                except Exception as e:
                    print(f"  ❌ Error creating bubble for {char_name}: {e}")
    
    print(f"\n✓ Speech bubble tests completed. Check the generated PNG files!")


def create_comparison_image(base_dir: str = "."):
    """Create a side-by-side comparison of different bubble styles"""
    base_path = Path(base_dir)
    
    print("\nCreating comparison image...")
    
    test_text = "This is a sample dialogue to compare different speech bubble styles."
    
    # Create renderers for each config
    bubble_images = []
    labels = []
    
    for config_name, config in SPEECH_BUBBLE_CONFIGS.items():
        renderer = ImprovedTextRenderer(
            font_size=config['font_size'],
            font_color=config['font_color']
        )
        
        bubble_img = renderer.create_speech_bubble(
            text=test_text,
            max_width=350,
            padding=config['padding'],
            corner_radius=config['corner_radius'],
            add_tail=True,
            tail_side="left"
        )
        
        bubble_images.append(bubble_img)
        labels.append(config_name)
    
    # Calculate comparison image size
    max_width = max(img.width for img in bubble_images)
    total_height = sum(img.height for img in bubble_images) + (len(bubble_images) - 1) * 20  # 20px spacing
    
    # Create comparison image
    comparison = Image.new('RGBA', (max_width + 100, total_height + 50), (240, 240, 240, 255))
    
    y_offset = 25
    for i, (img, label) in enumerate(zip(bubble_images, labels)):
        # Paste bubble image
        x_offset = (max_width - img.width) // 2 + 50
        comparison.paste(img, (x_offset, y_offset), img)
        
        # Add label (simple text overlay - could be improved with PIL text)
        print(f"  {label}: {img.width}x{img.height} at position ({x_offset}, {y_offset})")
        
        y_offset += img.height + 20
    
    # Save comparison
    comparison_path = base_path / "speech_bubble_comparison.png"
    comparison.save(comparison_path)
    print(f"✓ Saved comparison image: {comparison_path}")


def test_with_scene_data(base_dir: str):
    """Test speech bubbles with actual scene data"""
    scene_data_path = Path(base_dir) / "scene_data.json"
    
    if not scene_data_path.exists():
        print("No scene_data.json found. Skipping scene data test.")
        return
    
    try:
        with open(scene_data_path, 'r', encoding='utf-8') as f:
            scene_data = json.load(f)
    except Exception as e:
        print(f"Error reading scene_data.json: {e}")
        return
    
    print(f"\nTesting with actual scene data...")
    
    scene = scene_data.get('scene', {})
    dialogues = scene.get('dialogues', [])
    
    if not dialogues:
        print("No dialogues found in scene data.")
        return
    
    # Use the first config for testing
    config_name = "modern_bubbles"
    config = SPEECH_BUBBLE_CONFIGS[config_name]
    
    renderer = ImprovedTextRenderer(
        font_size=config['font_size'],
        font_color=config['font_color']
    )
    
    base_path = Path(base_dir)
    
    for i, dialogue in enumerate(dialogues[:3]):  # Test first 3 dialogues
        character = dialogue.get('character', 'Unknown')
        line = dialogue.get('line', '')
        
        # Get character config or use default
        char_positions = config['character_positions']
        if character in char_positions:
            char_config = char_positions[character]
        else:
            # Default config for unknown characters
            char_config = {"side": "left", "max_width": 400, "tail_side": "left"}
        
        try:
            bubble_img = renderer.create_speech_bubble(
                text=f"{character}: {line}",
                max_width=char_config['max_width'],
                padding=config['padding'],
                corner_radius=config['corner_radius'],
                add_tail=True,
                tail_side=char_config['tail_side']
            )
            
            # Save scene dialogue bubble
            output_name = f"scene_bubble_{character}_{i+1}.png"
            output_path = base_path / output_name
            bubble_img.save(output_path)
            
            print(f"  ✓ Created bubble for {character}: {output_name}")
            print(f"    Text: {line[:50]}{'...' if len(line) > 50 else ''}")
            
        except Exception as e:
            print(f"  ❌ Error creating bubble for {character}: {e}")


def main():
    """Main testing function"""
    print("Speech Bubble Text Renderer - Test Suite")
    print("="*50)
    
    # Get base directory
    import sys
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = input("Enter base directory (or press Enter for current): ").strip()
        if not base_dir:
            base_dir = "."
    
    base_dir = os.path.abspath(base_dir)
    print(f"Using directory: {base_dir}")
    
    # Run tests
    print("\n1. Testing speech bubble configurations...")
    test_speech_bubbles(base_dir)
    
    print("\n2. Creating comparison image...")
    create_comparison_image(base_dir)
    
    print("\n3. Testing with scene data...")
    test_with_scene_data(base_dir)
    
    print(f"\n🎉 All tests completed!")
    print(f"Check the generated PNG files in {base_dir} to see the results.")
    print(f"\nKey improvements in speech bubbles:")
    print(f"  ✓ Tight padding - no excessive whitespace")
    print(f"  ✓ Proper text centering within bubbles")
    print(f"  ✓ Rounded corners and speech tails")
    print(f"  ✓ Accurate text measurement and wrapping")
    print(f"  ✓ Dynamic sizing based on actual text content")


if __name__ == "__main__":
    main()