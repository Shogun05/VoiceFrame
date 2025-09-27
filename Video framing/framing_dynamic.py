"""
Enhanced Video Generator Module with Dynamic Audio-Based Rendering
Renders dialogue textboxes and audio based on actual audio file duration
"""

import os
import json
from moviepy.editor import (ImageClip, TextClip, CompositeVideoClip, ColorClip, 
                          AudioFileClip, CompositeAudioClip)
from moviepy.video.fx.all import fadein, fadeout


class DynamicVideoGenerator:
    """
    Enhanced VideoGenerator that renders dialogue based on actual audio duration
    """
    
    def __init__(self, imagemagick_path=None):
        if imagemagick_path and os.path.exists(imagemagick_path):
            os.environ['IMAGEMAGICK_BINARY'] = imagemagick_path

    @staticmethod
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

    @staticmethod
    def estimate_text_dimensions(text, fontsize, max_width):
        """Estimate the dimensions needed for text based on character count and word wrapping"""
        char_width = fontsize * 0.6
        line_height = fontsize * 1.4
        
        chars_per_line = int(max_width / char_width)
        
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
        
        estimated_height = len(lines) * line_height + 20
        estimated_width = min(max_width, max(len(line) * char_width for line in lines) + 20)
        
        return int(estimated_width), int(estimated_height), len(lines)

    @staticmethod
    def create_custom_border(size, border_width=3, border_color=(218, 165, 32), bg_color=(0, 0, 0)):
        """Create a custom border using ColorClips"""
        width, height = size
        
        background = ColorClip(size=(width, height), color=bg_color).set_opacity(0.8)
        
        top_border = ColorClip(size=(width, border_width), color=border_color)
        bottom_border = ColorClip(size=(width, border_width), color=border_color).set_position((0, height - border_width))
        left_border = ColorClip(size=(border_width, height), color=border_color)
        right_border = ColorClip(size=(border_width, height), color=border_color).set_position((width - border_width, 0))
        
        bordered_clip = CompositeVideoClip([background, top_border, bottom_border, left_border, right_border], size=(width, height))
        return bordered_clip

    @staticmethod
    def find_audio_file_flexible(sequence_num, character_name, start_time, end_time, audio_dir, verbose=False):
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
        
        if verbose and os.path.exists(audio_dir):
            print(f"  Files in {audio_dir}:")
            for file in os.listdir(audio_dir):
                if file.endswith('.wav'):
                    print(f"    - {file}")
        
        return None

    def get_audio_duration(self, audio_file_path):
        """Get the actual duration of an audio file"""
        try:
            temp_audio = AudioFileClip(audio_file_path)
            duration = temp_audio.duration
            temp_audio.close()
            return duration
        except Exception as e:
            print(f"Error getting audio duration from {audio_file_path}: {e}")
            return None

    def calculate_dynamic_timeline(self, scene_data, audio_dir, start_delay=2.0, verbose=False):
        """
        Calculate dynamic timeline based on actual audio durations
        Returns a list of dialogue timing information
        """
        timeline = []
        current_time = start_delay
        gap_between_dialogues = 0.5  # Half second gap between dialogues
        
        for i, dialogue in enumerate(scene_data['scene']['dialogues']):
            char_name = dialogue.get('character', 'Unknown')
            line_text = dialogue.get('line', '')
            
            # Try to find and get audio duration
            audio_file_path = None
            audio_duration = None
            
            if audio_dir:
                audio_file_path = self.find_audio_file_flexible(
                    sequence_num=i,
                    character_name=char_name,
                    start_time=dialogue['start'],
                    end_time=dialogue['end'],
                    audio_dir=audio_dir,
                    verbose=verbose
                )
                
                if audio_file_path:
                    audio_duration = self.get_audio_duration(audio_file_path)
                    if verbose:
                        print(f"Audio duration for {char_name}: {audio_duration}s")
            
            # Fallback to scene data timing if no audio found
            if audio_duration is None:
                start_sec = self.convert_time_to_seconds(dialogue['start'])
                end_sec = self.convert_time_to_seconds(dialogue['end'])
                audio_duration = end_sec - start_sec
                if verbose:
                    print(f"Using scene timing for {char_name}: {audio_duration}s")
            
            # Ensure minimum duration
            audio_duration = max(audio_duration, 1.0)
            
            timeline_entry = {
                'index': i,
                'character': char_name,
                'line': line_text,
                'start_time': current_time,
                'end_time': current_time + audio_duration,
                'duration': audio_duration,
                'audio_file': audio_file_path,
                'original_start': dialogue['start'],
                'original_end': dialogue['end']
            }
            
            timeline.append(timeline_entry)
            current_time += audio_duration + gap_between_dialogues
        
        return timeline

    def generate_video_dynamic(
        self,
        background_image_path,
        scene_data_path,
        output_path,
        audio_dir=None,
        character_positions=None,
        font_size=20,
        font_color='gold',
        gap_between_dialogues=0.5,
        start_delay=2.0,
        verbose=False
    ):
        """
        Generate video with dynamic timing based on actual audio durations
        
        Args:
            background_image_path (str): Path to background image file
            scene_data_path (str): Path to scene data JSON file
            output_path (str): Path for output video file
            audio_dir (str, optional): Directory containing audio files
            character_positions (dict, optional): Character positioning configuration
            font_size (int): Text font size (default: 20)
            font_color (str): Text color (default: 'gold')
            gap_between_dialogues (float): Gap between dialogues in seconds
            verbose (bool): Enable detailed logging (default: False)
        
        Returns:
            bool: True if successful, False otherwise
        """
        
        try:
            # Validate input files
            if not os.path.exists(background_image_path):
                raise FileNotFoundError(f"Background image not found: {background_image_path}")
            
            if not os.path.exists(scene_data_path):
                raise FileNotFoundError(f"Scene data file not found: {scene_data_path}")

            # Load scene data
            with open(scene_data_path, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)

            # Calculate dynamic timeline
            timeline = self.calculate_dynamic_timeline(
                scene_data, audio_dir, start_delay=start_delay, verbose=verbose
            )
            
            # Calculate total video duration based on timeline
            if timeline:
                video_duration = timeline[-1]['end_time'] + 2.0  # Add 2 seconds buffer at end
            else:
                video_duration = 10.0  # Default fallback
            
            if verbose:
                print(f"Dynamic video duration: {video_duration} seconds")
                print(f"Timeline has {len(timeline)} dialogues")

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

            # Create clips for each dialogue using dynamic timeline
            all_clips = [background_clip]
            audio_clips = []
            
            use_audio = audio_dir is not None and os.path.exists(audio_dir)
            
            if verbose:
                if use_audio:
                    print(f"Audio processing enabled. Audio directory: {audio_dir}")
                else:
                    print("Audio processing disabled.")

            for entry in timeline:
                start_sec = entry['start_time']
                end_sec = entry['end_time']
                line_duration = entry['duration']
                char_name = entry['character']
                line_text = entry['line']
                audio_file_path = entry['audio_file']
                
                if verbose:
                    print(f"Processing: {char_name} from {start_sec:.2f}s to {end_sec:.2f}s (duration: {line_duration:.2f}s)")

                # Set fade duration
                FADE_DURATION = min(0.2, line_duration / 6.0)
                
                text_content = f"{char_name}: {line_text}"
                
                # Audio processing with dynamic duration
                if use_audio and audio_file_path and os.path.exists(audio_file_path):
                    try:
                        if verbose:
                            print(f"Loading audio file: {audio_file_path}")
                        
                        audio_clip = AudioFileClip(audio_file_path)
                        # Don't trim the audio - let it play for its full duration
                        audio_clip = audio_clip.set_start(start_sec)
                        
                        # Only trim if audio is significantly longer than expected
                        if audio_clip.duration > line_duration * 1.2:  # 20% tolerance
                            if verbose:
                                print(f"Trimming audio from {audio_clip.duration}s to {line_duration}s")
                            audio_clip = audio_clip.subclip(0, line_duration)
                        
                        audio_clips.append(audio_clip)
                        
                        if verbose:
                            print(f"Successfully added audio for {char_name} (duration: {audio_clip.duration}s)")
                            
                    except Exception as e:
                        if verbose:
                            print(f"Error processing audio for {char_name}: {e}")

                # # Get character positioning
                # if char_name in character_positions:
                #     char_config = character_positions[char_name]
                #     side = char_config.get("side", "left")
                #     max_width = char_config.get("max_width", 400)
                # else:
                #     if verbose:
                #         print(f"WARNING: No position config for '{char_name}', using default.")
                #     side = "left"
                #     max_width = 400

                # try:
                #     # Estimate text dimensions
                #     text_width, text_height, num_lines = self.estimate_text_dimensions(text_content, font_size, max_width)
                    
                #     # Add padding to the border
                #     border_padding = 10
                #     border_width = text_width + border_padding
                #     border_height = text_height + border_padding
                    
                #     # Calculate positions based on side
                #     margin = 40
                #     bottom_margin = 60
                    
                #     if side == "left":
                #         text_x = margin + border_padding // 2
                #         border_x = margin
                #     else:  # right side
                #         text_x = W - margin - text_width - border_padding // 2
                #         border_x = W - margin - border_width
                    
                #     # Position from bottom
                #     text_y = H - bottom_margin - text_height - border_padding // 2
                #     border_y = H - bottom_margin - border_height
                    
                #     if verbose:
                #         print(f"  Text dimensions: {text_width}x{text_height} ({num_lines} lines)")
                #         print(f"  Position: ({text_x}, {text_y})")

                #     # Create custom border background
                #     dialogue_border = self.create_custom_border((border_width, border_height))
                #     dialogue_border = (dialogue_border
                #                      .set_start(start_sec)
                #                      .set_duration(line_duration)
                #                      .set_position((border_x, border_y)))
                    
                #     # Apply fade to border
                #     if FADE_DURATION > 0:
                #         dialogue_border = fadein(dialogue_border, FADE_DURATION)
                #         dialogue_border = fadeout(dialogue_border, FADE_DURATION)
                    
                #     all_clips.append(dialogue_border)

                #     # Create text clip
                #     text_clip = (
                #         TextClip(
                #             txt=text_content,
                #             fontsize=font_size,
                #             color=font_color,
                #             font='Arial-Bold',
                #             method='caption',
                #             size=(text_width, text_height),
                #             align='center',
                #             interline=3
                #         )
                #         .set_start(start_sec)
                #         .set_duration(line_duration)
                #         .set_position((text_x, text_y))
                #     )
                # Get character positioning
                if char_name in character_positions:
                    char_config = character_positions[char_name]
                    side = char_config.get("side", "left")         # left | right
                    vertical = char_config.get("vertical", "bottom")  # top | bottom
                    max_width = char_config.get("max_width", 400)
                else:
                    if verbose:
                        print(f"WARNING: No position config for '{char_name}', using default.")
                    side = "left"
                    vertical = "bottom"
                    max_width = 400

                try:
                    # Estimate text dimensions
                    text_width, text_height, num_lines = self.estimate_text_dimensions(
                        text_content, font_size, max_width
                    )

                    # Add padding to the border
                    border_padding = 10
                    border_width = text_width + border_padding
                    border_height = text_height + border_padding

                    # Margins
                    margin_x = 40
                    margin_y = 60

                    # Horizontal placement
                    if side == "left":
                        text_x = margin_x + border_padding // 2
                        border_x = margin_x
                    else:  # right side
                        text_x = W - margin_x - text_width - border_padding // 2
                        border_x = W - margin_x - border_width

                    # Vertical placement
                    if vertical == "top":
                        text_y = margin_y + border_padding // 2
                        border_y = margin_y
                    else:  # bottom
                        text_y = H - margin_y - text_height - border_padding // 2
                        border_y = H - margin_y - border_height

                    if verbose:
                        print(f"  Text dimensions: {text_width}x{text_height} ({num_lines} lines)")
                        print(f"  Position: ({text_x}, {text_y}) [side={side}, vertical={vertical}]")

                    # Create custom border background
                    dialogue_border = self.create_custom_border((border_width, border_height))
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
                output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac' if has_audio else None,
                audio=has_audio,
                verbose=verbose,
                logger='bar' if verbose else None
            )
            
            if verbose:
                print(f"Video saved successfully: {output_path}")

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


# Convenience function for dynamic video generation
def create_dynamic_video_with_audio(
    background_image_path,
    scene_data_json_path,
    output_file,
    character_positions=None,
    font_size=20,
    font_color='gold',
    audio_dir=None,
    gap_between_dialogues=0.5,
    start_delay=2.0,
    verbose=False
):
    """
    Convenience function to create a video with dynamic audio-based timing
    
    Args:
        background_image_path (str): Path to background image
        scene_data_json_path (str): Path to scene data JSON file
        output_file (str): Path for output video file
        character_positions (dict, optional): Character positioning config
        font_size (int): Text font size
        font_color (str): Text color
        audio_dir (str, optional): Directory containing audio files
        gap_between_dialogues (float): Gap between dialogues in seconds
        verbose (bool): Enable detailed logging
    
    Returns:
        bool: True if successful, False otherwise
    """
    generator = DynamicVideoGenerator()
    return generator.generate_video_dynamic(
        background_image_path=background_image_path,
        scene_data_path=scene_data_json_path,
        output_path=output_file,
        audio_dir=audio_dir,
        character_positions=character_positions,
        font_size=font_size,
        font_color=font_color,
        gap_between_dialogues=gap_between_dialogues,
        start_delay=start_delay,
        verbose=verbose
    )


# Hybrid approach - combine both original and dynamic methods
class HybridVideoGenerator(DynamicVideoGenerator):
    """
    Hybrid generator that can use either static timing or dynamic timing
    """
    
    def generate_video_hybrid(
        self,
        background_image_path,
        scene_data_path,
        output_path,
        audio_dir=None,
        character_positions=None,
        font_size=20,
        font_color='gold',
        use_dynamic_timing=True,
        gap_between_dialogues=0.5,
        verbose=False
    ):
        """
        Generate video using either dynamic or static timing
        
        Args:
            use_dynamic_timing (bool): If True, use audio-based timing. If False, use scene data timing.
        """
        if use_dynamic_timing and audio_dir:
            return self.generate_video_dynamic(
                background_image_path=background_image_path,
                scene_data_path=scene_data_path,
                output_path=output_path,
                audio_dir=audio_dir,
                character_positions=character_positions,
                font_size=font_size,
                font_color=font_color,
                gap_between_dialogues=gap_between_dialogues,
                verbose=verbose
            )
        else:
            # Fallback to original static timing method
            from framing import VideoGenerator
            original_generator = VideoGenerator()
            return original_generator.generate_video(
                background_image_path=background_image_path,
                scene_data_path=scene_data_path,
                output_path=output_path,
                audio_dir=audio_dir,
                character_positions=character_positions,
                font_size=font_size,
                font_color=font_color,
                verbose=verbose
            )