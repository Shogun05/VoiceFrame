VoiceFrame — quick start

This repository produces short voice clips from text using Piper-compatible ONNX voice models.

Follow the steps below (PowerShell examples) to install dependencies, create a voice folder for your preferred language, download both the `*.onnx` and `*.onnx.json` files from the Rhasspy Piper voices repository on Hugging Face, and run `main.py`.

## 1) Prerequisites

- Python 3.8+ (the project contains a `__pycache__` from Python 3.11 but 3.8+ should work).
- Git (optional, for cloning or inspecting the Hugging Face repo).

## 2) Install Python requirements

Run these PowerShell commands from the repository root (`d:\CODING\prism\VoiceFrame`):

```powershell
# upgrade pip (optional but recommended)
python -m pip install --upgrade pip

# install requirements from the included file
python -m pip install -r .\requirements.txt
```

If you don't have a `requirements.txt`, install the packages you need (for example `onnxruntime` or whatever the project requires). The included `requirements.txt` should list them.

## 3) Create a voices directory for your preferred language

The code expects voice models in a `voices` directory. Create a folder for the language/voice you want (for example `en` or `ar`).

## 4) Download both `.onnx` and `.onnx.json` files from the Hugging Face piper-voices repo

Open the web page with available voices:

https://huggingface.co/rhasspy/piper-voices/tree/main

Find the specific voice folder you want and copy the raw download links for the `.onnx` and `.onnx.json` files. Hugging Face raw file URLs follow this pattern:

```
https://huggingface.co/rhasspy/piper-voices/resolve/main/<voice-folder>/<file>
```


## 5) Run the app

Once the voice model files are in `voices/` run:

```powershell
python .\main.py
```
