import json
import os
os.environ['IMAGEMAGICK_BINARY'] = r'D:\ImageMagick-7.1.2-Q16-HDRI\magick.exe'

from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, ColorClip
from moviepy.video.fx.all import fadein, fadeout


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
    font_color='gold'
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
    
    for i, dialogue in enumerate(scene_data['scene']['dialogues']):
        start_sec = convert_time_to_seconds(dialogue['start'])
        end_sec = convert_time_to_seconds(dialogue['end'])
        line_duration = end_sec - start_sec
        
        print(f"Dialogue {i+1}: {dialogue['character']} from {start_sec:.2f}s to {end_sec:.2f}s")
        
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
            print(f"Created dynamic dialogue box for {char_name}")

        except Exception as e:
            print(f"Error creating dialogue for {char_name}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Create final composite video
    print(f"Creating composite with {len(all_clips)} total clips")
    final_clip = CompositeVideoClip(all_clips, size=(W, H))

    # Render video
    print(f"Rendering video (duration={video_duration:.2f}s, resolution={W}x{H}) ...")
    final_clip.write_videofile(
        output_file,
        fps=24,
        codec='libx264',
        audio=False,
        verbose=False,
        logger=None
    )
    print(f"Video saved successfully: {output_file}")

    # Clean up
    final_clip.close()
    for clip in all_clips:
        try:
            clip.close()
        except:
            pass


if __name__ == '__main__':
    BACKGROUND_IMAGE_FILE = 'background_image.jpg'
    OVERLAY_FRAME_IMAGE = 'ornate_frame.png'  # Not used anymore
    SCENE_DATA_JSON_FILE = 'scene_data.json'
    OUTPUT_VIDEO_FILE = 'scorpion_frog_story.mp4'

    # Character positioning config - now much simpler, just specify side and max width
    CHARACTER_POSITIONS = {
        "Scorpion": {
            "side": "left",      # left or right
            "max_width": 500     # maximum width for text box
        },
        "Frog": {
            "side": "right",
            "max_width": 500
        }
    }

    # Check if required files exist
    required_files = [BACKGROUND_IMAGE_FILE, SCENE_DATA_JSON_FILE]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print("ERROR: Missing required files:")
        for f in missing_files:
            print(f"  - {f}")
        print("\nPlease ensure all files are in the same directory as this script.")
    else:
        print("All required files found. Starting video generation...")
        
        try:
            process_scene_with_dialogues_and_frame(
                background_image_path=BACKGROUND_IMAGE_FILE,
                overlay_frame_path=OVERLAY_FRAME_IMAGE,
                scene_data_json_path=SCENE_DATA_JSON_FILE,
                output_file=OUTPUT_VIDEO_FILE,
                character_positions=CHARACTER_POSITIONS,
                font_size=16,  # Slightly smaller for better fitting
                font_color='gold'
            )
        except Exception as e:
            print(f"ERROR during video generation: {e}")
            import traceback
            traceback.print_exc()