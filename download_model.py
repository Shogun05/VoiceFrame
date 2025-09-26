# Create a simple Python script to download the model
# Save this as download_model.py
from huggingface_hub import hf_hub_download
import os

# Create models directory if it doesn't exist
os.makedirs("models/AnimeInstanceSegmentation", exist_ok=True)

# Download the checkpoint file
hf_hub_download(
    repo_id="dreMaz/AnimeInstanceSegmentation",
    filename="rtmdetl_e60.ckpt",
    local_dir="models/AnimeInstanceSegmentation"
)

print("Model downloaded successfully!")
