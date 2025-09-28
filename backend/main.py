from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from pydantic import BaseModel
from dotenv import load_dotenv
from invoke import InvokeClient
from gemini_client import GeminiClient
from video_gen import generate_video_from_scene_data, SPEECH_BUBBLE_CONFIGS
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

@app.get("/test-invoke")
async def test_invoke():
    """Test route to test InvokeAI image generation with mock Gemini data"""
    
    # Mock Gemini result
    mock_gemini_result = {
        'scene': {
            'background': {
                'description': 'A whimsical cartoon-style riverbank with oversized lily pads and cattails. The water is a serene blue, and the sky is a soft, gradient yellow to orange, indicating late afternoon.',
                'start': '00:00:00',
                'end': '00:00:45'
            },
            'characters': [
                {
                    'name': 'Ferdinand the Frog',
                    'appearance': 'A plump, cartoon-style green frog with big, friendly yellow eyes and a permanent wide smile. He wears a tiny red bow tie.',
                    'gender': 'male'
                },
                {
                    'name': 'Sterling the Scorpion',
                    'appearance': 'A sleek, cartoon-style purple scorpion with a long, segmented tail ending in a comically oversized, harmless-looking stinger. He has four tiny, black, beady eyes and wears a small, crooked top hat.',
                    'gender': 'male'
                }
            ],
            'dialogues': [
                {
                    'character': 'Ferdinand the Frog',
                    'start': '00:00:05',
                    'end': '00:00:12',
                    'line': "Good afternoon, Sterling! Lovely day for a swim, wouldn't you say?"
                },
                {
                    'character': 'Sterling the Scorpion',
                    'start': '00:00:15',
                    'end': '00:00:22',
                    'line': 'Indeed, Ferdinand. Though I, for one, prefer a leisurely stroll on dry land. The water, you see, is not quite my element.'
                },
                {
                    'character': 'Ferdinand the Frog',
                    'start': '00:00:25',
                    'end': '00:00:33',
                    'line': 'Ah, to each their own! But if you ever change your mind, these lily pads are quite comfortable for sunbathing.'
                },
                {
                    'character': 'Sterling the Scorpion',
                    'start': '00:00:36',
                    'end': '00:00:43',
                    'line': 'Perhaps one day, my amphibious friend. Perhaps one day.'
                }
            ]
        }
    }
    
    try:
        # Clean up old files first
        cleanup_directories()
        
        # Extract scene data
        scene_data = mock_gemini_result.get('scene', {})
        background_desc = scene_data.get('background', {}).get('description', '')
        characters = scene_data.get('characters', [])
        
        print(f"Testing InvokeAI with:")
        print(f"Background: {background_desc}")
        print(f"Characters: {[char.get('name', 'Unknown') for char in characters]}")
        
        if background_desc and characters:
            # Extract character prompts (appearances)
            character_prompts = []
            for char in characters:
                appearance = char.get('appearance', '')
                if appearance:
                    character_prompts.append(appearance)
            
            print(f"Character prompts: {character_prompts}")
            
            # Create InvokeClient with test data
            client = InvokeClient(
                background_prompt=background_desc,
                character_prompts=character_prompts
            )
            
            # Generate the complete scene
            print("Starting test image generation...")
            final_image = client.generate_complete_scene()
            
            if final_image:
                # Save the generated image
                image_path = os.path.join(BASE_DIR, "images", "test_scene.png")
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                final_image.save(image_path)
                print(f"Test image saved to: {image_path}")
                
                return {
                    "status": "success",
                    "message": "Test image generation completed successfully",
                    "image_path": image_path,
                    "scene_data": mock_gemini_result
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to generate test image"
                }
        else:
            return {
                "status": "error",
                "message": "Missing background description or characters in test data"
            }
            
    except Exception as e:
        print(f"Error during test image generation: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Test failed: {str(e)}"
        }

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

async def generate_images_from_scene(gemini_result, websocket=None):
    """Generate images based on the Gemini scene data with progress updates"""
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
        
        if websocket:
            await websocket.send_json({"status": "Setting up image generation"})
        
        if background_desc and characters:
            # Extract character prompts (just appearances)
            character_prompts = []
            for char in characters:
                appearance = char.get('appearance', '')
                if appearance:
                    character_prompts.append(appearance)
            
            print(f"Character prompts: {character_prompts}")
            
            if websocket:
                await websocket.send_json({"status": "Creating AI image prompts"})
            
            # Create InvokeClient with background and character prompts
            client = InvokeClient(
                background_prompt=background_desc,
                character_prompts=character_prompts
            )
            
            if websocket:
                await websocket.send_json({"status": "Generating scene with Stable Diffusion"})
            
            # Generate the complete scene
            print("Generating complete scene with InvokeClient...")
            
            # Run the image generation in a thread to avoid blocking
            import asyncio
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(client.generate_complete_scene)
                
                # Send progress updates while waiting for completion
                while not future.done():
                    pass
                
                # Wait for the image generation to complete (equivalent to thread.join())
                final_image = future.result(timeout=300)  # 5 minute timeout
            
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
        cleanup_directories()
        
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
        
        scene_data = await generate_images_from_scene(gemini_result, websocket)
        
        if not scene_data:
            await websocket.send_json({"status": "error", "message": "Failed to generate images"})
            return
        
        await websocket.send_json({"status": "Images generated successfully"})
        
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
                    
                    # Run voice synthesis in a thread to allow progress updates
                    import asyncio
                    import concurrent.futures
                    
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        voice_future = executor.submit(synthesizer.synthesize_dialogues, dialogues, characters)
                        
                        # Wait for voice synthesis to complete (equivalent to thread.join())
                        voice_future.result(timeout=120)  # 2 minute timeout
                    
                    # Verify audio files were created
                    audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]
                    print(f"Created {len(audio_files)} audio files: {audio_files}")
                    await websocket.send_json({"status": "Voice synthesis completed successfully"})
                    print("Voice synthesis completed successfully")
                else:
                    await websocket.send_json({"status": "No dialogues found, continuing without audio"})
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
        
        # Use the new video_gen module with improved speech bubbles
        print("Starting video generation with scene data and audio files...")
        print(f"Scene data contains {len(scene_data.get('scene', {}).get('dialogues', []))} dialogues")
        
        # Generate dynamic character positions based on actual characters from Gemini
        scene_info = scene_data.get('scene', {})
        characters = scene_info.get('characters', [])
        
        # Create character positions dynamically
        character_positions = {}
        sides = ["left", "right"]  # Alternate between left and right
        
        for i, character in enumerate(characters):
            char_name = character.get('name', f'Character_{i+1}')
            side = sides[i % len(sides)]  # Alternate sides
            
            character_positions[char_name] = {
                "side": side,
                "max_width": 450,  # Use modern bubble width
                "tail_side": side  # Tail points in same direction as position
            }
        
        # Use modern_bubbles config as default (best looking)
        bubble_config = SPEECH_BUBBLE_CONFIGS.get("modern_bubbles", {})
        
        print(f"Generated character positions: {list(character_positions.keys())}")
        print(f"Using speech bubble config: modern_bubbles")
        
        # Run video generation in a thread
        import asyncio
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            video_future = executor.submit(
                generate_video_from_scene_data,
                BASE_DIR, 
                scene_data, 
                character_positions
            )
            
            # Wait for video generation to complete (equivalent to thread.join())
            success = video_future.result(timeout=600)  # 10 minute timeout for video generation
        
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