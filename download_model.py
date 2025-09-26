# Create a complete download script - save as download_all_models.py
from huggingface_hub import snapshot_download
import os

# Remove existing directory to start fresh
import shutil
if os.path.exists("models/AnimeInstanceSegmentation"):
    shutil.rmtree("models/AnimeInstanceSegmentation")

# Download all files from the repository
snapshot_download(
    repo_id="dreMaz/AnimeInstanceSegmentation", 
    local_dir="models/AnimeInstanceSegmentation",
    allow_patterns=["*.ckpt", "*.pt", "*.pth"]  # Only download model files
)

print("All models downloaded!")