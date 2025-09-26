from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import ffmpeg
import shutil
from pydantic import BaseModel
from dotenv import load_dotenv
from invoke import InvokeClient
from gemini_client import GeminiClient
import asyncio

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

def generate_video_from_images_and_audio():
    print("Starting video generation...")
    image_folder = os.path.join(BASE_DIR, 'images')
    audio_folder = os.path.join(BASE_DIR, 'audio')
    output_video_path = os.path.join(BASE_DIR, 'video.mp4')

    print(f"Image folder: {image_folder}, Audio folder: {audio_folder}, Output: {output_video_path}")

    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
    if not os.path.exists(audio_folder):
        os.makedirs(audio_folder)

    image_files = sorted([f for f in os.listdir(image_folder) if f.endswith('.jpeg')], key=lambda x: int(x.split('.')[0]))
    audio_files = sorted([f for f in os.listdir(audio_folder) if f.endswith('.wav')], key=lambda x: int(x.split('.')[0]))

    print(f"Found image files: {image_files}")
    print(f"Found audio files: {audio_files}")

    if not image_files or not audio_files:
        print("No image or audio files found, skipping video generation.")
        return

    # Create a temporary file listing images and their durations for ffmpeg
    input_txt_path = os.path.join(BASE_DIR, "input.txt")
    print(f"Creating {input_txt_path} for image sequence...")
    with open(input_txt_path, "w") as f:
        for image in image_files:
            f.write(f"file '{os.path.join(image_folder, image)}'\n")
            f.write("duration 15\n")
    
    # Ensure the last image has a duration to avoid ffmpeg hanging
    if image_files:
        with open(input_txt_path, "a") as f:
            f.write(f"file '{os.path.join(image_folder, image_files[-1])}'\n")
    print("input.txt created.")

    # Concatenate audio files
    print("Preparing audio concatenation...")
    audio_inputs = [ffmpeg.input(os.path.join(audio_folder, f)) for f in audio_files]
    concatenated_audio = ffmpeg.concat(*audio_inputs, v=0, a=1)

    # Create video from images
    print("Preparing video stream from images...")
    video_from_images = ffmpeg.input(input_txt_path, f='concat', safe='0')

    # Add a scale filter to ensure width and height are divisible by 2
    video_from_images = video_from_images.filter('scale', 'trunc(iw/2)*2', 'trunc(ih/2)*2')

    # Combine video and audio
    stream = ffmpeg.output(video_from_images, concatenated_audio, output_video_path, **{'c:v': 'libx264', 'c:a': 'aac', 'b:a': '192k', 'pix_fmt': 'yuv420p', 'shortest': None})
    
    print("Compiling ffmpeg command...")
    args = ffmpeg.get_args(stream)
    print(f"Running ffmpeg command: {' '.join(args)}")

    stream.run(overwrite_output=True)
    
    print("ffmpeg command finished.")

    # Clean up temporary file
    print("Cleaning up temporary files...")
    os.remove(input_txt_path)
    print("Video generation complete.")

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
            else:
                print("Failed to generate image from InvokeClient")
        else:
            print("Missing background description or characters in scene data")
            
    except Exception as e:
        print(f"Error generating images from scene: {e}")

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
        await generate_images_from_scene(gemini_result)
        
        # Step 4: Generate audio (placeholder for now)
        await websocket.send_json({"status": "Generating voice audio"})
        # TODO: Implement actual audio generation
        
        # Step 5: Combine into video
        await websocket.send_json({"status": "Combining into final video"})
        generate_video_from_images_and_audio()
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