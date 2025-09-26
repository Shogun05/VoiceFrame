import os
import json
import wave
import random
from pathlib import Path
from piper import PiperVoice, SynthesisConfig

class VoiceSynthesizer:
    def __init__(self, voice_dir: str, output_dir: str, use_cuda: bool = False,
                 syn_config: SynthesisConfig = None):
        self.voice_dir = voice_dir
        self.output_dir = output_dir
        self.use_cuda = use_cuda
        self.syn_config = syn_config or SynthesisConfig(
            volume=1.0,
            length_scale=1.0,
            noise_scale=0.6,
            noise_w_scale=0.6,
            normalize_audio=True
        )
        Path(self.output_dir).mkdir(exist_ok=True, parents=True)
        self.voices = {}  # character name -> PiperVoice cache

    def _select_random_voice(self, gender: str) -> str:
        """Pick a random .onnx voice from voices/{gender}"""
        # normalize gender to either 'male' or 'female'
        g = (gender or "").strip().lower()
        if g.startswith("f"):
            preferred = ["female", "male"]
        else:
            preferred = ["male", "female"]

        # try preferred folders in order and return first available voice
        for p in preferred:
            gender_folder = os.path.join(self.voice_dir, p)
            if not os.path.exists(gender_folder):
                continue

            candidates = [f for f in os.listdir(gender_folder) if f.endswith(".onnx")]
            if candidates:
                chosen = random.choice(candidates)
                return os.path.join(gender_folder, chosen)

        # nothing found in either folder
        raise FileNotFoundError(
            f"No voice .onnx files found in any gender folders under {self.voice_dir} (tried: {preferred})"
        )

    def _get_voice_for_character(self, char_name: str, gender: str) -> PiperVoice:
        """Return cached voice if available; otherwise pick a random one and cache it."""
        if char_name in self.voices:
            return self.voices[char_name]

        voice_file = self._select_random_voice(gender)
        voice = PiperVoice.load(voice_file, use_cuda=self.use_cuda)
        self.voices[char_name] = voice
        print(f"Selected {os.path.basename(voice_file)} for {char_name} ({gender})")
        return voice

    def synthesize_dialogues(self, dialogues: list, characters: list):
        """
        Generate WAV files for each dialogue line.
        Uses the character gender to select voice from voices/{gender}.
        Caches one voice per character.
        """
        # Build mapping: normalized character name (lowercase, stripped) -> normalized gender
        char_gender_map = {}
        for c in characters:
            name = c.get("name")
            if not name:
                continue
            key = name.strip().lower()
            gen = str(c.get("gender", "")).strip().lower()
            # normalize values like 'F', 'female', 'Female' etc.
            if gen.startswith("f"):
                char_gender_map[key] = "female"
            else:
                # default to male for any unknown/missing value
                char_gender_map[key] = "male"

        # show a concise mapping of characters to genders
        print(f"character genders: {char_gender_map}")

        for i, dlg in enumerate(dialogues):
            char_raw = dlg.get("character")
            line = dlg.get("line", "")
            start = dlg.get("start", "").replace(":", "-")
            end = dlg.get("end", "").replace(":", "-")

            if not char_raw or not line:
                print(f"[WARN] Skipping dialogue {i} (missing character or line)")
                continue

            canonical_name = char_raw.strip()
            cache_key = canonical_name.lower()
            gender = char_gender_map.get(cache_key, "male")  # default male if missing
            voice = self._get_voice_for_character(cache_key, gender)

            out_file = os.path.join(self.output_dir, f"{i:03d}_{canonical_name}_{start}_{end}.wav")
            print(f"Generating audio for {canonical_name} ({line})")

            with wave.open(out_file, "wb") as wav_file:
                voice.synthesize_wav(line, wav_file, self.syn_config)
