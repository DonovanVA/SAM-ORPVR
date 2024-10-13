import cv2
import torch
from segment_anything import SamAutomaticMaskGenerator, sam_model_registry
import supervision as sv
import numpy as np
DEVICE = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
MODEL_TYPE = "vit_h"
SAM_MODEL_CHECKPOINT='SAM/checkpoints/sam_vit_h_4b8939.pth'
sam = sam_model_registry[MODEL_TYPE](checkpoint=SAM_MODEL_CHECKPOINT).to(device=DEVICE)
mask_generator = SamAutomaticMaskGenerator(sam)
image_bgr = cv2.imread('DAVIS-test/JPEGImages/480p/bmx-bumps/00000.jpg')
image_rgb = cv2.cvtColor(image_bgr,cv2.COLOR_BGR2RGB)
sam_result = mask_generator.generate(image_bgr)

print(sam_result[0].keys())
mask_annotator = sv.MaskAnnotator(color_lookup=sv.ColorLookup.INDEX)

detections = sv.Detections.from_sam(sam_result=sam_result)

annotated_image = mask_annotator.annotate(scene=image_bgr.copy(), detections=detections)

## show coloured images
sv.plot_images_grid(
    images=[image_bgr, annotated_image],
    grid_size=(1, 2),
    titles=['source image', 'segmented image']
)

masks = [
    mask['segmentation']
    for mask
    in sorted(sam_result, key=lambda x: x['area'], reverse=True)
]
## show binary masks
sv.plot_images_grid(
    images=masks[:10],
    grid_size=(8,8),
    size=(20, 20)
)


## plan:
## 1.generate masks
## filter those that have big area? same area as prev
## generate masks for the next=

