import json
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io

from moviepy.editor import (ImageClip, CompositeVideoClip, 
                          ColorClip, AudioFileClip, CompositeAudioClip)
from moviepy.video.fx.all import fadein, fadeout

def get_audio_file_path(sequence_num, character_name, start_time, end_time, audio_dir="output_audio"):
    """
    Generate audio file path based on the naming convention:
    {sequence_number}_{character_name}_{start_time}_{end_time}.wav
    """
    # Convert time format from "00:00:05" to "00-00-05"
    start_formatted = start_time.replace(":", "-")
    end_formatted = end_time.replace(":", "-")
    
    filename = f"{sequence_num:03d}_{character_name}_{start_formatted}_{end_formatted}.wav"
    return os.path.join(audio_dir, filename)

def find_audio_file_flexible(sequence_num, character_name, start_time, end_time, audio_dir="output_audio"):
    """
    Try to find audio file with flexible naming conventions
    """
    print(f"\n--- Searching for audio file for dialogue {sequence_num} ---")
    
    # Try multiple naming patterns
    patterns_to_try = [
        # Original pattern (0-based)
        f"{sequence_num:03d}_{character_name}_{start_time.replace(':', '-')}_{end_time.replace(':', '-')}.wav",
        # 1-based indexing
        f"{sequence_num+1:03d}_{character_name}_{start_time.replace(':', '-')}_{end_time.replace(':', '-')}.wav",
        # Without leading zeros
        f"{sequence_num}_{character_name}_{start_time.replace(':', '-')}_{end_time.replace(':', '-')}.wav",
        f"{sequence_num+1}_{character_name}_{start_time.replace(':', '-')}_{end_time.replace(':', '-')}.wav",
    ]
    
    for pattern in patterns_to_try:
        full_path = os.path.join(audio_dir, pattern)
        print(f"  Trying: {full_path}")
        if os.path.exists(full_path):
            print(f"  ✓ Found: {full_path}")
            return full_path
        else:
            print(f"  ✗ Not found: {full_path}")
    
    # List all files in the audio directory for debugging
    if os.path.exists(audio_dir):
        print(f"\n  Files in {audio_dir}:")
        for file in os.listdir(audio_dir):
            if file.endswith('.wav'):
                print(f"    - {file}")
    else:
        print(f"  Audio directory {audio_dir} does not exist!")
    
    return None

def convert_time_to_seconds(time_str):
    if not isinstance(time_str, str):
        raise ValueError("Time must be a string like '00:01:23' or '1:23.45'")
    parts = [p.strip() for p in time_str.strip().split(':')]
    if len(parts) == 3:
        h = int(parts[0]); m = int(parts[1]); s = float(parts[2])
        return h * 3600 + m * 60 + s
    elif len(parts) == 2:
        m = int(parts[0]); s = float(parts[1])
        return m * 60 + s
    elif len(parts) == 1:
        return float(parts[0])
    else:
        raise ValueError(f"Time string format '{time_str}' is invalid.")

def wrap_text_simple(text, max_chars_per_line=50):
    """
    Simple text wrapping without external dependencies
    """
    words = text.split(' ')
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + " " + word if current_line else word
        if len(test_line) <= max_chars_per_line:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines

def create_text_image_pil(text, font_size=20, font_color=(255, 255, 255), 
                         bg_color=(0, 0, 0), bg_opacity=0.8, 
                         padding=20, border_color=(218, 165, 32), border_width=3,
                         max_chars=50):
    """
    Create text image using PIL instead of MoviePy TextClip
    """
    try:
        # Try to load a font, fallback to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("Arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.load_default()
                    font_size = 11  # Default font size
                except:
                    # If all else fails, create without font
                    font = None
        
        # Wrap text
        lines = wrap_text_simple(text, max_chars)
        
        # Calculate text dimensions
        if font:
            # Get text dimensions using font
            temp_img = Image.new('RGB', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            
            line_heights = []
            line_widths = []
            
            for line in lines:
                bbox = temp_draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                line_height = bbox[3] - bbox[1]
                line_widths.append(line_width)
                line_heights.append(line_height)
            
            text_width = max(line_widths) if line_widths else 0
            text_height = sum(line_heights) + (len(lines) - 1) * 5  # 5px line spacing
        else:
            # Fallback calculation without font
            text_width = max(len(line) for line in lines) * 8  # Rough estimate
            text_height = len(lines) * 15  # Rough estimate
        
        # Add padding
        img_width = text_width + padding * 2
        img_height = text_height + padding * 2
        
        # Create image with transparent background
        img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw background with opacity
        bg_alpha = int(255 * bg_opacity)
        bg_with_alpha = (*bg_color, bg_alpha)
        draw.rectangle([0, 0, img_width-1, img_height-1], fill=bg_with_alpha)
        
        # Draw border
        for i in range(border_width):
            draw.rectangle([i, i, img_width-1-i, img_height-1-i], 
                         outline=border_color, width=1)
        
        # Draw text
        y_offset = padding
        for line in lines:
            if font:
                draw.text((padding, y_offset), line, fill=font_color, font=font)
                bbox = draw.textbbox((0, 0), line, font=font)
                line_height = bbox[3] - bbox[1]
                y_offset += line_height + 5
            else:
                draw.text((padding, y_offset), line, fill=font_color)
                y_offset += 15  # Estimated line height
        
        # Convert PIL image to numpy array for MoviePy
        img_array = np.array(img)
        
        return img_array
        
    except Exception as e:
        print(f"Error creating text image: {e}")
        # Return a simple colored rectangle as fallback
        img = Image.new('RGBA', (300, 100), (*bg_color, int(255 * bg_opacity)))
        return np.array(img)

def create_dialogue_clip_from_image(text, font_size=20, font_color=(255, 255, 255),
                                  bg_color=(0, 0, 0), bg_opacity=0.8,
                                  padding=20, border_color=(218, 165, 32), 
                                  border_width=3, max_chars=50):
    """
    Create a MoviePy clip from PIL-generated text image
    """
    img_array = create_text_image_pil(
        text=text,
        font_size=font_size,
        font_color=font_color,
        bg_color=bg_color,
        bg_opacity=bg_opacity,
        padding=padding,
        border_color=border_color,
        border_width=border_width,
        max_chars=max_chars
    )
    
    # Create ImageClip from numpy array
    clip = ImageClip(img_array, transparent=True, duration=1)
    return clip

def process_scene_with_dialogues_and_frame(
    background_image_path,
    overlay_frame_path,  # Not used anymore
    scene_data_json_path,
    output_file,
    character_positions=None,
    font_size=20,
    font_color=(255, 255, 255),
    audio_dir="output_audio"
):
    # Check if files exist
    for p in (background_image_path, scene_data_json_path):
        if not os.path.exists(p):
            raise FileNotFoundError(f"Required file not found: {p}")

    # Load scene data
    with open(scene_data_json_path, 'r', encoding='utf-8') as f:
        scene_data = json.load(f)

    scene_end_time = scene_data['scene']['background']['end']
    video_duration = float(convert_time_to_seconds(scene_end_time))
    print(f"Video duration: {video_duration} seconds")

    # Create background clip
    background_clip = ImageClip(background_image_path).set_duration(video_duration)
    W, H = background_clip.size
    print(f"Background size: {W}x{H}")

    # Default character positions if none provided
    if character_positions is None:
        character_positions = {
            "Scorpion": {"side": "left", "max_chars": 45},
            "Frog": {"side": "right", "max_chars": 45}
        }

    # Create clips for each dialogue
    all_clips = [background_clip]  # Start with background
    audio_clips = []

    print(f"\n=== PROCESSING {len(scene_data['scene']['dialogues'])} DIALOGUES ===")

    for i, dialogue in enumerate(scene_data['scene']['dialogues']):
        start_sec = convert_time_to_seconds(dialogue['start'])
        end_sec = convert_time_to_seconds(dialogue['end'])
        line_duration = end_sec - start_sec
        
        print(f"\n--- Dialogue {i+1}: {dialogue['character']} from {start_sec:.2f}s to {end_sec:.2f}s ---")
        
        if line_duration <= 0:
            print(f"Warning: Dialogue {i+1} has invalid duration, skipping")
            continue

        # Set fade duration
        FADE_DURATION = min(0.2, line_duration / 6.0)
        
        # Get character info
        char_name = dialogue.get('character', 'Unknown')
        line_text = dialogue.get('line', '')
        
        # AUDIO PROCESSING
        try:
            audio_file_path = find_audio_file_flexible(
                sequence_num=i,
                character_name=dialogue['character'],
                start_time=dialogue['start'],
                end_time=dialogue['end'],
                audio_dir=audio_dir
            )
            
            if audio_file_path and os.path.exists(audio_file_path):
                print(f"✓ Loading audio file: {audio_file_path}")
                
                audio_clip = AudioFileClip(audio_file_path)
                print(f"  Original audio duration: {audio_clip.duration:.2f}s")
                print(f"  Expected dialogue duration: {line_duration:.2f}s")
                
                audio_clip = audio_clip.set_start(start_sec)
                
                if audio_clip.duration > line_duration:
                    print(f"  Trimming audio from {audio_clip.duration:.2f}s to {line_duration:.2f}s")
                    audio_clip = audio_clip.subclip(0, line_duration)
                elif audio_clip.duration < line_duration:
                    print(f"  Warning: Audio ({audio_clip.duration:.2f}s) is shorter than dialogue duration ({line_duration:.2f}s)")
                
                audio_clips.append(audio_clip)
                print(f"✓ Successfully added audio for {dialogue['character']}")
            else:
                print(f"✗ No audio file found for {dialogue['character']}")
                
        except Exception as e:
            print(f"✗ Error processing audio for {dialogue['character']}: {e}")

        # Get character positioning preferences
        if char_name in character_positions:
            char_config = character_positions[char_name]
            side = char_config.get("side", "left")
            max_chars = char_config.get("max_chars", 45)
        else:
            print(f"WARNING: No position config for '{char_name}', using default.")
            side = "left"
            max_chars = 45

        try:
            # Format text
            text_content = f"{char_name}: {line_text}"
            print(f"  Creating text box for: {text_content[:50]}...")

            # Create dialogue clip using PIL
            dialogue_clip = create_dialogue_clip_from_image(
                text=text_content,
                font_size=font_size,
                font_color=font_color,
                bg_color=(0, 0, 0),
                bg_opacity=0.8,
                padding=15,
                border_color=(218, 165, 32),
                border_width=3,
                max_chars=max_chars
            )
            
            # Calculate position based on side
            margin = 30
            bottom_margin = 60
            
            clip_w, clip_h = dialogue_clip.size
            
            if side == "left":
                x_pos = margin
            else:  # right side
                x_pos = W - margin - clip_w
            
            y_pos = H - bottom_margin - clip_h
            
            print(f"  Clip dimensions: {clip_w}x{clip_h}")
            print(f"  Position: ({x_pos}, {y_pos})")

            # Set timing and position
            dialogue_clip = (dialogue_clip
                           .set_start(start_sec)
                           .set_duration(line_duration)
                           .set_position((x_pos, y_pos)))
            
            # Apply fade effects
            if FADE_DURATION > 0:
                dialogue_clip = fadein(dialogue_clip, FADE_DURATION)
                dialogue_clip = fadeout(dialogue_clip, FADE_DURATION)

            all_clips.append(dialogue_clip)
            print(f"✓ Successfully created dialogue box for {char_name}")

        except Exception as e:
            print(f"✗ Error creating dialogue for {char_name}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Audio debugging information
    print(f"\n=== AUDIO PROCESSING SUMMARY ===")
    print(f"Total dialogues processed: {len(scene_data['scene']['dialogues'])}")
    print(f"Audio clips found and loaded: {len(audio_clips)}")
    
    if audio_clips:
        print("Audio clip details:")
        for i, clip in enumerate(audio_clips):
            print(f"  Clip {i+1}: start={clip.start:.2f}s, duration={clip.duration:.2f}s")

    # Create final composite video
    print(f"\n=== VIDEO COMPOSITION ===")
    print(f"Creating composite with {len(all_clips)} total clips")
    final_clip = CompositeVideoClip(all_clips, size=(W, H))

    # Add audio if we have audio clips
    if audio_clips:
        print(f"✓ Compositing {len(audio_clips)} audio clips")
        try:
            final_audio = CompositeAudioClip(audio_clips)
            final_clip = final_clip.set_audio(final_audio)
            print("✓ Audio successfully added to video")
            
            print(f"Final audio duration: {final_audio.duration:.2f}s")
            print(f"Video duration: {video_duration:.2f}s")
            
        except Exception as e:
            print(f"✗ Error compositing audio: {e}")
            import traceback
            traceback.print_exc()
            print("Proceeding without audio...")
    else:
        print("⚠ No audio files found - creating video without audio")

    # Render video
    print(f"\n=== RENDERING VIDEO ===")
    has_audio = len(audio_clips) > 0
    print(f"Rendering video {'with' if has_audio else 'without'} audio (duration={video_duration:.2f}s, resolution={W}x{H}) ...")
    
    try:
        final_clip.write_videofile(
            output_file,
            fps=24,
            codec='libx264',
            audio_codec='aac' if has_audio else None,
            audio=has_audio,
            verbose=False,
            logger=None
        )
        print(f"✓ Video saved successfully: {output_file}")
    except Exception as e:
        print(f"✗ Error during video rendering: {e}")
        import traceback
        traceback.print_exc()
        raise

    # Clean up
    final_clip.close()
    for clip in all_clips:
        try:
            clip.close()
        except:
            pass
    
    for clip in audio_clips:
        try:
            clip.close()
        except:
            pass

if __name__ == '__main__':
    BACKGROUND_IMAGE_FILE = 'background_image.jpg'
    OVERLAY_FRAME_IMAGE = 'ornate_frame.png'  # Not used anymore
    SCENE_DATA_JSON_FILE = 'scene_data.json'
    OUTPUT_VIDEO_FILE = 'scorpion_frog_story.mp4'
    AUDIO_DIRECTORY = 'output_audio'
    
    # Character positioning config
    CHARACTER_POSITIONS = {
        "Scorpion": {
            "side": "left",
            "max_chars": 45  # Maximum characters per line
        },
        "Frog": {
            "side": "right", 
            "max_chars": 45
        }
    }

    print("=== PIL-BASED TEXT RENDERER - NO IMAGEMAGICK REQUIRED ===")
    print("✓ Uses Python PIL library for text rendering!")
    
    # Check if required files exist
    required_files = [BACKGROUND_IMAGE_FILE, SCENE_DATA_JSON_FILE]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    # Check if audio directory exists
    if not os.path.exists(AUDIO_DIRECTORY):
        print(f"⚠ Warning: Audio directory '{AUDIO_DIRECTORY}' not found")
        print("Video will be created without audio")
        print(f"Please create the directory and add audio files in format:")
        print(f"  000_CharacterName_00-00-05_00-00-15.wav")
    else:
        print(f"✓ Audio directory found: {AUDIO_DIRECTORY}")
        # List audio files for verification
        audio_files = [f for f in os.listdir(AUDIO_DIRECTORY) if f.endswith('.wav')]
        print(f"Found {len(audio_files)} audio files:")
        for audio_file in audio_files:
            print(f"  - {audio_file}")

    if missing_files:
        print("\n✗ ERROR: Missing required files:")
        for f in missing_files:
            print(f"  - {f}")
        print("\nPlease ensure all files are in the same directory as this script.")
    else:
        print(f"\n✓ All required files found. Starting video generation...")
        
        try:
            process_scene_with_dialogues_and_frame(
                background_image_path=BACKGROUND_IMAGE_FILE,
                overlay_frame_path=OVERLAY_FRAME_IMAGE,
                scene_data_json_path=SCENE_DATA_JSON_FILE,
                output_file=OUTPUT_VIDEO_FILE,
                character_positions=CHARACTER_POSITIONS,
                font_size=18,
                font_color=(255, 255, 255),  # White text
                audio_dir=AUDIO_DIRECTORY 
            )
        except Exception as e:
            print(f"\n✗ ERROR during video generation: {e}")
            import traceback
            traceback.print_exc()