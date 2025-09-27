import os 
os.environ['IMAGEMAGICK_BINARY'] = r'D:\ImageMagick-7.1.2-Q16-HDRI\magick.exe' 
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip 
bg = ImageClip("background_image.jpg").set_duration(5) 
frame = ImageClip("ornate_frame.png").set_duration(5).resize(bg.size) 
txt = TextClip("Hello World", fontsize=50, color='gold', font='Arial', method='caption', size=(500, 100)) 
txt = txt.set_start(0).set_duration(5).set_pos((50, 50)) 
final = CompositeVideoClip([bg, frame, txt], size=bg.size) 
final.write_videofile("test_output.mp4", fps=24)