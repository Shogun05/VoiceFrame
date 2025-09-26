import gradio as gr
import os

# Set environment variables to force CPU usage
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['FORCE_CUDA'] = '0'

# Remove or comment out these problematic installation commands
# os.system("mim install mmengine")
# os.system('mim install "mmcv==2.1.0"')
# os.system("mim install mmdet")

# Instead, ensure packages are installed manually or handle import errors
try:
    import cv2
    from PIL import Image
    import numpy as np
    from animeinsseg import AnimeInsSeg, AnimeInstances
    from animeinsseg.anime_instances import get_color
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please install required packages manually:")
    print("pip install mmcv==2.1.0 -f https://download.openmmlab.com/mmcv/dist/cpu/torch2.0/index.html")
    print("pip install mmengine mmdet")
    exit(1)

if not os.path.exists("models"):
    os.mkdir("models")

# Only clone if directory doesn't exist to avoid repeated downloads
if not os.path.exists("models/AnimeInstanceSegmentation"):
    os.system("huggingface-cli lfs-enable-largefiles .")
    os.system("git clone https://huggingface.co/dreMaz/AnimeInstanceSegmentation models/AnimeInstanceSegmentation")

ckpt = r'models/AnimeInstanceSegmentation/rtmdetl_e60.ckpt'

mask_thres = 0.3
instance_thres = 0.3
# refine_kwargs = {'refine_method': 'refinenet_isnet'} # set to None if not using refinenet
refine_kwargs = None

# Force CPU device
net = AnimeInsSeg(ckpt, mask_thr=mask_thres, refine_kwargs=refine_kwargs, device='cpu')

def fn(image):
    img = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    instances: AnimeInstances = net.infer(
        img,
        output_type='numpy',
        pred_score_thr=instance_thres
    )

    drawed = img.copy()
    im_h, im_w = img.shape[:2]

    if instances.bboxes is None or len(instances) == 0:
        return Image.fromarray(drawed[..., ::-1])

    # Create folder for individual characters
    input_name = "images/img1"  # or extract from filename
    if not os.path.exists(input_name):
        os.makedirs(input_name)

    for i in range(len(instances)):
        instance = instances.get_instance(i, out_type='numpy')
        mask = instance['mask']
        bbox = instance['bbox']
        tag = instance['character_tags'] or f"char_{i}"

        # Crop character using bbox
        x, y, w, h = bbox
        char_img = img[y:y+h, x:x+w]
        char_mask = mask[y:y+h, x:x+w]
        char_img_masked = char_img * char_mask[..., None]

        # Save masked character
        out_path = os.path.join(input_name, f"{i}_{tag}.png")
        cv2.imwrite(out_path, char_img_masked)

        # Optional: draw on main image for visualization
        color = get_color(i)
        p1, p2 = (int(x), int(y)), (int(x+w), int(y+h))
        cv2.rectangle(drawed, p1, p2, color, thickness=2)
        alpha_msk = 0.5
        blend_mask = np.full((im_h, im_w, 3), color, dtype=np.float32)
        alpha_ori = 1 - (alpha_msk * mask)[..., None]
        drawed = drawed * alpha_ori + (alpha_msk * mask)[..., None] * blend_mask
        drawed = drawed.astype(np.uint8)

    return Image.fromarray(drawed[..., ::-1])

iface = gr.Interface(
    # design titles and text descriptions
    title="Anime Subject Instance Segmentation",
    description="Segment image subjects with the proposed model in the paper [*Instance-guided Cartoon Editing with a Large-scale Dataset*](https://cartoonsegmentation.github.io/).",
    fn=fn,
    inputs=gr.Image(type="numpy"),
    outputs=gr.Image(type="pil"),
    examples=["1562990.jpg", "612989.jpg", "sample_3.jpg"]
)

if __name__ == "__main__":
    iface.launch()