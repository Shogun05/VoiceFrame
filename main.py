from voice_generation import VoiceSynthesizer

if __name__ == "__main__":
    vs = VoiceSynthesizer(
        voice_dir="./voices",       
        output_dir="./output_audio",
        use_cuda=False
    )


