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

## 3) Download both `.onnx` and `.onnx.json` files from the zip file

Download a pre-packaged ZIP of the `voices/` folder from Google Drive (contains `.onnx` and `.onnx.json` files):

https://drive.google.com/file/d/1k22GJTXCtRCsQs_r-iiVic8vuMiw0bRI/view?usp=drive_link

Save the ZIP and extract its contents into the repository `voices/` folder.

## 4) Run the app

Once the voice model files are in `voices/` run:

```powershell
python .\main.py
```
