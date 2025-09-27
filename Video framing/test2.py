"""
Test script for the Dynamic Video Generator
Shows how to use dynamic audio-based timing for dialogue rendering
with support for top/bottom positioning of dialogue boxes
"""

import os
from framing import VideoGenerator  # Original generator
from framing_dynamic import DynamicVideoGenerator, create_dynamic_video_with_audio, HybridVideoGenerator


def test_dynamic_video_generation():
    """Test the dynamic video generation with audio-based timing"""
    print("=== Testing Dynamic Video Generation ===")

    generator = DynamicVideoGenerator()

    background_image = "background_image.jpg"
    scene_data_file = "scene_data.json"
    audio_directory = "output_audio"
    output_video = "output/dynamic_video.mp4"

    # Custom character positioning (side + vertical)
    custom_positions = {
        "Scorpion": {"side": "left", "vertical": "top", "max_width": 500},
        "Frog": {"side": "right", "vertical": "top", "max_width": 500}
    }

    success = generator.generate_video_dynamic(
        background_image_path=background_image,
        scene_data_path=scene_data_file,
        output_path=output_video,
        audio_dir=audio_directory,
        character_positions=custom_positions,
        font_size=22,
        font_color='gold',
        gap_between_dialogues=0.8,
        start_delay=3.0,
        verbose=True
    )

    if success:
        print("✓ Dynamic video generated successfully!")
    else:
        print("✗ Dynamic video generation failed!")

    return success


def test_convenience_function():
    """Test the convenience function for dynamic video generation"""
    print("\n=== Testing Convenience Function ===")

    success = create_dynamic_video_with_audio(
        background_image_path="background_image.jpg",
        scene_data_json_path="scene_data.json",
        output_file="output/convenience_dynamic_video.mp4",
        character_positions={
            "Scorpion": {"side": "left", "vertical": "bottom", "max_width": 480},
            "Frog": {"side": "right", "vertical": "bottom", "max_width": 480}
        },
        font_size=20,
        font_color='white',
        audio_dir="output_audio",
        gap_between_dialogues=0.5,
        verbose=True
    )

    if success:
        print("✓ Convenience function video generated successfully!")
    else:
        print("✗ Convenience function video generation failed!")

    return success


def test_hybrid_generator():
    """Test the hybrid generator that can switch between dynamic and static timing"""
    print("\n=== Testing Hybrid Generator ===")

    hybrid_gen = HybridVideoGenerator()

    print("Testing hybrid generator with dynamic timing...")
    success1 = hybrid_gen.generate_video_hybrid(
        background_image_path="background_image.jpg",
        scene_data_path="scene_data.json",
        output_path="output/hybrid_dynamic.mp4",
        audio_dir="output_audio",
        use_dynamic_timing=True,
        gap_between_dialogues=0.6,
        verbose=True
    )

    print("\nTesting hybrid generator with static timing...")
    success2 = hybrid_gen.generate_video_hybrid(
        background_image_path="background_image.jpg",
        scene_data_path="scene_data.json",
        output_path="output/hybrid_static.mp4",
        audio_dir="output_audio",
        use_dynamic_timing=False,
        verbose=True
    )

    if success1 and success2:
        print("✓ Both hybrid tests completed successfully!")
    else:
        print(f"✗ Hybrid tests completed with issues (Dynamic: {success1}, Static: {success2})")

    return success1 and success2


def compare_timing_methods():
    """Compare original static timing vs new dynamic timing"""
    print("\n=== Comparing Timing Methods ===")

    original_gen = VideoGenerator()
    print("Generating video with original static timing...")
    success1 = original_gen.generate_video(
        background_image_path="background_image.jpg",
        scene_data_path="scene_data.json",
        output_path="output/original_static.mp4",
        audio_dir="output_audio",
        verbose=True
    )

    dynamic_gen = DynamicVideoGenerator()
    print("\nGenerating video with dynamic audio-based timing...")
    success2 = dynamic_gen.generate_video_dynamic(
        background_image_path="background_image.jpg",
        scene_data_path="scene_data.json",
        output_path="output/new_dynamic.mp4",
        audio_dir="output_audio",
        gap_between_dialogues=0.5,
        verbose=True
    )

    print("\n--- Comparison Results ---")
    print(f"Static timing (original): {'✓ Success' if success1 else '✗ Failed'}")
    print(f"Dynamic timing (new): {'✓ Success' if success2 else '✗ Failed'}")

    return success1 and success2


def batch_process_with_dynamic_timing():
    """Example of batch processing with dynamic timing"""
    print("\n=== Batch Processing with Dynamic Timing ===")

    generator = DynamicVideoGenerator()

    video_configs = [
        {
            "background": "backgrounds/scene1.jpg",
            "scene_data": "data/scene1.json",
            "audio_dir": "audio/scene1",
            "output": "output/scene1_dynamic.mp4",
            "gap": 0.5
        },
        {
            "background": "backgrounds/scene2.jpg",
            "scene_data": "data/scene2.json",
            "audio_dir": "audio/scene2",
            "output": "output/scene2_dynamic.mp4",
            "gap": 0.8
        }
    ]

    successful_videos = 0
    for i, config in enumerate(video_configs, 1):
        print(f"\nProcessing video {i}/{len(video_configs)}...")
        success = generator.generate_video_dynamic(
            background_image_path=config["background"],
            scene_data_path=config["scene_data"],
            output_path=config["output"],
            audio_dir=config["audio_dir"],
            gap_between_dialogues=config["gap"],
            verbose=True
        )
        if success:
            print(f"✓ Video {i} completed: {config['output']}")
            successful_videos += 1
        else:
            print(f"✗ Video {i} failed!")

    print(f"\nBatch processing complete: {successful_videos}/{len(video_configs)} videos successful")
    return successful_videos == len(video_configs)


def main():
    print("Dynamic Video Generator Test Suite")
    print("=" * 50)

    os.makedirs("output", exist_ok=True)

    test_results = []
    test_results.append(("Dynamic Generation", test_dynamic_video_generation()))
    test_results.append(("Convenience Function", test_convenience_function()))
    test_results.append(("Hybrid Generator", test_hybrid_generator()))
    test_results.append(("Timing Comparison", compare_timing_methods()))

    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    for test_name, result in test_results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")

    total_passed = sum(1 for _, result in test_results if result)
    print(f"\nTotal: {total_passed}/{len(test_results)} tests passed")

    if total_passed == len(test_results):
        print("\nRunning batch processing test...")
        batch_success = batch_process_with_dynamic_timing()
        if batch_success:
            print("✓ All tests completed successfully!")
        else:
            print("✗ Batch processing had issues")


if __name__ == "__main__":
    main()
