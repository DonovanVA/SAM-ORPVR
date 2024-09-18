import os
import cv2
from shutil import copy
import json
from tqdm import tqdm
from glob import glob
import numpy as np

import torch

from mmdet.apis import inference_detector,init_detector

from util.option_masking import args,compute_intersect_area

target = 0
subtarget = [24,26,28,67]
subtarget=[]
def segmentation(args,model):
    fname = os.path.splitext(os.path.basename(args.imgpath))[0]
    result = inference_detector(model,args.imgpath)
    mask = np.zeros((args.h,args.w),dtype=np.uint8)
    objects = {'box':[],'coor':[]}

    for k in range(len(result.pred_instances.bboxes)):
        # -------- masking person object --------
        score = result.pred_instances.bboxes[k][-1]
        if score < args.score_thr:                                               # if the score is less than score threshold, ignore this objects.
            continue
        coor = set()                                                             # counting the pixel of objects
        c1,r1,c2,r2 = map(int,result.pred_instances.bboxes[k][:])
        pred = result.pred_instances.masks[k]
        for i in range(r1,r2):
            for j in range(c1,c2):
                if pred[i][j]:
                    coor.add((i,j))
        if len(coor) / args.size < args.area_thr:                                     # if the area of person is less than area threshold, ignore this objects.
            continue
        
        # -------- masking subcategory object --------
        x1,y1,x2,y2 = c1,r1,c2,r2
        for subidx in subtarget:
            # Iterate over the bounding boxes for this subcategory (subidx)
            for l in range(len(result.pred_instances.bboxes)):
                # Check if the label corresponds to one of the subtarget categories
                if result.pred_instances.labels[l].item() != subidx:
                    continue
                
                # Get the confidence score for this instance
                score = result.pred_instances.scores[l].item()
                if score < args.score_thr:  # Ignore objects with scores less than threshold
                    continue
                
                # Extract the bounding box coordinates for the instance
                nc1, nr1, nc2, nr2 = map(int, result.pred_instances.bboxes[l].tolist())
                
                # Extract the predicted mask for the instance
                pred = result.pred_instances.masks[l].cpu().numpy()  # Convert mask to numpy if needed
                
                # Calculate the intersection area with the main object box
                interarea = compute_intersect_area([c1, r1, c2, r2], [nc1, nr1, nc2, nr2])
                
                # Calculate the size of the subcategory's bounding box
                nsize = (nr2 - nr1) * (nc2 - nc1)
                
                # Check if overlap is greater than 30%
                if interarea / nsize > 0.3:
                    # Update the bounding box for the subtarget by finding min/max of coordinates
                    x1, y1, x2, y2 = min(x1, nc1), min(y1, nr1), max(x2, nc2), max(y2, nr2)
                    
                    # Mask the region by iterating over the subcategory's mask
                    for i in range(nr1, nr2):
                        for j in range(nc1, nc2):
                            if pred[i][j]:  # If the mask value is True, add the coordinates
                                coor.add((i, j))

        
        for i,j in coor:
            mask[i][j] = 255
        
        objects['box'].append([x1,y1,x2,y2])
        objects['coor'].append(sorted(list(coor)))

    # cv2.imwrite(os.path.join(args.imgdir,args.fname+'.'+args.ext), img)
    copy(args.imgpath,os.path.join(args.imgdir,fname+'.'+args.ext))
    cv2.imwrite(os.path.join(args.maskdir,fname+'.png'), mask)
    with open(os.path.join(args.objdir,fname+'.json'),"w") as f:
        json.dump(objects,f)

#if args.device == None:
    #args.device = 'cuda' if torch.cuda.is_available() else 'cpu'

args.config = 'mmdetection\mask2former_swin-s-p4-w7-224_8xb2-lsj-50e_coco.py'
args.checkpoint = 'mmdetection\mask2former_swin-s-p4-w7-224_8xb2-lsj-50e_coco_20220504_001756-c9d0c4f2.pth'
model_m2f = init_detector(args.config, args.checkpoint, device='cpu')

datadir = args.dstdir

if os.path.isdir(args.src):
    clip = os.path.basename(args.src)
    args.imgdir = os.path.join(datadir,clip,'images')
    args.maskdir = os.path.join(datadir,clip,'masks')
    args.objdir = os.path.join(datadir,clip,'objects')
    os.makedirs(args.imgdir,exist_ok=True)
    os.makedirs(args.maskdir,exist_ok=True)
    os.makedirs(args.objdir,exist_ok=True)
    
    img_list = []
    for ext in ['*.jpg', '*.png']: 
        img_list.extend(glob(os.path.join(args.src, ext)))
    img_list.sort()
    args.ext = os.path.basename(img_list[0]).split('.')[-1]
    
    tempimg = cv2.imread(img_list[0])
    args.h,args.w,_ = tempimg.shape
    args.size = args.h*args.w

    for imgpath in tqdm(img_list):
        args.imgpath = imgpath
        segmentation(args, model_m2f)
else:
    print(f"Directory {args.src} not exists.")
    # args.img = args.src
    # args.imgdir = os.path.join(datadir,'single','images')
    # args.maskdir = os.path.join(datadir,'single','masks')
    # os.makedirs(args.imgdir,exist_ok=True)
    # os.makedirs(args.maskdir,exist_ok=True)
    # args.fname, args.ext = os.path.basename(args.img).split('.')
    # tempimg = cv2.imread(args.img,cv2.IMREAD_COLOR)
    # args.h,args.w,_ = tempimg.shape
    # segmentation(args, model_m2f)