import json
import os
os.environ['IMAGEMAGICK_BINARY'] = r'D:\ImageMagick-7.1.2-Q16-HDRI\magick.exe'

from moviepy.editor import ImageClip, TextClip, CompositeVideoClip
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


def process_scene_with_dialogues_and_frame(
    background_image_path,
    overlay_frame_path,
    scene_data_json_path,
    output_file,
    character_text_coords,
    font_size=35,
    font_color='gold'
):
    for p in (background_image_path, overlay_frame_path, scene_data_json_path):
        if not os.path.exists(p):
            raise FileNotFoundError(f"Required file not found: {p}")

    with open(scene_data_json_path, 'r', encoding='utf-8') as f:
        scene_data = json.load(f)

    scene_end_time = scene_data['scene']['background']['end']
    video_duration = float(convert_time_to_seconds(scene_end_time))

    background_clip = ImageClip(background_image_path).set_duration(video_duration)
    W, H = background_clip.size

    overlay_frame_clip = ImageClip(overlay_frame_path).set_duration(video_duration).resize((W, H))

    text_clips = []
    for dialogue in scene_data['scene']['dialogues']:
        start_sec = convert_time_to_seconds(dialogue['start'])
        end_sec = convert_time_to_seconds(dialogue['end'])
        line_duration = end_sec - start_sec
        if line_duration <= 0:
            continue

        FADE_DURATION = min(0.5, line_duration / 2.0)
        char_name = dialogue.get('character', 'Unknown')
        if char_name in character_text_coords:
            coords = character_text_coords[char_name]
            text_pos = coords.get("position", (W // 2, H - 150))
            text_size = coords.get("size", (400, 100))
        else:
            print(f"WARNING: No coords for '{char_name}', using default.")
            text_pos = (W // 2 - 200, H - 150)
            text_size = (400, 100)

        text_content = f"{char_name}: {dialogue.get('line', '')}"

        text_clip = (
            TextClip(
                txt=text_content,
                fontsize=font_size,
                color=font_color,
                method='caption',  # safe fallback, no ImageMagick needed
                size=text_size
            )
            .set_start(start_sec)
            .set_duration(line_duration)
            .set_pos(text_pos)
        )

        text_clip = fadein(text_clip, FADE_DURATION)
        text_clip = fadeout(text_clip, FADE_DURATION)

        text_clips.append(text_clip)

    final_clip = CompositeVideoClip([background_clip, overlay_frame_clip] + text_clips, size=(W, H))

    print(f"Rendering video (duration={video_duration:.2f}s, resolution={W}x{H}) ...")
    final_clip.write_videofile(
        output_file,
        fps=24,
        codec='libx264',
        audio=False,
        verbose=True
    )
    print(f"Saved: {output_file}")


if __name__ == '__main__':
    BACKGROUND_IMAGE_FILE = 'background_image.jpg'
    OVERLAY_FRAME_IMAGE = 'ornate_frame.png'
    SCENE_DATA_JSON_FILE = 'scene_data.json'
    OUTPUT_VIDEO_FILE = 'test_dialogue_video.mp4'

    CHARACTER_TEXT_COORDS = {
        "Scorpion": {"position": (100, 600), "size": (500, 100)},
        "Frog": {"position": (680, 600), "size": (500, 100)}
    }

    if not os.path.exists(SCENE_DATA_JSON_FILE):
        DUMMY_JSON = {
            "scene": {
                "background": {"end": "00:00:20"},
                "dialogues": [
                    {"character": "Scorpion", "start": "00:00:02", "end": "00:00:08",
                     "line": "Test 1: Scorpion begins to speak and the text fades in on the left side."},
                    {"character": "Frog", "start": "00:00:09", "end": "00:00:18",
                     "line": "Test 2: Frog replies, and this text fades in on the right side. Check the positioning!"}
                ]
            }
        }
        with open(SCENE_DATA_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(DUMMY_JSON, f, indent=4)

    process_scene_with_dialogues_and_frame(
        background_image_path=BACKGROUND_IMAGE_FILE,
        overlay_frame_path=OVERLAY_FRAME_IMAGE,
        scene_data_json_path=SCENE_DATA_JSON_FILE,
        output_file=OUTPUT_VIDEO_FILE,
        character_text_coords=CHARACTER_TEXT_COORDS
    )
