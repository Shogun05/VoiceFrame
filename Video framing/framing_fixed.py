"""
Video Generator Module
Converts scene data and background images into videos with text overlays and optional audio
"""

import json
import os
from moviepy.editor import (ImageClip, TextClip, CompositeVideoClip, ColorClip, 
                          AudioFileClip, CompositeAudioClip)
from moviepy.video.fx.all import fadein, fadeout

# Set ImageMagick binary path if needed
if 'IMAGEMAGICK_BINARY' not in os.environ:
    # You can set this path or leave it to auto-detect
    imagemagick_paths = [
        r'D:\ImageMagick-7.1.2-Q16-HDRI\magick.exe',
        r'C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe',
        r'C:\ImageMagick\magick.exe'
    ]
    
    for path in imagemagick_paths:
        if os.path.exists(path):
            os.environ['IMAGEMAGICK_BINARY'] = path
            break


def convert_time_to_seconds(time_str):
    """Convert time string to seconds"""
    if not isinstance(time_str, str):
        raise ValueError("Time must be a string like '00:01:23' or '1:23.45'")
    
    parts = [p.strip() for p in time_str.strip().split(':')]
    if len(parts) == 3:
        h = int(parts[0])
        m = int(parts[1])
        s = float(parts[2])
        return h * 3600 + m * 60 + s
    elif len(parts) == 2:
        m = int(parts[0])
        s = float(parts[1])
        return m * 60 + s
    elif len(parts) == 1:
        return float(parts[0])
    else:
        raise ValueError(f"Time string format '{time_str}' is invalid.")


def estimate_text_dimensions(text, fontsize, max_width):
    """Estimate the dimensions needed for text based on character count and word wrapping"""
    # Average character width (approximate)
    char_width = fontsize * 0.6
    line_height = fontsize * 1.4
    
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
    estimated_height = len(lines) * line_height + 20
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


def get_audio_file_path(sequence_num, character_name, start_time, end_time, audio_dir="output_audio"):
    """Generate audio file path based on naming convention"""
    start_formatted = start_time.replace(":", "-")
    end_formatted = end_time.replace(":", "-")
    filename = f"{sequence_num:03d}_{character_name}_{start_formatted}_{end_formatted}.wav"
    return os.path.join(audio_dir, filename)


def find_audio_file_flexible(sequence_num, character_name, start_time, end_time, audio_dir="output_audio", verbose=False):
    """Try to find audio file with flexible naming conventions"""
    if verbose:
        print(f"Searching for audio file for dialogue {sequence_num}")
    
    patterns_to_try = [
        f"{sequence_num:03d}_{character_name}_{start_time.replace(':', '-')}_{end_time.replace(':', '-')}.wav",
        f"{sequence_num+1:03d}_{character_name}_{start_time.replace(':', '-')}_{end_time.replace(':', '-')}.wav",
        f"{sequence_num}_{character_name}_{start_time.replace(':', '-')}_{end_time.replace(':', '-')}.wav",
        f"{sequence_num+1}_{character_name}_{start_time.replace(':', '-')}_{end_time.replace(':', '-')}.wav",
    ]
    
    for pattern in patterns_to_try:
        full_path = os.path.join(audio_dir, pattern)
        if verbose:
            print(f"  Trying: {full_path}")
        
        if os.path.exists(full_path):
            if verbose:
                print(f"  Found: {full_path}")
            return full_path
        elif verbose:
            print(f"  Not found: {full_path}")
    
    if verbose and os.path.exists(audio_dir):
        print(f"  Files in {audio_dir}:")
        for file in os.listdir(audio_dir):
            if file.endswith('.wav'):
                print(f"    - {file}")
    
    return None


def create_video_with_audio(
    background_image_path,
    scene_data_json_path,
    output_file,
    character_positions=None,
    font_size=20,
    font_color='gold',
    audio_dir=None,
    verbose=False
):
    """
    Create a video from background image and scene data with optional audio
    
    Parameters:
    - background_image_path: Path to background image
    - scene_data_json_path: Path to scene data JSON file
    - output_file: Path for output video file
    - character_positions: Dict with character positioning config
    - font_size: Text font size
    - font_color: Text color
    - audio_dir: Directory containing audio files (None to disable audio)
    - verbose: Enable detailed logging
    
    Returns:
    - True if successful, False otherwise
    """
    
    try:
        # Check if files exist
        required_files = [background_image_path, scene_data_json_path]
        for file_path in required_files:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Required file not found: {file_path}")

        # Load scene data
        with open(scene_data_json_path, 'r', encoding='utf-8') as f:
            scene_data = json.load(f)

        scene_end_time = scene_data['scene']['background']['end']
        video_duration = float(convert_time_to_seconds(scene_end_time))
        
        if verbose:
            print(f"Video duration: {video_duration} seconds")

        # Create background clip
        background_clip = ImageClip(background_image_path).set_duration(video_duration)
        W, H = background_clip.size
        
        if verbose:
            print(f"Background size: {W}x{H}")

        # Default character positions if none provided
        if character_positions is None:
            character_positions = {
                "Scorpion": {"side": "left", "max_width": 450},
                "Frog": {"side": "right", "max_width": 450}
            }

        # Create clips for each dialogue
        all_clips = [background_clip]
        audio_clips = []
        
        # Check if audio processing is enabled
        use_audio = audio_dir is not None and os.path.exists(audio_dir)
        
        if verbose:
            if use_audio:
                print(f"Audio processing enabled. Audio directory: {audio_dir}")
            else:
                print("Audio processing disabled.")

        for i, dialogue in enumerate(scene_data['scene']['dialogues']):
            start_sec = convert_time_to_seconds(dialogue['start'])
            end_sec = convert_time_to_seconds(dialogue['end'])
            line_duration = end_sec - start_sec
            
            if verbose:
                print(f"Dialogue {i+1}: {dialogue['character']} from {start_sec:.2f}s to {end_sec:.2f}s")
            
            if line_duration <= 0:
                if verbose:
                    print(f"Warning: Dialogue {i+1} has invalid duration, skipping")
                continue

            # Set fade duration
            FADE_DURATION = min(0.2, line_duration / 6.0)
            
            # Get character info
            char_name = dialogue.get('character', 'Unknown')
            line_text = dialogue.get('line', '')
            text_content = f"{char_name}: {line_text}"
            
            # Audio processing
            if use_audio:
                try:
                    audio_file_path = find_audio_file_flexible(
                        sequence_num=i,
                        character_name=dialogue['character'],
                        start_time=dialogue['start'],
                        end_time=dialogue['end'],
                        audio_dir=audio_dir,
                        verbose=verbose
                    )
                    
                    if audio_file_path and os.path.exists(audio_file_path):
                        if verbose:
                            print(f"Loading audio file: {audio_file_path}")
                        
                        audio_clip = AudioFileClip(audio_file_path)
                        audio_clip = audio_clip.set_start(start_sec)
                        
                        # Handle duration mismatches
                        if audio_clip.duration > line_duration:
                            audio_clip = audio_clip.subclip(0, line_duration)
                        
                        audio_clips.append(audio_clip)
                        
                        if verbose:
                            print(f"Successfully added audio for {dialogue['character']}")
                    elif verbose:
                        print(f"No audio file found for {dialogue['character']}")
                        
                except Exception as e:
                    if verbose:
                        print(f"Error processing audio for {dialogue['character']}: {e}")

            # Get character positioning
            if char_name in character_positions:
                char_config = character_positions[char_name]
                side = char_config.get("side", "left")
                max_width = char_config.get("max_width", 400)
            else:
                if verbose:
                    print(f"WARNING: No position config for '{char_name}', using default.")
                side = "left"
                max_width = 400

            try:
                # Estimate text dimensions
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
                
                if verbose:
                    print(f"  Text dimensions: {text_width}x{text_height} ({num_lines} lines)")
                    print(f"  Position: ({text_x}, {text_y})")

                # Create custom border background
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

                # Create text clip
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
                
                if verbose:
                    print(f"Created dialogue box for {char_name}")

            except Exception as e:
                if verbose:
                    print(f"Error creating dialogue for {char_name}: {e}")
                continue

        # Create final composite video
        if verbose:
            print(f"Creating composite with {len(all_clips)} total clips")
        
        final_clip = CompositeVideoClip(all_clips, size=(W, H))

        # Add audio if available
        has_audio = len(audio_clips) > 0
        if has_audio:
            if verbose:
                print(f"Compositing {len(audio_clips)} audio clips")
            
            final_audio = CompositeAudioClip(audio_clips)
            final_clip = final_clip.set_audio(final_audio)
            
            if verbose:
                print("Audio added to video")

        # Render video
        if verbose:
            print(f"Rendering video {'with' if has_audio else 'without'} audio...")
        
        final_clip.write_videofile(
            output_file,
            fps=24,
            codec='libx264',
            audio_codec='aac' if has_audio else None,
            audio=has_audio,
            verbose=verbose,
            logger='bar' if verbose else None
        )
        
        if verbose:
            print(f"Video saved successfully: {output_file}")

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

        return True

    except Exception as e:
        print(f"Error during video generation: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


# Convenience function that matches the original interface
def process_scene_with_dialogues_and_frame(
    background_image_path,
    overlay_frame_path,  # Not used but kept for compatibility
    scene_data_json_path,
    output_file,
    character_positions=None,
    font_size=20,
    font_color='gold',
    audio_dir=None
):
    """Legacy function for backward compatibility"""
    return create_video_with_audio(
        background_image_path=background_image_path,
        scene_data_json_path=scene_data_json_path,
        output_file=output_file,
        character_positions=character_positions,
        font_size=font_size,
        font_color=font_color,
        audio_dir=audio_dir,
        verbose=True
    )