"""
Video Generator Module for VoiceFrame
Converts scene data, generated images, and audio files into videos with text overlays
Uses PIL and OpenCV instead of ImageMagick for better compatibility
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

# Import moviepy v2.x modules (no ImageMagick dependency needed)
from moviepy import ImageClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip
from moviepy import vfx


class ImprovedTextRenderer:
    """
    Improved text renderer with speech bubble styling and better text alignment
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
        """Get accurate text dimensions using textbbox"""
        try:
            # Use textbbox for more accurate measurements (PIL 8.0.0+)
            bbox = font.getbbox(text)
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            return width, height
        except AttributeError:
            # Fallback for older PIL versions
            width, height = font.getsize(text)
            return width, height
    
    def _wrap_text(self, text: str, font, max_width: int) -> list:
        """Wrap text to fit within max_width with accurate measurements"""
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
                           bg_color: tuple = (0, 0, 0, 220),
                           border_color: tuple = (218, 165, 32, 255),
                           padding: int = 15,
                           corner_radius: int = 15,
                           add_tail: bool = True,
                           tail_side: str = "left") -> Image.Image:
        """
        Create a speech bubble-style text image
        
        Args:
            text: Text to render
            max_width: Maximum width for text wrapping
            bg_color: Background color (R, G, B, A)
            border_color: Border color (R, G, B, A)  
            padding: Internal padding around text
            corner_radius: Radius for rounded corners
            add_tail: Whether to add speech bubble tail
            tail_side: Which side to add tail ("left" or "right")
        
        Returns:
            PIL Image with speech bubble and text
        """
        # Load font
        try:
            if self.font_path:
                font = ImageFont.truetype(self.font_path, self.font_size)
            else:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Wrap text with accurate measurements
        content_width = max_width - (2 * padding)
        lines = self._wrap_text(text, font, content_width)
        
        # Calculate actual text dimensions
        line_height = self.font_size + 4  # Reduced line spacing
        text_height = len(lines) * line_height
        
        # Find the actual width needed (not max_width)
        actual_text_width = 0
        for line in lines:
            line_width, _ = self._get_text_dimensions(line, font)
            actual_text_width = max(actual_text_width, line_width)
        
        # Calculate bubble dimensions based on actual text size
        bubble_width = actual_text_width + (2 * padding)
        bubble_height = text_height + (2 * padding)
        
        # Add space for tail if needed
        tail_height = 20
        tail_width = 15
        
        if add_tail:
            img_width = bubble_width + tail_width
            img_height = bubble_height + tail_height
        else:
            img_width = bubble_width
            img_height = bubble_height
        
        # Create image with transparent background
        img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate bubble position
        if add_tail and tail_side == "right":
            bubble_x = 0
        else:
            bubble_x = tail_width if add_tail else 0
            
        bubble_y = 0
        
        # Draw rounded rectangle for speech bubble
        self._draw_rounded_rectangle(
            draw, 
            [bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height],
            corner_radius, 
            fill=bg_color, 
            outline=border_color,
            width=2
        )
        
        # Draw speech bubble tail
        if add_tail:
            self._draw_speech_tail(draw, bubble_x, bubble_y, bubble_width, bubble_height, 
                                 tail_side, bg_color, border_color)
        
        # Draw text centered in bubble
        text_color = self._parse_color(self.font_color)
        y_offset = bubble_y + padding
        
        for line in lines:
            line_width, _ = self._get_text_dimensions(line, font)
            # Center each line horizontally
            x_offset = bubble_x + padding + (actual_text_width - line_width) // 2
            
            draw.text((x_offset, y_offset), line, font=font, fill=text_color)
            y_offset += line_height
        
        return img
    
    def _draw_rounded_rectangle(self, draw, coords, radius, fill=None, outline=None, width=1):
        """Draw a rounded rectangle"""
        x1, y1, x2, y2 = coords
        
        # Draw the main rectangle
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
        
        # Draw corners
        draw.pieslice([x1, y1, x1 + 2*radius, y1 + 2*radius], 180, 270, fill=fill)
        draw.pieslice([x2 - 2*radius, y1, x2, y1 + 2*radius], 270, 360, fill=fill)
        draw.pieslice([x1, y2 - 2*radius, x1 + 2*radius, y2], 90, 180, fill=fill)
        draw.pieslice([x2 - 2*radius, y2 - 2*radius, x2, y2], 0, 90, fill=fill)
        
        # Draw outline if specified
        if outline:
            # Main rectangle outlines
            draw.rectangle([x1 + radius, y1, x2 - radius, y1 + width], fill=outline)  # top
            draw.rectangle([x1 + radius, y2 - width, x2 - radius, y2], fill=outline)  # bottom
            draw.rectangle([x1, y1 + radius, x1 + width, y2 - radius], fill=outline)  # left
            draw.rectangle([x2 - width, y1 + radius, x2, y2 - radius], fill=outline)  # right
            
            # Corner outlines
            draw.arc([x1, y1, x1 + 2*radius, y1 + 2*radius], 180, 270, fill=outline, width=width)
            draw.arc([x2 - 2*radius, y1, x2, y1 + 2*radius], 270, 360, fill=outline, width=width)
            draw.arc([x1, y2 - 2*radius, x1 + 2*radius, y2], 90, 180, fill=outline, width=width)
            draw.arc([x2 - 2*radius, y2 - 2*radius, x2, y2], 0, 90, fill=outline, width=width)
    
    def _draw_speech_tail(self, draw, bubble_x, bubble_y, bubble_width, bubble_height, 
                         tail_side, bg_color, border_color):
        """Draw speech bubble tail"""
        tail_height = 20
        tail_width = 15
        
        if tail_side == "left":
            # Tail pointing left
            tail_points = [
                (bubble_x, bubble_y + bubble_height - 30),  # Top of tail
                (bubble_x - tail_width, bubble_y + bubble_height - 10),  # Tip of tail
                (bubble_x, bubble_y + bubble_height - 10)   # Bottom of tail
            ]
        else:  # right
            # Tail pointing right
            tail_points = [
                (bubble_x + bubble_width, bubble_y + bubble_height - 30),  # Top of tail
                (bubble_x + bubble_width + tail_width, bubble_y + bubble_height - 10),  # Tip of tail
                (bubble_x + bubble_width, bubble_y + bubble_height - 10)   # Bottom of tail
            ]
        
        # Draw filled tail
        draw.polygon(tail_points, fill=bg_color)
        
        # Draw tail outline
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

# Updated configuration for speech bubbles
SPEECH_BUBBLE_CONFIGS = {
    "classic_bubbles": {
        "font_size": 22,
        "font_color": "white",
        "padding": 12,
        "corner_radius": 18,
        "character_positions": {
            "Scorpion": {"side": "left", "max_width": 400, "tail_side": "left"},
            "Frog": {"side": "right", "max_width": 400, "tail_side": "right"}
        }
    },
    "modern_bubbles": {
        "font_size": 20,
        "font_color": "gold",
        "padding": 15,
        "corner_radius": 20,
        "character_positions": {
            "Scorpion": {"side": "left", "max_width": 450, "tail_side": "left"},
            "Frog": {"side": "right", "max_width": 450, "tail_side": "right"}
        }
    },
    "compact_bubbles": {
        "font_size": 18,
        "font_color": "white",
        "padding": 10,
        "corner_radius": 15,
        "character_positions": {
            "Scorpion": {"side": "left", "max_width": 350, "tail_side": "left"},
            "Frog": {"side": "right", "max_width": 350, "tail_side": "right"}
        }
    }
}

class VoiceFrameVideoGenerator:
    """
    Video generator specifically designed for VoiceFrame project
    Handles images from InvokeAI and audio files for dialogue
    """
    
    def __init__(self, base_dir: str):
        """
        Initialize the video generator
        
        Args:
            base_dir: Base directory containing images and audio folders
        """
        self.base_dir = Path(base_dir)
        self.images_dir = self.base_dir / 'images'
        self.audio_dir = self.base_dir / 'audio'
        self.output_path = self.base_dir / 'video.mp4'
        self.text_renderer = ImprovedTextRenderer()
    
    @staticmethod
    def convert_time_to_seconds(time_str: str) -> float:
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
    

    
    def get_background_image(self) -> Optional[str]:
        """Get the first available background image"""
        if not self.images_dir.exists():
            return None
        
        # Look for generated images (typically numbered)
        image_files = sorted([f for f in os.listdir(self.images_dir) if f.endswith(('.jpeg', '.jpg', '.png'))], 
                           key=lambda x: int(x.split('.')[0]) if x.split('.')[0].isdigit() else 0)
        
        if image_files:
            return str(self.images_dir / image_files[0])
        return None
    
    def get_audio_files(self) -> List[str]:
        """Get all audio files from audio directory"""
        if not self.audio_dir.exists():
            return []
        
        audio_files = sorted([f for f in os.listdir(self.audio_dir) if f.endswith(('.wav', '.mp3', '.m4a'))],
                           key=lambda x: int(x.split('.')[0]) if x.split('.')[0].isdigit() else 0)
        
        return [str(self.audio_dir / f) for f in audio_files]
    
    def generate_video_with_dialogues(self, scene_data: Dict, 
                                    character_positions: Optional[Dict] = None,
                                    font_size: int = 20, 
                                    font_color: str = 'gold') -> bool:
        """
        Generate video with dialogue overlays from scene data
        
        Args:
            scene_data: Scene data from Gemini containing dialogues
            character_positions: Character positioning configuration
            font_size: Font size for dialogue text
            font_color: Color of dialogue text
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get background image
            background_image_path = self.get_background_image()
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
            video_duration = self.convert_time_to_seconds(scene_end_time)
            print(f"Video duration: {video_duration} seconds")
            
            # Create background clip
            background_clip = ImageClip(background_image_path).with_duration(video_duration)
            W, H = background_clip.size
            print(f"Background size: {W}x{H}")
            
            # Default character positions
            if not character_positions:
                character_positions = {
                    "Scorpion": {
                        "side": "left", 
                        "max_width": 400,
                        "tail_side": "left"  # ADD THIS
                    },
                    "Frog": {
                        "side": "right", 
                        "max_width": 400,
                        "tail_side": "right"  # ADD THIS
                    }
                }
            
            # Create clips for each dialogue
            all_clips = [background_clip]
            
            for i, dialogue in enumerate(dialogues):
                try:
                    start_sec = self.convert_time_to_seconds(dialogue['start'])
                    end_sec = self.convert_time_to_seconds(dialogue['end'])
                    line_duration = end_sec - start_sec
                    
                    if line_duration <= 0:
                        print(f"Warning: Dialogue {i+1} has invalid duration, skipping")
                        continue
                    
                    # Get dialogue info
                    char_name = dialogue.get('character', 'Unknown')
                    line_text = dialogue.get('line', '')
                    text_content = f"{char_name}: {line_text}"
                    
                    # Get character positioning
                    char_config = character_positions.get(char_name, {"side": "left", "max_width": 400})
                    side = char_config.get("side", "left")
                    max_width = char_config.get("max_width", 400)
                    
                    # # Create text image using PIL (includes background and border)
                    # text_renderer = TextRenderer(font_size, font_color)
                    # text_img = text_renderer.create_text_image(text_content, max_width)
                    
                    # NEW CODE - Create speech bubble instead of plain text box
                    text_renderer = ImprovedTextRenderer(font_size, font_color)

                    # Get tail side from character config (or default to left)
                    tail_side = char_config.get("tail_side", "left" if side == "left" else "right")

                    # Create speech bubble with proper styling
                    text_img = text_renderer.create_speech_bubble(
                        text=text_content,
                        max_width=max_width,
                        padding=12,  # Reduced padding for tighter boxes
                        corner_radius=18,
                        add_tail=True,
                        tail_side=tail_side
                    )
                    # Save text image temporarily
                    temp_text_path = self.base_dir / f"temp_text_{i}.png"
                    text_img.save(temp_text_path)
                    
                    # Calculate position
                    margin = 40
                    bottom_margin = 60
                    
                    if side == "left":
                        text_x = margin
                    else:  # right side
                        text_x = W - margin - text_img.width
                    
                    text_y = H - bottom_margin - text_img.height
                    
                    # Create text clip from PIL image with fade effects
                    fade_duration = min(0.2, line_duration / 6.0)
                    
                    text_clip = ImageClip(str(temp_text_path)).with_start(start_sec).with_duration(line_duration).with_position((text_x, text_y))
                    
                    # Add fade effects using new v2.x API
                    if fade_duration > 0:
                        text_clip = text_clip.with_effects([vfx.FadeIn(fade_duration), vfx.FadeOut(fade_duration)])
                    
                    all_clips.append(text_clip)
                    print(f"Created dialogue for {char_name}: {line_text[:50]}...")
                    
                except Exception as e:
                    print(f"Error creating dialogue {i+1}: {e}")
                    continue
            
            # Add synchronized audio if available
            audio_files = self.get_audio_files()
            if audio_files and len(audio_files) >= len(dialogues):
                print(f"Found {len(audio_files)} audio files for {len(dialogues)} dialogues")
                try:
                    # Create synchronized audio clips
                    synchronized_audio_clips = []
                    
                    for i, dialogue in enumerate(dialogues):
                        if i >= len(audio_files):
                            break
                            
                        # Get dialogue timing
                        start_sec = self.convert_time_to_seconds(dialogue['start'])
                        end_sec = self.convert_time_to_seconds(dialogue['end'])
                        expected_duration = end_sec - start_sec
                        
                        print(f"Processing audio {i+1}: {dialogue['character']} from {start_sec:.2f}s to {end_sec:.2f}s (expected: {expected_duration:.2f}s)")
                        
                        # Load the audio file
                        audio_file = audio_files[i]
                        audio_clip = AudioFileClip(audio_file)
                        actual_duration = audio_clip.duration
                        
                        print(f"  Audio file duration: {actual_duration:.2f}s, expected: {expected_duration:.2f}s")
                        
                        # Adjust audio duration to match expected timing
                        if abs(actual_duration - expected_duration) > 0.1:  # If difference > 0.1 seconds
                            if actual_duration > expected_duration:
                                # Audio is too long - speed it up to fit the time slot
                                speed_factor = (actual_duration / expected_duration) + 0.05  # Add 0.05 buffer
                                print(f"  Audio is {actual_duration:.2f}s, expected {expected_duration:.2f}s")
                                print(f"  Speeding up audio by factor of {speed_factor:.3f}")
                                
                                # Apply speed change and save back to original file
                                sped_up_audio = audio_clip.with_effects([vfx.MultiplySpeed(speed_factor)])
                                
                                # Save the sped-up audio back to the original file  
                                temp_audio_path = audio_file.replace('.wav', '_temp.wav')
                                sped_up_audio.write_audiofile(temp_audio_path, verbose=False, logger=None)
                                
                                # Replace original file with sped-up version
                                import shutil
                                shutil.move(temp_audio_path, audio_file)
                                
                                # Reload the audio clip with the new sped-up version
                                audio_clip.close()
                                audio_clip = AudioFileClip(audio_file)
                                sped_up_audio.close()
                                
                                print(f"  Saved sped-up audio to {audio_file}, new duration: {audio_clip.duration:.2f}s")
                            else:
                                # Audio is too short - pad with silence
                                silence_duration = expected_duration - actual_duration
                                print(f"  Audio is {silence_duration:.2f}s too short, will be padded during composition")
                                # Note: We'll handle short audio by letting MoviePy handle it naturally
                        
                        # Set the start time for this audio clip using MoviePy 2.x API
                        audio_clip = audio_clip.with_start(start_sec)
                        synchronized_audio_clips.append(audio_clip)
                    
                    # Handle gaps between dialogues by adding silence
                    final_audio_clips = []
                    
                    for i, audio_clip in enumerate(synchronized_audio_clips):
                        final_audio_clips.append(audio_clip)
                        
                        # Check if there's a gap before the next dialogue
                        if i < len(synchronized_audio_clips) - 1:
                            current_end = self.convert_time_to_seconds(dialogues[i]['end'])
                            next_start = self.convert_time_to_seconds(dialogues[i+1]['start'])
                            gap_duration = next_start - current_end
                            
                            if gap_duration > 0.1:  # If gap > 0.1 seconds
                                print(f"  Gap of {gap_duration:.2f}s detected between dialogues {i+1} and {i+2}")
                                # Note: Gaps will be handled naturally by CompositeAudioClip positioning
                    
                    # Combine all audio clips
                    combined_audio = CompositeAudioClip(final_audio_clips)
                    
                    # Create final composite with synchronized audio
                    final_clip = CompositeVideoClip(all_clips, size=(W, H)).with_audio(combined_audio)
                    print("Successfully synchronized audio with dialogue timing")
                    
                except Exception as e:
                    print(f"Error synchronizing audio: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback to video without audio
                    final_clip = CompositeVideoClip(all_clips, size=(W, H))
            else:
                if audio_files:
                    print(f"Audio file count mismatch: {len(audio_files)} files for {len(dialogues)} dialogues")
                else:
                    print("No audio files found, creating video without audio")
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
            
            if audio_files and 'synchronized_audio_clips' in locals():
                for clip in synchronized_audio_clips:
                    try:
                        clip.close()
                    except:
                        pass
            
            # Clean up temporary text images
            for temp_file in self.base_dir.glob("temp_text_*.png"):
                try:
                    temp_file.unlink()
                except:
                    pass
            
            print(f"Video generated successfully: {self.output_path}")
            return True
            
        except Exception as e:
            print(f"Error generating video: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_simple_video(self, duration: float = 15.0) -> bool:
        """
        Generate a simple video without dialogues (fallback)
        
        Args:
            duration: Video duration in seconds
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            background_image_path = self.get_background_image()
            if not background_image_path:
                print("No background image found for simple video")
                return False
            
            # Create simple background clip
            background_clip = ImageClip(background_image_path).with_duration(duration)
            
            # Add audio if available
            audio_files = self.get_audio_files()
            if audio_files:
                try:
                    audio_clips = [AudioFileClip(f) for f in audio_files]
                    combined_audio = CompositeAudioClip(audio_clips)
                    final_clip = background_clip.with_audio(combined_audio)
                except Exception as e:
                    print(f"Error adding audio to simple video: {e}")
                    final_clip = background_clip
            else:
                final_clip = background_clip
            
            # Render video
            print(f"Rendering simple video to {self.output_path}...")
            final_clip.write_videofile(
                str(self.output_path),
                fps=24,
                codec='libx264',
                audio_codec='aac' if audio_files else None
            )
            
            # Cleanup
            final_clip.close()
            background_clip.close()
            
            print(f"Simple video generated successfully: {self.output_path}")
            return True
            
        except Exception as e:
            print(f"Error generating simple video: {e}")
            return False


# Convenience functions for integration with main.py
def generate_video_from_scene_data(base_dir: str, scene_data: Dict, 
                                 character_positions: Optional[Dict] = None) -> bool:
    """
    Generate video from scene data (for use in main.py)
    
    Args:
        base_dir: Base directory containing images and audio
        scene_data: Scene data from Gemini
        character_positions: Character positioning config
    
    Returns:
        bool: True if successful, False otherwise
    """
    generator = VoiceFrameVideoGenerator(base_dir)
    
    # Try to generate with dialogues first
    if generator.generate_video_with_dialogues(scene_data, character_positions):
        return True
    
    # Fallback to simple video
    print("Falling back to simple video generation...")
    return generator.generate_simple_video()


def generate_simple_video_from_images(base_dir: str, duration: float = 15.0) -> bool:
    """
    Generate simple video from images (fallback function)
    
    Args:
        base_dir: Base directory containing images
        duration: Video duration
    
    Returns:
        bool: True if successful, False otherwise
    """
    generator = VoiceFrameVideoGenerator(base_dir)
    return generator.generate_simple_video(duration)