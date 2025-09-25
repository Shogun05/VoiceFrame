import json
import re
from typing import Any, Dict, Optional
from google import genai
from google.genai import types


class GeminiClient:
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Tries to extract and parse JSON from Gemini output text.
        Returns a dict if successful, None otherwise.
        """
        # Look for a JSON block inside json ... 
        match = re.search(r"json\s*(\{.*?\})\s*", text, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            # fallback: try raw text
            json_str = text.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None

    def ask(self, prompt: str, temperature: float = 0.2) -> Dict[str, Any]:
        """
        Send a text prompt to Gemini and return parsed JSON response.
        Falls back to a dict with error info if parsing fails.
        """
        response = self.model.generate_content(
            contents=prompt,
            generation_config=types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=2048
            )
        )

        raw_text = response.candidates[0].content.parts[0].text
        parsed = self._extract_json(raw_text)

        if parsed is not None:
            return parsed
        else:
            return {
                "error": "Failed to parse JSON",
                "raw_output": raw_text
            }