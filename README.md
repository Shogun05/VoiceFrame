# VoiceFrame - AI Video Generation Platform

## Project Overview
VoiceFrame is a full-stack AI-powered video generation platform that creates videos with synchronized dialogue from text prompts. The system uses multiple AI services including Google Gemini for script generation, Stable Diffusion for image generation, voice synthesis for audio, and MoviePy for video assembly.


## Setup
1. Install uv: https://docs.astral.sh/uv/getting-started/installation/
2. Install npm: https://nodejs.org/en/download
3. [Setup Invoke](#invoke-setup-details)
4. [Setup project](#project-setup)
5. [Environment configuration](#environment-configuration)
6. [Voices Setup](#voices-setup)

## Invoke Setup Details:
1. Run the binary downloaded above
2. Go ahead and install it in any location (The location of installation does not matter)
3. After installation is complete, hit Launch to begin InvokeAI desktop application. 
4. Navigate to `Models` tab and at the top right corner of the screen, find the `Starter Models`.
5. Inside `Starter Models` install the `DreamShaper XL v2 Turbo`
6. Download the LoRA Model from this link: https://drive.google.com/file/d/1fXbewulnWMrup0AEylBXK5_J10oOw0nZ/view?usp=sharing
7. Place the download in a known location and copy the parent folder path
8. While being in the `Models` tab in the InvokeAI, Navigate to the `Scan Folder` option, beside, to the `Starter Models`, add in the path of the parent directory containing the LoRA and hit scan
9. You will see the LoRA `1990sCartoonsStyle_PXL_Leaf1.safetensors`. Installing that completes the setup required for image generation. Make sure to keep InvokeAI on henceforth when testing.

## Project Setup
1. Git clone this project using the command: 
```bash
git clone https://github.com/Shogun05/VoiceFrame.git
```
2. Navigate to the downloaded repo, head into the `backend` folder and create the files: 
   a. `.env`
   b. Directory (case-sensitive): `voices` with two more sub directories inside `voices` named (again, case-sensitive): `male` and `female`

### Environment Configuration
Grab your API key from here: https://aistudio.google.com/api-keys

Create a `.env` file in the `backend` directory with:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

## Voices setup
1. Get yourself some voices that you prefer from: https://huggingface.co/rhasspy/piper-voices
2. Correspondingly place the male and female voices in their respective directories so that the final directory strucutre looks something like this (We recommend `hfc_female` and `hfc_male`): 
```
voices
├── female
│   ├── en_US-amy-low.onnx
│   └── en_US-amy-low.onnx.json
└── male
    ├── en_US-joe-medium.onnx
    └── en_US-joe-medium.onnx.json
```
## Backend Setup
Navigate to `/backend` from the root of the repo.  
```bash
uv sync                             # install and sync dependencies
uv run python -m uvicorn main:app --port 8000   # start the backend server
```
## Frontend Setup
Navigate to `/frontend-app` from the root of the repo. 
```bash
npm i         # install dependencies
npm run dev   # run the expo app
```

(Optional) Set up Android Studio with Android Virtual Device downloaded during installation and you shall be able to use the Expo project on mobile.

---
## Architecture Overview

### Frontend (React Native with Expo)
- **Framework**: React Native with Expo SDK
- **Language**: TypeScript
- **Key Libraries**: 
  - `expo-video` for video playback
  - `expo-router` for navigation
  - `lucide-react-native` for icons
  - WebSocket for real-time progress updates

### Backend (FastAPI Python)
- **Framework**: FastAPI with WebSocket support
- **Language**: Python 3.8+
- **AI Services**:
  - Google Gemini API for script generation
  - InvokeAI/Stable Diffusion for image generation
  - Voice synthesis for audio generation
  - MoviePy for video assembly

---
---
## System Flow

### 1. User Input Processing
```
User enters prompt → Frontend sends to backend via WebSocket → Backend processes prompt
```

### 2. AI Pipeline Execution
```
1. Gemini AI Script Generation
2. Stable Diffusion Image Generation  
3. Voice Synthesis Audio Generation
4. MoviePy Video Assembly with Speech Bubbles
5. Real-time Progress Updates via WebSocket
```

### 3. Video Delivery
```
Video generation complete → Backend streams MP4 → Frontend displays with controls
```

## Detailed Component Breakdown

### Frontend Components

#### 1. Video Screen (`app/video.tsx`)
- **Purpose**: Main video generation and playback interface
- **Key Features**:
  - Real-time WebSocket progress tracking
  - Custom progress cards with gradient border effects
  - Video playback with download/share functionality
  - Error handling and toast notifications
- **State Management**:
  ```typescript
  const [progressSteps, setProgressSteps] = useState<{step: string, status: 'active' | 'completed' | 'error'}[]>([]);
  const [generationDone, setGenerationDone] = useState(false);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  ```

#### 2. FadingBorderButton Component (`components/FadingBorderButton.tsx`)
- **Purpose**: Reusable button with gradient border bleed effect
- **Visual Effects**:
  - 3-layer gradient overlays for border bleed
  - Customizable glow colors
  - Shadow effects for depth
  - Cross-platform compatibility
- **Props Interface**:
  ```typescript
  interface FadingBorderButtonProps {
    title: string;
    onPress: () => void;
    disabled?: boolean;
    glowColor?: string;
    backgroundColor?: string;
    textColor?: string;
    width?: number;
    height?: number;
  }
  ```

#### 3. WebSocket Communication
- **Connection**: `ws://localhost:8000/ws/progress`
- **Message Flow**:
  ```
  Backend: {"status": "Waiting for prompt..."}
  Frontend: {"prompt": "user input"}
  Backend: {"status": "Generating script with AI"}
  Backend: {"status": "Generating characters and background images"}
  Backend: {"status": "Images generated successfully"}
  Backend: {"status": "Generating voice audio"}  
  Backend: {"status": "Voice synthesis completed successfully"}
  Backend: {"status": "Combining into final video with dialogues"}
  Backend: {"status": "done", "video_id": "video_123"}
  ```

### Backend Architecture

#### 1. Main FastAPI Application (`main.py`)
- **WebSocket Endpoint**: `/ws/progress` for real-time updates
- **Video Streaming**: `/video/{video_id}` for MP4 delivery
- **CORS Configuration**: Allows all origins for development
- **Threading**: Uses `ThreadPoolExecutor` for non-blocking AI operations

#### 2. Gemini Client (`gemini_client.py`)
- **Purpose**: Interface with Google Gemini API for script generation
- **Input**: User text prompt
- **Output**: Structured scene data with characters, dialogues, and timing
- **Example Response Structure**:
  ```python
  {
    "scene": {
      "background": {
        "description": "...",
        "start": "00:00:00",
        "end": "00:01:30"
      },
      "characters": [
        {"name": "Character1", "appearance": "..."},
        {"name": "Character2", "appearance": "..."}
      ],
      "dialogues": [
        {
          "character": "Character1",
          "line": "Hello world",
          "start": "00:00:05",
          "end": "00:00:08"
        }
      ]
    }
  }
  ```

#### 3. InvokeAI Integration (`invoke.py`)
- **Purpose**: Generate images using Stable Diffusion
- **Process**: Takes character descriptions and background prompts
- **Output**: High-quality scene images saved to `/images/` directory
- **Configuration**: Uses local InvokeAI installation

#### 4. Voice Synthesis (`voice_generation.py`)
- **Purpose**: Convert dialogue text to speech
- **Input**: Character dialogues with timing information
- **Output**: Individual WAV files for each dialogue line
- **Features**: Character-specific voice assignment

#### 5. Video Generation (`video_gen.py`)
- **Purpose**: Assemble final video with synchronized audio and text overlays
- **Key Classes**:

##### ImprovedTextRenderer
```python
class ImprovedTextRenderer:
    def create_speech_bubble(self, text: str, max_width: int, 
                           bg_color: tuple = (0, 0, 0, 220),
                           border_color: tuple = (218, 165, 32, 255),
                           padding: int = 15,
                           corner_radius: int = 15,
                           add_tail: bool = True,
                           tail_side: str = "left") -> Image.Image
```

##### VoiceFrameVideoGenerator
```python
class VoiceFrameVideoGenerator:
    def generate_video_with_dialogues(self, scene_data: Dict, 
                                    character_positions: Optional[Dict] = None,
                                    font_size: int = 20, 
                                    font_color: str = 'gold') -> bool
```

- **Speech Bubble Features**:
  - Rounded corners with customizable radius
  - Speech bubble tails pointing to characters
  - Dynamic text wrapping and sizing
  - Gradient backgrounds and borders
  - Character-specific positioning (left/right sides)

- **Audio Synchronization**:
  - Automatic audio speed adjustment for timing
  - Formula: `speed_factor = (actual_duration / expected_duration) + 0.05`
  - Preserves all dialogue content while fitting time slots
  - Saves modified audio back to original files

#### 6. Speech Bubble Configurations
```python
SPEECH_BUBBLE_CONFIGS = {
    "modern_bubbles": {
        "font_size": 20,
        "font_color": "gold",
        "padding": 15,
        "corner_radius": 20,
        "character_positions": {
            "Character1": {"side": "left", "max_width": 450, "tail_side": "left"},
            "Character2": {"side": "right", "max_width": 450, "tail_side": "right"}
        }
    }
}
```
---
---
## Technical Implementation Details

### WebSocket Progress System
- **Purpose**: Real-time progress updates during video generation
- **Flow**: Frontend connects → Backend sends status updates → Frontend updates UI
- **Error Handling**: Connection drops handled gracefully with reconnection
- **Thread Safety**: Uses `ThreadPoolExecutor` with proper synchronization

### Audio Processing Pipeline
1. **Voice Synthesis**: Generate WAV files from dialogue text
2. **Duration Analysis**: Compare actual vs expected audio length
3. **Speed Adjustment**: Automatically speed up audio that's too long
4. **File Replacement**: Save adjusted audio back to original files
5. **Video Sync**: Use processed audio in final video assembly

### Video Assembly Process
1. **Background Loading**: Load generated scene image
2. **Speech Bubble Creation**: Generate text overlays with PIL
3. **Audio Synchronization**: Align audio files with dialogue timing
4. **Clip Composition**: Combine all elements using MoviePy
5. **Export**: Render final MP4 with H.264/AAC encoding

### Visual Effects System
- **Gradient Borders**: 3-layer gradient system for smooth bleed effects
- **Status Icons**: Dynamic color-coded progress indicators
- **Speech Bubbles**: Custom-drawn rounded rectangles with tails
- **Fade Transitions**: Smooth fade in/out for dialogue overlays



### Dependencies
- **Frontend**: React Native, Expo SDK, TypeScript
- **Backend**: FastAPI, MoviePy, PIL, Google Gemini API, InvokeAI
- **AI Services**: Gemini API key, local InvokeAI installation

## API Endpoints

### WebSocket
- `GET /ws/progress` - Real-time progress updates

### HTTP
- `GET /` - Health check endpoint
- `GET /video/{video_id}` - Stream generated video

## Error Handling Strategy
- **WebSocket**: Graceful disconnection handling with reconnection
- **AI Services**: Fallback mechanisms for service failures
- **File Operations**: Proper cleanup of temporary files
- **Video Generation**: Fallback to simple video if dialogue sync fails

## Performance Optimizations
- **Threading**: Non-blocking AI operations using thread pools
- **Audio Processing**: In-memory audio speed adjustment
- **Video Streaming**: Chunked video delivery for faster loading
- **Resource Management**: Proper cleanup of MoviePy clips and resources

## Security Considerations
- **CORS**: Configured for development (should be restricted in production)
- **File Access**: Controlled access to generated media files
- **API Keys**: Environment variable configuration for sensitive data
- **Input Validation**: Proper validation of user prompts and WebSocket messages
