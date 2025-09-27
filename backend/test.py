"""
Unified testing script for VoiceFrame Video Generator with Speech Bubbles
Combines speech bubble rendering directly into video generation without intermediate steps
"""

import os
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Optional, Tuple

# Import your video generator (modify import as needed)
try:
    from video_gen import VoiceFrameVideoGenerator
except ImportError:
    print("Warning: Could not import video_gen. Make sure video_gen.py is in the same directory.")
    VoiceFrameVideoGenerator = None

# Integrated Speech Bubble Renderer (no separate image generation)
class IntegratedSpeechBubbleRenderer:
    """
    Speech bubble renderer integrated directly into video generation workflow
    """
    
    def __init__(self, font_size: int = 20, font_color: str = 'gold'):
        self.font_size = font_size
        self.font_color = font_color
        self.font_path = self._get_font_path()
    
    def _get_font_path(self) -> Optional[str]:
        """Find a suitable font file"""
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # Linux
            '/System/Library/Fonts/Arial.ttf',  # macOS
            'C:/Windows/Fonts/arial.ttf',  # Windows
            '/usr/share/fonts/TTF/arial.ttf',  # Some Linux distributions
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                return path
        return None
    
    def _get_text_dimensions(self, text: str, font) -> Tuple[int, int]:
        """Get accurate text dimensions"""
        try:
            bbox = font.getbbox(text)
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            return width, height
        except AttributeError:
            width, height = font.getsize(text)
            return width, height
    
    def _wrap_text(self, text: str, font, max_width: int) -> list:
        """Wrap text to fit within max_width"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            text_width, _ = self._get_text_dimensions(test_line, font)
            
            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def create_speech_bubble(self, text: str, max_width: int, 
                           padding: int = 12,
                           corner_radius: int = 18,
                           tail_side: str = "left") -> Image.Image:
        """
        Create speech bubble image for video overlay
        """
        # Load font
        try:
            if self.font_path:
                font = ImageFont.truetype(self.font_path, self.font_size)
            else:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Wrap text
        content_width = max_width - (2 * padding)
        lines = self._wrap_text(text, font, content_width)
        
        # Calculate dimensions
        line_height = self.font_size + 4
        text_height = len(lines) * line_height
        
        actual_text_width = 0
        for line in lines:
            line_width, _ = self._get_text_dimensions(line, font)
            actual_text_width = max(actual_text_width, line_width)
        
        # Bubble dimensions
        bubble_width = actual_text_width + (2 * padding)
        bubble_height = text_height + (2 * padding)
        
        # Add tail space
        tail_width = 15
        tail_height = 20
        img_width = bubble_width + tail_width
        img_height = bubble_height + tail_height
        
        # Create image
        img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate bubble position
        bubble_x = tail_width if tail_side == "left" else 0
        bubble_y = 0
        
        # Colors
        bg_color = (0, 0, 0, 220)
        border_color = (218, 165, 32, 255)
        
        # Draw rounded rectangle
        self._draw_rounded_rectangle(
            draw, 
            [bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height],
            corner_radius, 
            fill=bg_color, 
            outline=border_color,
            width=2
        )
        
        # Draw speech tail
        self._draw_speech_tail(draw, bubble_x, bubble_y, bubble_width, bubble_height, 
                             tail_side, bg_color, border_color)
        
        # Draw text
        text_color = self._parse_color(self.font_color)
        y_offset = bubble_y + padding
        
        for line in lines:
            line_width, _ = self._get_text_dimensions(line, font)
            x_offset = bubble_x + padding + (actual_text_width - line_width) // 2
            draw.text((x_offset, y_offset), line, font=font, fill=text_color)
            y_offset += line_height
        
        return img
    
    def _draw_rounded_rectangle(self, draw, coords, radius, fill=None, outline=None, width=1):
        """Draw rounded rectangle"""
        x1, y1, x2, y2 = coords
        
        # Main rectangle
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
        
        # Corners
        draw.pieslice([x1, y1, x1 + 2*radius, y1 + 2*radius], 180, 270, fill=fill)
        draw.pieslice([x2 - 2*radius, y1, x2, y1 + 2*radius], 270, 360, fill=fill)
        draw.pieslice([x1, y2 - 2*radius, x1 + 2*radius, y2], 90, 180, fill=fill)
        draw.pieslice([x2 - 2*radius, y2 - 2*radius, x2, y2], 0, 90, fill=fill)
        
        # Outline
        if outline:
            draw.rectangle([x1 + radius, y1, x2 - radius, y1 + width], fill=outline)
            draw.rectangle([x1 + radius, y2 - width, x2 - radius, y2], fill=outline)
            draw.rectangle([x1, y1 + radius, x1 + width, y2 - radius], fill=outline)
            draw.rectangle([x2 - width, y1 + radius, x2, y2 - radius], fill=outline)
    
    def _draw_speech_tail(self, draw, bubble_x, bubble_y, bubble_width, bubble_height, 
                         tail_side, bg_color, border_color):
        """Draw speech bubble tail"""
        tail_height = 20
        tail_width = 15
        
        if tail_side == "left":
            tail_points = [
                (bubble_x, bubble_y + bubble_height - 30),
                (bubble_x - tail_width, bubble_y + bubble_height - 10),
                (bubble_x, bubble_y + bubble_height - 10)
            ]
        else:
            tail_points = [
                (bubble_x + bubble_width, bubble_y + bubble_height - 30),
                (bubble_x + bubble_width + tail_width, bubble_y + bubble_height - 10),
                (bubble_x + bubble_width, bubble_y + bubble_height - 10)
            ]
        
        draw.polygon(tail_points, fill=bg_color)
        for i in range(len(tail_points)):
            start = tail_points[i]
            end = tail_points[(i + 1) % len(tail_points)]
            draw.line([start, end], fill=border_color, width=2)
    
    def _parse_color(self, color_str: str) -> tuple:
        """Parse color string to RGB tuple"""
        color_map = {
            'gold': (255, 215, 0, 255),
            'white': (255, 255, 255, 255),
            'black': (0, 0, 0, 255),
            'red': (255, 0, 0, 255),
            'green': (0, 255, 0, 255),
            'blue': (0, 0, 255, 255),
            'cyan': (0, 255, 255, 255),
            'orange': (255, 165, 0, 255),
            'purple': (128, 0, 128, 255),
        }
        return color_map.get(color_str.lower(), (255, 215, 0, 255))


# Enhanced Video Generator with Integrated Speech Bubbles
class EnhancedVoiceFrameGenerator:
    """
    Enhanced video generator that uses speech bubbles instead of plain text boxes
    """
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.images_dir = self.base_dir / 'images'
        self.audio_dir = self.base_dir / 'audio'
        self.output_path = self.base_dir / 'video.mp4'
    
    def generate_video_with_speech_bubbles(self, scene_data: Dict, 
                                         character_positions: Optional[Dict] = None,
                                         font_size: int = 20, 
                                         font_color: str = 'gold',
                                         padding: int = 12,
                                         corner_radius: int = 18) -> bool:
        """
        Generate video with speech bubble dialogues
        """
        try:
            # Import necessary modules here to avoid dependency issues
            from moviepy import ImageClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip
            from moviepy import vfx
            
            # Get background image
            background_image_path = self._get_background_image()
            if not background_image_path:
                print("No background image found")
                return False
            
            # Extract scene information
            scene_info = scene_data.get('scene', {})
            background_info = scene_info.get('background', {})
            dialogues = scene_info.get('dialogues', [])
            
            if not dialogues:
                print("No dialogues found in scene data")
                return False
            
            # Calculate video duration
            scene_end_time = background_info.get('end', '00:01:30')
            video_duration = self._convert_time_to_seconds(scene_end_time)
            print(f"Video duration: {video_duration} seconds")
            
            # Create background clip
            background_clip = ImageClip(background_image_path).with_duration(video_duration)
            W, H = background_clip.size
            print(f"Background size: {W}x{H}")
            
            # Default character positions
            if not character_positions:
                character_positions = {
                    "Scorpion": {"side": "left", "max_width": 400, "tail_side": "left"},
                    "Frog": {"side": "right", "max_width": 400, "tail_side": "right"}
                }
            
            # Create clips for each dialogue
            all_clips = [background_clip]
            
            for i, dialogue in enumerate(dialogues):
                try:
                    start_sec = self._convert_time_to_seconds(dialogue['start'])
                    end_sec = self._convert_time_to_seconds(dialogue['end'])
                    line_duration = end_sec - start_sec
                    
                    if line_duration <= 0:
                        print(f"Warning: Dialogue {i+1} has invalid duration, skipping")
                        continue
                    
                    # Get dialogue info
                    char_name = dialogue.get('character', 'Unknown')
                    line_text = dialogue.get('line', '')
                    text_content = f"{char_name}: {line_text}"
                    
                    # Get character positioning
                    char_config = character_positions.get(char_name, {
                        "side": "left", "max_width": 400, "tail_side": "left"
                    })
                    side = char_config.get("side", "left")
                    max_width = char_config.get("max_width", 400)
                    tail_side = char_config.get("tail_side", side)
                    
                    # Create speech bubble renderer
                    bubble_renderer = IntegratedSpeechBubbleRenderer(font_size, font_color)
                    
                    # Create speech bubble image
                    bubble_img = bubble_renderer.create_speech_bubble(
                        text=text_content,
                        max_width=max_width,
                        padding=padding,
                        corner_radius=corner_radius,
                        tail_side=tail_side
                    )
                    
                    # Save bubble image temporarily
                    temp_bubble_path = self.base_dir / f"temp_bubble_{i}.png"
                    bubble_img.save(temp_bubble_path)
                    
                    # Calculate position
                    margin = 40
                    bottom_margin = 60
                    
                    if side == "left":
                        bubble_x = margin
                    else:  # right side
                        bubble_x = W - margin - bubble_img.width
                    
                    bubble_y = H - bottom_margin - bubble_img.height
                    
                    # Create bubble clip with fade effects
                    fade_duration = min(0.2, line_duration / 6.0)
                    
                    bubble_clip = ImageClip(str(temp_bubble_path)).with_start(start_sec).with_duration(line_duration).with_position((bubble_x, bubble_y))
                    
                    # Add fade effects
                    if fade_duration > 0:
                        bubble_clip = bubble_clip.with_effects([vfx.FadeIn(fade_duration), vfx.FadeOut(fade_duration)])
                    
                    all_clips.append(bubble_clip)
                    print(f"Created speech bubble for {char_name}: {line_text[:50]}...")
                    
                except Exception as e:
                    print(f"Error creating dialogue {i+1}: {e}")
                    continue
            
            # Add audio if available
            audio_files = self._get_audio_files()
            if audio_files and len(audio_files) >= len(dialogues):
                print(f"Found {len(audio_files)} audio files for {len(dialogues)} dialogues")
                try:
                    synchronized_audio_clips = []
                    
                    for i, dialogue in enumerate(dialogues):
                        if i >= len(audio_files):
                            break
                            
                        start_sec = self._convert_time_to_seconds(dialogue['start'])
                        end_sec = self._convert_time_to_seconds(dialogue['end'])
                        expected_duration = end_sec - start_sec
                        
                        audio_file = audio_files[i]
                        audio_clip = AudioFileClip(audio_file)
                        
                        if abs(audio_clip.duration - expected_duration) > 0.1:
                            if audio_clip.duration > expected_duration:
                                audio_clip = audio_clip.with_duration(expected_duration)
                        
                        audio_clip = audio_clip.with_start(start_sec)
                        synchronized_audio_clips.append(audio_clip)
                    
                    combined_audio = CompositeAudioClip(synchronized_audio_clips)
                    final_clip = CompositeVideoClip(all_clips, size=(W, H)).with_audio(combined_audio)
                    print("Successfully synchronized audio with dialogue timing")
                    
                except Exception as e:
                    print(f"Error synchronizing audio: {e}")
                    final_clip = CompositeVideoClip(all_clips, size=(W, H))
            else:
                final_clip = CompositeVideoClip(all_clips, size=(W, H))
            
            # Render video
            print(f"Rendering video to {self.output_path}...")
            final_clip.write_videofile(
                str(self.output_path),
                fps=24,
                codec='libx264',
                audio_codec='aac' if audio_files else None
            )
            
            # Cleanup
            final_clip.close()
            for clip in all_clips:
                try:
                    clip.close()
                except:
                    pass
            
            # Clean up temporary bubble images
            for temp_file in self.base_dir.glob("temp_bubble_*.png"):
                try:
                    temp_file.unlink()
                except:
                    pass
            
            print(f"Video with speech bubbles generated successfully: {self.output_path}")
            return True
            
        except Exception as e:
            print(f"Error generating video: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_background_image(self) -> Optional[str]:
        """Get the first available background image"""
        if not self.images_dir.exists():
            return None
        
        image_files = sorted([f for f in os.listdir(self.images_dir) if f.endswith(('.jpeg', '.jpg', '.png'))], 
                           key=lambda x: int(x.split('.')[0]) if x.split('.')[0].isdigit() else 0)
        
        if image_files:
            return str(self.images_dir / image_files[0])
        return None
    
    def _get_audio_files(self) -> List[str]:
        """Get all audio files from audio directory"""
        if not self.audio_dir.exists():
            return []
        
        audio_files = sorted([f for f in os.listdir(self.audio_dir) if f.endswith(('.wav', '.mp3', '.m4a'))],
                           key=lambda x: int(x.split('.')[0]) if x.split('.')[0].isdigit() else 0)
        
        return [str(self.audio_dir / f) for f in audio_files]
    
    @staticmethod
    def _convert_time_to_seconds(time_str: str) -> float:
        """Convert time string to seconds"""
        if not isinstance(time_str, str):
            raise ValueError("Time must be a string like '00:01:23' or '1:23.45'")
        
        parts = [p.strip() for p in time_str.strip().split(':')]
        if len(parts) == 3:
            h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
            return h * 3600 + m * 60 + s
        elif len(parts) == 2:
            m, s = int(parts[0]), float(parts[1])
            return m * 60 + s
        elif len(parts) == 1:
            return float(parts[0])
        else:
            raise ValueError(f"Time string format '{time_str}' is invalid.")


# Test configurations with speech bubble settings
SPEECH_BUBBLE_TEST_CONFIGS = {
    "modern_bubbles": {
        "font_size": 22,
        "font_color": "white",
        "padding": 12,
        "corner_radius": 18,
        "character_positions": {
            "Scorpion": {"side": "left", "max_width": 450, "tail_side": "left"},
            "Frog": {"side": "right", "max_width": 450, "tail_side": "right"}
        }
    },
    "compact_bubbles": {
        "font_size": 18,
        "font_color": "gold",
        "padding": 10,
        "corner_radius": 15,
        "character_positions": {
            "Scorpion": {"side": "left", "max_width": 350, "tail_side": "left"},
            "Frog": {"side": "right", "max_width": 350, "tail_side": "right"}
        }
    },
    "large_bubbles": {
        "font_size": 26,
        "font_color": "cyan",
        "padding": 15,
        "corner_radius": 20,
        "character_positions": {
            "Scorpion": {"side": "left", "max_width": 500, "tail_side": "left"},
            "Frog": {"side": "right", "max_width": 500, "tail_side": "right"}
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


def run_speech_bubble_video_test(base_dir: str, config_name: str, config: dict):
    """Run video generation test with speech bubbles"""
    print(f"\n{'='*50}")
    print(f"TESTING: {config_name.upper()}")
    print(f"Font: {config['font_size']}px {config['font_color']}")
    print(f"Bubble: padding={config['padding']}, radius={config['corner_radius']}")
    print('='*50)
    
    try:
        scene_data = load_scene_data(base_dir)
        if not scene_data:
            print("Cannot run test without scene data")
            return False
        
        # Create enhanced generator
        generator = EnhancedVoiceFrameGenerator(base_dir)
        
        # Set output path for this test
        base_path = Path(base_dir)
        test_output = base_path / f"speech_bubble_video_{config_name}.mp4"
        generator.output_path = test_output
        
        # Generate video with speech bubbles
        success = generator.generate_video_with_speech_bubbles(
            scene_data=scene_data,
            character_positions=config['character_positions'],
            font_size=config['font_size'],
            font_color=config['font_color'],
            padding=config['padding'],
            corner_radius=config['corner_radius']
        )
        
        if success:
            print(f"Successfully generated: {test_output}")
            if test_output.exists():
                print(f"Video size: {test_output.stat().st_size / (1024*1024):.2f} MB")
            return True
        else:
            print(f"Failed to generate video with {config_name} configuration")
            return False
            
    except Exception as e:
        print(f"Error during {config_name} test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main unified testing function"""
    print("VoiceFrame Video Generator - Unified Speech Bubble Testing")
    print("="*65)
    
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
    
    # Show available test configurations
    print(f"\nAvailable Speech Bubble Test Configurations:")
    for i, (name, config) in enumerate(SPEECH_BUBBLE_TEST_CONFIGS.items(), 1):
        print(f"  {i}. {name} - {config['font_size']}px {config['font_color']}, padding={config['padding']}")
    
    print(f"  {len(SPEECH_BUBBLE_TEST_CONFIGS) + 1}. Run all tests")
    print(f"  0. Exit")
    
    while True:
        try:
            choice = input(f"\nSelect test to run (0-{len(SPEECH_BUBBLE_TEST_CONFIGS) + 1}): ").strip()
            
            if choice == "0":
                print("Exiting...")
                break
            elif choice == str(len(SPEECH_BUBBLE_TEST_CONFIGS) + 1):
                # Run all tests
                print(f"\nRunning all {len(SPEECH_BUBBLE_TEST_CONFIGS)} speech bubble configurations...")
                success_count = 0
                
                for config_name, config in SPEECH_BUBBLE_TEST_CONFIGS.items():
                    if run_speech_bubble_video_test(base_dir, config_name, config):
                        success_count += 1
                
                print(f"\nTest Results: {success_count}/{len(SPEECH_BUBBLE_TEST_CONFIGS)} tests passed")
                break
            else:
                # Run specific test
                config_names = list(SPEECH_BUBBLE_TEST_CONFIGS.keys())
                config_index = int(choice) - 1
                
                if 0 <= config_index < len(config_names):
                    config_name = config_names[config_index]
                    config = SPEECH_BUBBLE_TEST_CONFIGS[config_name]
                    run_speech_bubble_video_test(base_dir, config_name, config)
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
    
    print("\nTesting completed!")
    print("Speech bubble videos generated directly without intermediate image steps.")


if __name__ == "__main__":
    main()