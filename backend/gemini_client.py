import json
from typing import Any, Dict
from google import genai
from google.genai import types
from enum import Enum

class CharacterGender(Enum):
    MALE = "male"
    FEMALE = "female"

class GeminiClient:
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model_name

    def ask(self, prompt: str, temperature: float = 0.2) -> Dict[str, Any]:
        """
        Send a text prompt to Gemini and return structured JSON response.
        """
        try:
            # Modify the prompt to optimize for stable diffusion image generation
            prompt = "Create a scene with characters optimized for stable diffusion image generation. Remember that the it is supposed to cartoon style, so don't ask for realism. " + prompt

            generate_content_config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_budget=0,
                ),
                response_mime_type="application/json",
                response_schema=genai.types.Schema(
                    type=genai.types.Type.OBJECT,
                    required=["scene"],
                    properties={
                        "scene": genai.types.Schema(
                            type=genai.types.Type.OBJECT,
                            description="A single scene with background, characters, and dialogues",
                            required=["background", "characters", "dialogues"],
                            properties={
                                "background": genai.types.Schema(
                                    type=genai.types.Type.OBJECT,
                                    description="Background description and timing for the scene",
                                    required=["description", "start", "end"],
                                    properties={
                                        "description": genai.types.Schema(
                                            type=genai.types.Type.STRING,
                                            description="Description of the background",
                                        ),
                                        "start": genai.types.Schema(
                                            type=genai.types.Type.STRING,
                                            description="Start timestamp of the background (HH:MM:SS)",
                                        ),
                                        "end": genai.types.Schema(
                                            type=genai.types.Type.STRING,
                                            description="End timestamp of the background (HH:MM:SS)",
                                        ),
                                    },
                                ),
                                "characters": genai.types.Schema(
                                    type=genai.types.Type.ARRAY,
                                    description="List of characters present in the scene with consistent appearances",
                                    items=genai.types.Schema(
                                        type=genai.types.Type.OBJECT,
                                        required=["name", "appearance", "gender"],
                                        properties={
                                            "name": genai.types.Schema(
                                                type=genai.types.Type.STRING,
                                                description="Character's name",
                                            ),
                                            "appearance": genai.types.Schema(
                                                type=genai.types.Type.STRING,
                                                description="Description of the character's appearance (color, outfit, style, etc.)",
                                            ),
                                            "gender": genai.types.Schema(
                                                type=genai.types.Type.STRING,
                                                description="Character's gender",
                                                enum=[gender.value for gender in CharacterGender],
                                            ),
                                        },
                                    ),
                                ),
                                "dialogues": genai.types.Schema(
                                    type=genai.types.Type.ARRAY,
                                    description="Dialogues happening during this scene",
                                    items=genai.types.Schema(
                                        type=genai.types.Type.OBJECT,
                                        required=["character", "start", "end", "line"],
                                        properties={
                                            "character": genai.types.Schema(
                                                type=genai.types.Type.STRING,
                                                description="Name of the character speaking",
                                            ),
                                            "start": genai.types.Schema(
                                                type=genai.types.Type.STRING,
                                                description="Start timestamp of this dialogue (HH:MM:SS)",
                                            ),
                                            "end": genai.types.Schema(
                                                type=genai.types.Type.STRING,
                                                description="End timestamp of this dialogue (HH:MM:SS)",
                                            ),
                                            "line": genai.types.Schema(
                                                type=genai.types.Type.STRING,
                                                description="Text of the dialogue",
                                            ),
                                        },
                                    ),
                                ),
                            },
                        ),
                    },
                ),
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=generate_content_config,
            )

            # The response is already structured JSON, so we can directly parse it
            if response.text:
                return json.loads(response.text)
            else:
                return {
                    "error": "No response text received",
                    "raw_output": None
                }

        except Exception as e:
            return {
                "error": f"Failed to generate content: {str(e)}",
                "raw_output": None
            }