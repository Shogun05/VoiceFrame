import gradio as gr

import os

os.system("mim install mmengine")
os.system('mim install "mmcv>=2.0.0"')
os.system("mim install mmdet")

import cv2
from PIL import Image
import numpy as np

from animeinsseg import AnimeInsSeg, AnimeInstances
from animeinsseg.anime_instances import get_color



if not os.path.exists("models"):
    os.mkdir("models")

os.system("huggingface-cli lfs-enable-largefiles .")
os.system("git clone https://huggingface.co/dreMaz/AnimeInstanceSegmentation models/AnimeInstanceSegmentation")

ckpt = r'models/AnimeInstanceSegmentation/rtmdetl_e60.ckpt'

mask_thres = 0.3
instance_thres = 0.3
refine_kwargs = {'refine_method': 'refinenet_isnet'} # set to None if not using refinenet
# refine_kwargs = None

net = AnimeInsSeg(ckpt, mask_thr=mask_thres, refine_kwargs=refine_kwargs)

def fn(image):
    img = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    instances: AnimeInstances = net.infer(
        img,
        output_type='numpy',
        pred_score_thr=instance_thres
    )

    drawed = img.copy()
    im_h, im_w = img.shape[:2]

    # instances.bboxes, instances.masks will be None, None if no obj is detected

    for ii, (xywh, mask) in enumerate(zip(instances.bboxes, instances.masks)):
        color = get_color(ii)

        mask_alpha = 0.5
        linewidth = max(round(sum(img.shape) / 2 * 0.003), 2)

        # draw bbox
        p1, p2 = (int(xywh[0]), int(xywh[1])), (int(xywh[2] + xywh[0]), int(xywh[3] + xywh[1]))
        cv2.rectangle(drawed, p1, p2, color, thickness=linewidth, lineType=cv2.LINE_AA)
        
        # draw mask
        p = mask.astype(np.float32)
        blend_mask = np.full((im_h, im_w, 3), color, dtype=np.float32)
        alpha_msk = (mask_alpha * p)[..., None]
        alpha_ori = 1 - alpha_msk
        drawed = drawed * alpha_ori + alpha_msk * blend_mask

        drawed = drawed.astype(np.uint8)

    return Image.fromarray(drawed[..., ::-1])

iface = gr.Interface(
    # design titles and text descriptions
    title="Anime Subject Instance Segmentation",
    description="This is a demo of Anime Instance Segmentation with our proposed model in [AnimeInstanceSegmentation](https://cartoonsegmentation.github.io/)",
    fn=fn,
    inputs=gr.Image(type="numpy"),
    outputs=gr.Image(type="pil"),
    examples=["1562990.jpg", "612989.jpg"]
)

iface.launch()

