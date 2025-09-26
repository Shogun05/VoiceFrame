import os
import json
import wave
from pathlib import Path
from piper import PiperVoice, SynthesisConfig

# -----------------------------
# FUNCTIONS
# -----------------------------
def ensure_dir(directory: str):
    """Ensure that a directory exists."""
    Path(directory).mkdir(exist_ok=True, parents=True)

def load_voices(character_voices: dict, voice_dir: str, use_cuda: bool = False):
    """
    Load Piper voices for each character dynamically.

    Args:
        character_voices: dict mapping character names to .onnx voice files
        voice_dir: folder where voice files are stored
        use_cuda: whether to use GPU
    """
    voices = {}
    for char, voice_file in character_voices.items():
        voice_path = os.path.join(voice_dir, voice_file)
        if not os.path.exists(voice_path):
            raise FileNotFoundError(f"Voice file not found: {voice_path}")
        voices[char] = PiperVoice.load(voice_path, use_cuda=use_cuda)
        print(f"[INFO] Loaded voice for {char} -> {voice_file}")
    return voices

def synthesize_dialogues(dialogues: list, voices: dict, output_dir: str,
                         syn_config: SynthesisConfig):
    """
    Generate WAV files for each dialogue line.

    Args:
        dialogues: list of dicts, each with keys: character, line, start, end
        voices: dict of loaded PiperVoice objects
        output_dir: folder to save WAV files
        syn_config: Piper SynthesisConfig
    """
    ensure_dir(output_dir)

    for i, dlg in enumerate(dialogues):
        char = dlg.get("character")
        line = dlg.get("line", "")
        start = dlg.get("start", "").replace(":", "-")
        end = dlg.get("end", "").replace(":", "-")

        if not char or not line:
            print(f"[WARN] Skipping dialogue index {i} (missing character or line)")
            continue
        if char not in voices:
            print(f"[WARN] No voice loaded for {char}, skipping")
            continue

        out_file = os.path.join(output_dir, f"{i:03d}_{char}_{start}_{end}.wav")
        print(f"[INFO] Generating audio for {char}: {line}")

        with wave.open(out_file, "wb") as wav_file:
            voices[char].synthesize_wav(line, wav_file, syn_config)

def synthesize_from_file(dialogue_file: str, character_voices: dict, voice_dir: str,
                         output_dir: str, syn_config: SynthesisConfig = None,
                         use_cuda: bool = False):
    """
    Load dialogues from JSON and synthesize audio for all lines dynamically.

    Args:
        dialogue_file: JSON file containing dialogues
        character_voices: dict mapping character names to voice files
        voice_dir: folder where voice files are stored
        output_dir: folder to save WAV files
        syn_config: Piper SynthesisConfig object (optional)
        use_cuda: whether to use GPU
    """
    if not os.path.exists(dialogue_file):
        raise FileNotFoundError(f"Dialogue file not found: {dialogue_file}")

    with open(dialogue_file, "r", encoding="utf-8") as f:
        dialogues = json.load(f)

    if syn_config is None:
        syn_config = SynthesisConfig(volume=1.0, length_scale=1.0,
                                     noise_scale=0.6, noise_w_scale=0.6,
                                     normalize_audio=True)

    voices = load_voices(character_voices, voice_dir, use_cuda)
    synthesize_dialogues(dialogues, voices, output_dir, syn_config)

    print(f"[ALL DONE] Audio saved in {output_dir}/")
