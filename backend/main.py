from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from pydantic import BaseModel
from dotenv import load_dotenv
from invoke import InvokeClient
from gemini_client import GeminiClient
from video_gen import generate_video_from_scene_data
from voice_generation import VoiceSynthesizer

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

# Helper functions moved to video_gen module

# Border creation is now handled by video_gen module

# Old video generation function removed - now handled by video_gen module

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
        
        # Step 4: Generate voice audio
        await websocket.send_json({"status": "Generating voice audio"})
        try:
            # Set up voice synthesizer
            voice_dir = os.path.join(BASE_DIR, "voices")  # Assuming voices are in backend/voices/
            audio_dir = os.path.join(BASE_DIR, "audio")
            
            print(f"Voice directory: {voice_dir}")
            print(f"Audio output directory: {audio_dir}")
            print(f"Voice directory exists: {os.path.exists(voice_dir)}")
            
            if os.path.exists(voice_dir):
                # Create audio directory if it doesn't exist
                os.makedirs(audio_dir, exist_ok=True)
                
                synthesizer = VoiceSynthesizer(voice_dir, audio_dir)
                
                # Extract dialogues and characters from scene data
                scene_info = scene_data.get('scene', {})
                dialogues = scene_info.get('dialogues', [])
                characters = scene_info.get('characters', [])
                
                print(f"Found {len(dialogues)} dialogues and {len(characters)} characters")
                print(f"Dialogues: {[d.get('character', 'Unknown') + ': ' + d.get('line', '')[:30] + '...' for d in dialogues[:3]]}")
                
                if dialogues and characters:
                    print(f"Synthesizing {len(dialogues)} dialogue lines for {len(characters)} characters")
                    synthesizer.synthesize_dialogues(dialogues, characters)
                    
                    # Verify audio files were created
                    audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]
                    print(f"Created {len(audio_files)} audio files: {audio_files}")
                    print("Voice synthesis completed successfully")
                else:
                    print("No dialogues or characters found for voice synthesis")
            else:
                print(f"Voice directory not found at {voice_dir}, skipping voice synthesis")
                print(f"Available directories in {BASE_DIR}: {[d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]}")
        except Exception as e:
            print(f"Error during voice synthesis: {e}")
            import traceback
            traceback.print_exc()
            # Continue without audio - video generation can still work
        
        # Step 5: Combine into video with dialogue overlays
        await websocket.send_json({"status": "Combining into final video with dialogues"})
        
        # Verify audio files exist before video generation
        audio_dir = os.path.join(BASE_DIR, "audio")
        if os.path.exists(audio_dir):
            audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]
            print(f"Audio files available for video generation: {audio_files}")
            if audio_files:
                print("Audio files will be integrated into the video")
            else:
                print("No audio files found - video will be generated without audio")
        else:
            print("Audio directory not found - video will be generated without audio")
        
        # Use the new video_gen module with detailed logging
        print("Starting video generation with scene data and audio files...")
        print(f"Scene data contains {len(scene_data.get('scene', {}).get('dialogues', []))} dialogues")
        
        success = generate_video_from_scene_data(BASE_DIR, scene_data)
        if not success:
            await websocket.send_json({"status": "error", "message": "Video generation failed"})
            return
        
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