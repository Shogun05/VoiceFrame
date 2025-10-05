import json
from typing import Any, Dict
from google import genai
from google.genai import types
from enum import Enum

class CharacterGender(Enum):
    MALE = "male"
    FEMALE = "female"

class GeminiClient:
    def __init__(self, api_key: str, model_name: str = "gemini-flash-latest"):
        self.client = genai.Client(api_key=api_key)
        self.model = model_name

    def ask(self, prompt: str, temperature: float = 0.2) -> Dict[str, Any]:
        """
        Send a text prompt to Gemini and return structured JSON response.
        """
        try:
            # System context for better story generation
            system_context = """
You are an expert children's story creator specializing in cartoon-style narratives. 

KEY REQUIREMENTS:
- Generate 8-12 dialogues per story
- Give character description to be as simplistic as possible. No adjectives or adverbs
- Use vivid, cartoon-style descriptions with bright colors and fun details
- Keep content appropriate for children (ages 4-10)
- Include natural conversation flow with emotional expressions
- Create engaging, positive stories with clear beginning, middle, and end
- Each dialogue should be 3-7 seconds long for natural pacing
- Characters (atmost 3) should interact meaningfully and learn something

STYLE EXAMPLES:
- Background: "A magical rainbow bridge spanning across fluffy white clouds, with golden stars twinkling in a lavender sky and cotton candy trees swaying gently"
- Character: "one, yellow cat, blue striped scarf, green eyes, wearing red boots, silver bell collar"
- Dialogue: No emotions in brackets. Just the line.
(Note: Keep the character prompts no nonsense, like no adjectives just the description of the objects themselves as the above example. Use just basic emotions like happy, sad, angry)

STORY STRUCTURE GUIDELINES:
1. Setting introduction with rich visual details
2. Character introductions with distinct appearances and personalities
3. Problem or interesting situation that brings characters together
4. Character interactions showing friendship, problem-solving, or learning
5. Positive, uplifting resolution with a gentle lesson or happy ending

DIALOGUE QUALITY:
- Avoid repetitive phrases - keep conversations fresh and engaging

Remember: Every story should be uplifting, educational, and spark imagination while maintaining cartoon-style whimsy!
"""

            # Enhanced prompt with system context
            enhanced_prompt = f"{system_context}\n\nCreate a detailed cartoon story about: {prompt}"

            generate_content_config = types.GenerateContentConfig(
                response_mime_type="application/json",
                max_output_tokens=8192,
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
                contents=enhanced_prompt,
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