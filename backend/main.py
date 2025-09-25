from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import ffmpeg
import shutil
from pydantic import BaseModel

from gemini_client import GeminiClient

# --- Configuration ---
# It's recommended to set this in your environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
if GEMINI_API_KEY == "YOUR_API_KEY_HERE":
    print("Warning: GEMINI_API_KEY not set. Using a placeholder.")

# Get the absolute path of the directory where the script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- FastAPI App and Gemini Client Initialization ---
app = FastAPI()
gemini_client = GeminiClient(api_key=GEMINI_API_KEY)

# Add CORS middleware to allow requests from any origin
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

def generate_video_stream():
    video_path = os.path.join(BASE_DIR, "video.mp4")
    with open(video_path, "rb") as video_file:
        while True:
            chunk = video_file.read(1024 * 1024) # Read 1MB chunks
            if not chunk:
                break
            yield chunk

@app.post("/video")
async def stream_video(request: VideoRequest):
    print(f"Received request for /video with prompt: {request.prompt}")

    # 1. Clean up previous run
    cleanup_directories()

    # 2. Use Gemini to get a script or instructions
    # For now, we'll just print the result from Gemini
    # In the future, this result will drive image and audio generation
    print("Asking Gemini for a response...")
    gemini_result = gemini_client.ask(request.prompt)
    print("Received from Gemini:")
    print(gemini_result)

    # This is where you would add logic to:
    # a. Parse gemini_result
    # b. Generate images based on the result and save them to the 'images' folder
    # c. Generate audio based on the result and save it to the 'audio' folder

    # 3. Generate the video from the (not yet created) files
    generate_video_from_images_and_audio()

    # 4. Stream the video
    video_path = os.path.join(BASE_DIR, "video.mp4")
    if not os.path.exists(video_path):
        print("Video file not found after generation attempt.")
        return Response(status_code=404, content="Video not found. This is expected since image/audio generation from the prompt is not yet implemented.")
    
    print("Streaming video...")
    return StreamingResponse(generate_video_stream(), media_type="video/mp4")