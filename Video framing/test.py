import os
from moviepy.editor import AudioFileClip, CompositeAudioClip, VideoFileClip

def test_audio_files():
    """Test if we can actually load and process your audio files"""
    audio_dir = "output_audio"
    
    print("=== AUDIO FILES TEST ===")
    
    if not os.path.exists(audio_dir):
        print(f"✗ Audio directory {audio_dir} not found")
        return False
    
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]
    print(f"Found {len(audio_files)} audio files")
    
    test_clips = []
    
    for i, audio_file in enumerate(audio_files[:3]):  # Test first 3 files
        file_path = os.path.join(audio_dir, audio_file)
        try:
            print(f"\nTesting: {audio_file}")
            clip = AudioFileClip(file_path)
            print(f"  ✓ Duration: {clip.duration:.2f}s")
            print(f"  ✓ Sample rate: {clip.fps}Hz")
            print(f"  ✓ Channels: {clip.nchannels}")
            
            # Test setting start time
            clip_with_start = clip.set_start(i * 2)
            test_clips.append(clip_with_start)
            print(f"  ✓ Set start time: {i * 2}s")
            
        except Exception as e:
            print(f"  ✗ Error loading {audio_file}: {e}")
            return False
    
    # Test compositing multiple audio clips
    if test_clips:
        try:
            print(f"\nTesting audio composition with {len(test_clips)} clips...")
            composite = CompositeAudioClip(test_clips)
            print(f"  ✓ Composite duration: {composite.duration:.2f}s")
            
            # Clean up
            for clip in test_clips:
                clip.close()
            composite.close()
            
            print("✓ All audio tests passed!")
            return True
            
        except Exception as e:
            print(f"  ✗ Error compositing audio: {e}")
            return False
    
    return False

def test_simple_video_with_audio():
    """Create a simple test video with audio"""
    from moviepy.editor import ColorClip
    
    print("\n=== SIMPLE VIDEO + AUDIO TEST ===")
    
    try:
        # Create a simple 5-second red video
        video_clip = ColorClip(size=(640, 480), color=(255, 0, 0), duration=5)
        
        # Try to load first audio file
        audio_dir = "output_audio"
        audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]
        
        if audio_files:
            audio_path = os.path.join(audio_dir, audio_files[0])
            audio_clip = AudioFileClip(audio_path)
            
            # Trim audio to 5 seconds
            if audio_clip.duration > 5:
                audio_clip = audio_clip.subclip(0, 5)
            
            # Add audio to video
            final_clip = video_clip.set_audio(audio_clip)
            
            # Try to render
            test_output = "audio_test.mp4"
            print(f"Rendering test video: {test_output}")
            
            final_clip.write_videofile(
                test_output,
                fps=24,
                codec='libx264',
                audio_codec='aac',
                verbose=True,  # Enable verbose output
                logger='bar'   # Show progress bar
            )
            
            # Verify the result
            print(f"\nVerifying {test_output}...")
            test_video = VideoFileClip(test_output)
            
            if test_video.audio is not None:
                print(f"  ✓ Video has audio: {test_video.audio.duration:.2f}s")
                success = True
            else:
                print("  ✗ Video has no audio track")
                success = False
            
            # Clean up
            final_clip.close()
            test_video.close()
            
            return success
            
        else:
            print("✗ No audio files found for testing")
            return False
            
    except Exception as e:
        print(f"✗ Error in simple video test: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_existing_video():
    """Check if your existing video actually has audio"""
    print("\n=== CHECKING EXISTING VIDEO ===")
    
    video_file = "scorpion_frog_story.mp4"
    
    if not os.path.exists(video_file):
        print(f"✗ Video file {video_file} not found")
        return
    
    try:
        clip = VideoFileClip(video_file)
        print(f"Video duration: {clip.duration:.2f}s")
        print(f"Video size: {clip.size}")
        
        if clip.audio is not None:
            print(f"✓ Audio track found: {clip.audio.duration:.2f}s")
            print(f"  Sample rate: {clip.audio.fps}Hz")
            print(f"  Channels: {clip.audio.nchannels}")
        else:
            print("✗ No audio track found")
        
        clip.close()
        
    except Exception as e:
        print(f"Error checking video: {e}")

if __name__ == "__main__":
    # Run all tests
    audio_ok = test_audio_files()
    
    if audio_ok:
        simple_test_ok = test_simple_video_with_audio()
        
        if simple_test_ok:
            print("\n🎉 SUCCESS: Audio processing works!")
            print("The issue might be elsewhere in your main script.")
        else:
            print("\n❌ ISSUE: Simple audio test failed")
            print("There's a problem with audio encoding in MoviePy")
    
    # Check your existing video
    check_existing_video()
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print("If audio tests pass but your main video has no audio,")
    print("the issue is likely in the main script's rendering section.")