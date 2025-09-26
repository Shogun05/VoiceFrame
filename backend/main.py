from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from pydantic import BaseModel
from dotenv import load_dotenv
from invoke import InvokeClient
from gemini_client import GeminiClient
import asyncio

# MoviePy imports for video generation
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, ColorClip
from moviepy.video.fx.all import fadein, fadeout

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file or environment.")

# Get the absolute path of the directory where the script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- FastAPI App and Gemini Client Initialization ---
app = FastAPI()
gemini_client = GeminiClient(api_key=GEMINI_API_KEY)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- Pydantic Models ---
class VideoRequest(BaseModel):
    prompt: str

# --- Helper Functions ---
@app.get("/")
def read_root():
    return {"Hello": "World"}

def cleanup_directories():
    """Removes old generated files and directories."""
    print("Cleaning up old files and directories...")
    
    import shutil
    image_folder = os.path.join(BASE_DIR, 'images')
    audio_folder = os.path.join(BASE_DIR, 'audio')
    output_video_path = os.path.join(BASE_DIR, 'video.mp4')
    
    if os.path.exists(image_folder):
        shutil.rmtree(image_folder)
    if os.path.exists(audio_folder):
        shutil.rmtree(audio_folder)
    if os.path.exists(output_video_path):
        os.remove(output_video_path)
    
    print("Cleanup complete.")

def convert_time_to_seconds(time_str):
    """Convert time string to seconds"""
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
    """Estimate the dimensions needed for text based on character count and word wrapping"""
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

def generate_video_from_images_and_audio(scene_data=None):
    print("Starting video generation with dialogue overlays...")
    image_folder = os.path.join(BASE_DIR, 'images')
    output_video_path = os.path.join(BASE_DIR, 'video.mp4')

    print(f"Image folder: {image_folder}, Output: {output_video_path}")

    if not os.path.exists(image_folder):
        print("No images folder found, cannot generate video.")
        return

    image_files = sorted([f for f in os.listdir(image_folder) if f.endswith('.jpeg')], key=lambda x: int(x.split('.')[0]))
    print(f"Found image files: {image_files}")

    if not image_files:
        print("No image files found, skipping video generation.")
        return

    # Get the first (and likely only) background image
    background_image_path = os.path.join(image_folder, image_files[0])
    
    if not scene_data:
        print("No scene data provided, creating simple video without dialogues.")
        # Fallback to simple video generation
        background_clip = ImageClip(background_image_path).set_duration(15)
        background_clip.write_videofile(output_video_path, fps=24, codec='libx264', audio=False)
        background_clip.close()
        return

    # Extract scene information
    scene_info = scene_data.get('scene', {})
    background_info = scene_info.get('background', {})
    dialogues = scene_info.get('dialogues', [])
    
    # Calculate video duration from scene end time
    scene_end_time = background_info.get('end', '00:01:30')
    video_duration = convert_time_to_seconds(scene_end_time)
    print(f"Video duration: {video_duration} seconds")

    # Create background clip
    background_clip = ImageClip(background_image_path).set_duration(video_duration)
    W, H = background_clip.size
    print(f"Background size: {W}x{H}")

    # Character positions configuration
    character_positions = {
        "Scorpion": {"side": "left", "max_width": 450},
        "Frog": {"side": "right", "max_width": 450}
    }

    # Create clips for each dialogue with dynamic sizing
    all_clips = [background_clip]  # Start with background
    font_size = 20
    font_color = 'gold'
    
    for i, dialogue in enumerate(dialogues):
        try:
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
        output_video_path,
        fps=24,
        codec='libx264',
        audio=False,
        verbose=False,
        logger=None
    )
    print(f"Video saved successfully: {output_video_path}")

    # Clean up
    final_clip.close()
    for clip in all_clips:
        try:
            clip.close()
        except:
            pass

async def generate_images_from_scene(gemini_result):
    """Generate images based on the Gemini scene data"""
    print("Starting image generation from scene data...")
    
    # Create images directory
    image_folder = os.path.join(BASE_DIR, 'images')
    os.makedirs(image_folder, exist_ok=True)
    
    try:
        scene_data = gemini_result.get('scene', {})
        background_desc = scene_data.get('background', {}).get('description', '')
        characters = scene_data.get('characters', [])
        
        print(f"Background description: {background_desc}")
        print(f"Characters: {[char.get('name', 'Unknown') for char in characters]}")
        
        if background_desc and characters:
            # Extract character prompts (just appearances)
            character_prompts = []
            for char in characters:
                appearance = char.get('appearance', '')
                if appearance:
                    character_prompts.append(appearance)
            
            print(f"Character prompts: {character_prompts}")
            
            # Create InvokeClient with background and character prompts
            client = InvokeClient(
                background_prompt=background_desc,
                character_prompts=character_prompts
            )
            
            # Generate the complete scene
            print("Generating complete scene with InvokeClient...")
            final_image = client.generate_complete_scene()
            
            if final_image:
                # Save the generated image as 1.jpeg in the images folder
                image_path = os.path.join(image_folder, "1.jpeg")
                final_image.save(image_path)
                print(f"Generated image saved to: {image_path}")
                
                # Return the scene data for video generation
                return gemini_result
            else:
                print("Failed to generate image from InvokeClient")
                return None
        else:
            print("Missing background description or characters in scene data")
            return None
            
    except Exception as e:
        print(f"Error generating images from scene: {e}")
        return None

def generate_video_stream():
    video_path = os.path.join(BASE_DIR, "video.mp4")
    with open(video_path, "rb") as video_file:
        while True:
            chunk = video_file.read(1024 * 1024)
            if not chunk:
                break
            yield chunk

@app.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    await websocket.accept()
    print("Client connected!")
    
    try:
        # Wait for the prompt from the frontend
        await websocket.send_json({"status": "Waiting for prompt..."})
        prompt_message = await websocket.receive_json()
        
        if "prompt" not in prompt_message:
            await websocket.send_json({"status": "error", "message": "No prompt provided"})
            return
        
        prompt = prompt_message["prompt"]
        print(f"Received prompt from frontend: {prompt}")
        
        if not prompt or prompt.strip() == "":
            await websocket.send_json({"status": "error", "message": "Empty prompt provided"})
            return
        
        # Step 1: Cleanup
        await websocket.send_json({"status": "Cleaning up previous files"})
        cleanup_directories()
        
        # Step 2: Generate script with Gemini
        await websocket.send_json({"status": "Generating script with AI"})
        optimized_prompt = f"Create a scene with characters optimized for stable diffusion image generation. Story about: {prompt}"
        gemini_result = gemini_client.ask(optimized_prompt)
        
        print("Received from Gemini:")
        print(gemini_result)
        
        if "error" in gemini_result:
            await websocket.send_json({"status": "error", "message": f"Failed to get valid script: {gemini_result['raw_output']}"})
            return
        
        # Step 3: Generate images
        await websocket.send_json({"status": "Generating characters and background images"})
        scene_data = await generate_images_from_scene(gemini_result)
        
        if not scene_data:
            await websocket.send_json({"status": "error", "message": "Failed to generate images"})
            return
        
        # Step 4: Generate audio (placeholder for now)
        await websocket.send_json({"status": "Generating voice audio"})
        # TODO: Implement actual audio generation
        
        # Step 5: Combine into video with dialogue overlays
        await websocket.send_json({"status": "Combining into final video with dialogues"})
        generate_video_from_images_and_audio(scene_data)
        video_path = os.path.join(BASE_DIR, "video.mp4")
        
        if not os.path.exists(video_path):
            await websocket.send_json({"status": "error", "message": "Video generation failed - file not found"})
            return
        
        # Generate unique video ID (use timestamp for now)
        import time
        video_id = f"video_{int(time.time())}"
        
        # Send completion with video_id
        await websocket.send_json({"status": "done", "video_id": video_id})
        print(f"Video generation completed! video_id: {video_id}")
        
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error during video generation: {e}")
        try:
            await websocket.send_json({"status": "error", "message": f"Generation failed: {str(e)}"})
        except:
            pass  # Connection might be closed

@app.get("/video/{video_id}")
async def stream_video(video_id: str):
    """Stream the generated video by video_id"""
    print(f"Streaming video for video_id: {video_id}")
    
    # In production, you'd map video_id to actual file paths
    # For now, we'll serve the generated video.mp4
    video_path = os.path.join(BASE_DIR, "video.mp4")
    
    if not os.path.exists(video_path):
        return Response(status_code=404, content="Video not found")
    
    print(f"Streaming video from: {video_path}")
    return StreamingResponse(generate_video_stream(), media_type="video/mp4")