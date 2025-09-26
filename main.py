from voice_generation import synthesize_from_file, SynthesisConfig

dialogues_file = "dialogues.json"
voice_dir = "voices" # Directory containing .onnx voice files
output_dir = "output_audio"

# Flexible character-to-voice mapping
character_voices = {
    "Zafir": "en_US-john-medium.onnx",
    "Narrator": "en_US-hfc_male-medium.onnx",
    "King Darius": "en_US-arctic-medium.onnx",
    "Minister Aldric": "en_US-bryce-medium.onnx"
}

# Custom synthesis config
custom_config = SynthesisConfig(volume=0.9, length_scale=1.1,
                                noise_scale=0.5, noise_w_scale=0.5)

synthesize_from_file(
    dialogue_file=dialogues_file,
    character_voices=character_voices,
    voice_dir=voice_dir,
    output_dir=output_dir,
    syn_config=custom_config,
    use_cuda=False
)
