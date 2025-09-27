import json
import os
os.environ['IMAGEMAGICK_BINARY'] = r'D:\ImageMagick-7.1.2-Q16-HDRI\magick.exe'

from moviepy.editor import (ImageClip, TextClip, CompositeVideoClip, 
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

def estimate_text_dimensions(text, fontsize, max_width):
    """
    Estimate the dimensions needed for text based on character count and word wrapping
    """
    # Average character width (approximate)
    char_width = fontsize * 0.6  # This varies by font, but 0.6 is a reasonable estimate for Arial
    line_height = fontsize * 1.4  # Line height is typically 1.2-1.4 times font size
    
    # Calculate how many characters fit per line
    chars_per_line = int(max_width / char_width)
    
    # Split text into words and estimate line breaks
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + " " + word if current_line else word
        if len(test_line) <= chars_per_line:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    # Calculate final dimensions
    estimated_height = len(lines) * line_height + 20  # Add some padding
    estimated_width = min(max_width, max(len(line) * char_width for line in lines) + 20)
    
    return int(estimated_width), int(estimated_height), len(lines)

def create_custom_border(size, border_width=3, border_color=(218, 165, 32), bg_color=(0, 0, 0)):
    """Create a custom border using ColorClips"""
    width, height = size
    
    # Create background rectangle (semi-transparent black)
    background = ColorClip(size=(width, height), color=bg_color).set_opacity(0.8)
    
    # Create border rectangles
    top_border = ColorClip(size=(width, border_width), color=border_color)
    bottom_border = ColorClip(size=(width, border_width), color=border_color).set_position((0, height - border_width))
    left_border = ColorClip(size=(border_width, height), color=border_color)
    right_border = ColorClip(size=(border_width, height), color=border_color).set_position((width - border_width, 0))
    
    # Composite all border elements
    bordered_clip = CompositeVideoClip([background, top_border, bottom_border, left_border, right_border], size=(width, height))
    return bordered_clip

def process_scene_with_dialogues_and_frame(
    background_image_path,
    overlay_frame_path,  # Not used anymore
    scene_data_json_path,
    output_file,
    character_positions=None,
    font_size=20,
    font_color='gold',
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
            "Scorpion": {"side": "left", "max_width": 450},
            "Frog": {"side": "right", "max_width": 450}
        }

    # Create clips for each dialogue with dynamic sizing
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
        
        # Format text content
        text_content = f"{char_name}: {line_text}"
        
        # AUDIO PROCESSING - Enhanced with flexible search
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
                
                # Load and time the audio clip
                audio_clip = AudioFileClip(audio_file_path)
                print(f"  Original audio duration: {audio_clip.duration:.2f}s")
                print(f"  Expected dialogue duration: {line_duration:.2f}s")
                
                # Set the start time to match the dialogue timing
                audio_clip = audio_clip.set_start(start_sec)
                
                # Handle duration mismatches
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
            import traceback
            traceback.print_exc()

        # Get character positioning preferences
        if char_name in character_positions:
            char_config = character_positions[char_name]
            side = char_config.get("side", "left")
            max_width = char_config.get("max_width", 400)
        else:
            print(f"WARNING: No position config for '{char_name}', using default.")
            side = "left"
            max_width = 400

        try:
            # Estimate text dimensions dynamically
            text_width, text_height, num_lines = estimate_text_dimensions(text_content, font_size, max_width)
            
            # Add padding to the border
            border_padding = 20
            border_width = text_width + border_padding
            border_height = text_height + border_padding
            
            # Calculate positions based on side
            margin = 40
            bottom_margin = 60
            
            if side == "left":
                text_x = margin + border_padding // 2
                border_x = margin
            else:  # right side
                text_x = W - margin - text_width - border_padding // 2
                border_x = W - margin - border_width
            
            # Position from bottom
            text_y = H - bottom_margin - text_height
            border_y = H - bottom_margin - border_height
            
            print(f"  Text dimensions: {text_width}x{text_height} ({num_lines} lines)")
            print(f"  Border dimensions: {border_width}x{border_height}")
            print(f"  Text position: ({text_x}, {text_y})")
            print(f"  Border position: ({border_x}, {border_y})")

            # Create custom border background for this dialogue
            dialogue_border = create_custom_border((border_width, border_height))
            dialogue_border = (dialogue_border
                             .set_start(start_sec)
                             .set_duration(line_duration)
                             .set_position((border_x, border_y)))
            
            # Apply fade to border
            if FADE_DURATION > 0:
                dialogue_border = fadein(dialogue_border, FADE_DURATION)
                dialogue_border = fadeout(dialogue_border, FADE_DURATION)
            
            all_clips.append(dialogue_border)

            # Create text clip with dynamic sizing
            text_clip = (
                TextClip(
                    txt=text_content,
                    fontsize=font_size,
                    color=font_color,
                    font='Arial-Bold',
                    method='caption',
                    size=(text_width, text_height),
                    align='center',
                    interline=3
                )
                .set_start(start_sec)
                .set_duration(line_duration)
                .set_position((text_x, text_y))
            )

            all_clips.append(text_clip)
            print(f"✓ Created dynamic dialogue box for {char_name}")

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
            
            # Additional audio debugging
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
            "max_width": 500
        },
        "Frog": {
            "side": "right",
            "max_width": 500
        }
    }

    print("=== AUDIO-ENABLED VIDEO GENERATOR ===")
    
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
                font_size=16,
                font_color='gold',
                audio_dir=AUDIO_DIRECTORY 
            )
        except Exception as e:
            print(f"\n✗ ERROR during video generation: {e}")
            import traceback
            traceback.print_exc()