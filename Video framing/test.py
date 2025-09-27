"""
Main file example showing how to use the video_generator module
"""

# Import the video generator module
from framing import VideoGenerator, create_video_with_audio

def main():
    # Option 1: Using the VideoGenerator class
    print("Creating video using VideoGenerator class...")
    
    # Initialize the generator
    generator = VideoGenerator()
    
    # Configure paths
    background_image = "background_image.jpg"
    scene_data_file = "scene_data.json"
    audio_directory = "output_audio"
    output_video = "output/generated_video.mp4"
    
    # Optional: Custom character positioning
    custom_positions = {
        "Scorpion": {"side": "left", "max_width": 500},
        "Frog": {"side": "right", "max_width": 500}
    }
    
    # Generate the video
    success = generator.generate_video(
        background_image_path=background_image,
        scene_data_path=scene_data_file,
        output_path=output_video,
        audio_dir=audio_directory,
        character_positions=custom_positions,
        font_size=22,
        font_color='gold',
        verbose=True
    )
    
    if success:
        print("Video generated successfully!")
    else:
        print("Video generation failed!")
    
    print("-" * 50)
    
    # Option 2: Using the convenience function
    print("Creating video using convenience function...")
    
    success2 = create_video_with_audio(
        background_image_path=background_image,
        scene_data_json_path=scene_data_file,
        output_file="output/generated_video_2.mp4",
        character_positions=custom_positions,
        font_size=20,
        font_color='white',
        audio_dir=audio_directory,
        verbose=True
    )
    
    if success2:
        print("Second video generated successfully!")
    else:
        print("Second video generation failed!")


def batch_process_videos():
    """Example of processing multiple videos"""
    generator = VideoGenerator()
    
    # List of videos to process
    video_configs = [
        {
            "background": "backgrounds/scene1.jpg",
            "scene_data": "data/scene1.json",
            "audio_dir": "audio/scene1",
            "output": "output/scene1_video.mp4"
        },
        {
            "background": "backgrounds/scene2.jpg",
            "scene_data": "data/scene2.json",
            "audio_dir": "audio/scene2",
            "output": "output/scene2_video.mp4"
        }
    ]
    
    for i, config in enumerate(video_configs, 1):
        print(f"Processing video {i}/{len(video_configs)}...")
        
        success = generator.generate_video(
            background_image_path=config["background"],
            scene_data_path=config["scene_data"],
            output_path=config["output"],
            audio_dir=config["audio_dir"],
            verbose=True
        )
        
        if success:
            print(f"✓ Video {i} completed: {config['output']}")
        else:
            print(f"✗ Video {i} failed!")


if __name__ == "__main__":
    main()
    
    # Uncomment to run batch processing
    # batch_process_videos()