import os
import cv2
from shutil import copy
import json
from tqdm import tqdm
from glob import glob
import numpy as np
import argparse  # Import argparse for command line arguments
import torch

from mmdetection.mmdet.apis import inference_detector,init_detector

from util.option_masking import args,compute_intersect_area

target = 0
subtarget = [24,26,28,67]

def load_predefined_mask(mask_path):
    """Load a predefined mask image and return it as a binary mask."""
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise ValueError(f"Mask at {mask_path} could not be loaded.")
    return mask
def segmentation_with_predefined_mask(args):
    image_files = [f for f in os.listdir(args.src) if f.endswith(('.png', '.jpg', '.jpeg'))]
    if not image_files:
        raise ValueError(f"No image files found in directory: {args.src}")
    # Load the predefined mask
    for i in range(len(image_files)):
        predefined_mask_path = os.path.join(args.src, image_files[i])
    
        mask = load_predefined_mask(predefined_mask_path)

        objects = {'box': [], 'coor': []}
        
        # Create a binary mask from the predefined mask
        mask_binary = (mask > 0).astype(np.uint8)
        contours, _ = cv2.findContours(mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
     

        for contour in contours:
            # Get bounding box coordinates
            x, y, w, h = cv2.boundingRect(contour)
            objects['box'].append([int(x), int(y), int(x + w), int(y + h)])

            # Create a mask for the current contour and fill it to get internal pixels
            filled_contour_mask = np.zeros(mask_binary.shape, dtype=np.uint8)
            cv2.drawContours(filled_contour_mask, [contour], -1, 255, thickness=-1)  # Fill the contour
            
            # Get all non-zero points inside the filled contour (everything inside the contour)
            internal_points = np.column_stack(np.where(filled_contour_mask > 0))

            # Convert to [y, x] format
            internal_points = [[int(pt[0]), int(pt[1])] for pt in internal_points]
            objects['coor'].append(internal_points)

        # Sort the boxes and coordinates based on the top-left corner (y, x)
        sorted_indices = sorted(range(len(objects['box'])), key=lambda i: (objects['box'][i][1], objects['box'][i][0]))

        objects['box'] = [objects['box'][i] for i in sorted_indices]
        objects['coor'] = [objects['coor'][i] for i in sorted_indices]
        # Save the images and JSON file
        fname = os.path.splitext(os.path.basename(predefined_mask_path))[0]
        objects_path = os.path.join(os.path.dirname(args.src), 'objects')
        os.makedirs(objects_path, exist_ok=True)  # Ensure the directory exists
        with open(os.path.join(objects_path, fname + '.json'), "w") as f:
            json.dump(objects, f)
    

def segmentation_with_model(args,model):
    fname = os.path.splitext(os.path.basename(args.imgpath))[0]
    result = inference_detector(model,args.imgpath)

    mask = np.zeros((args.h,args.w),dtype=np.uint8)
    objects = {'box':[],'coor':[]}

    for k in range(len(result[0][target])):
        # -------- masking person object --------
        score = result[0][target][k][-1]
        if score < args.score_thr:                                               # if the score is less than score threshold, ignore this objects.
            continue
        coor = set()                                                             # counting the pixel of objects
        c1,r1,c2,r2 = map(int,result[0][target][k][:-1])
        pred = result[1][target][k]
        for i in range(r1,r2):
            for j in range(c1,c2):
                if pred[i][j]:
                    coor.add((i,j))
        if len(coor) / args.size < args.area_thr:                                     # if the area of person is less than area threshold, ignore this objects.
            continue
        
        # -------- masking subcategory object --------
        x1,y1,x2,y2 = c1,r1,c2,r2
        for subidx in subtarget:
            for l in range(len(result[0][subidx])):
                score = result[0][subidx][l][-1]
                if score < args.score_thr:                                       # if the score is less than score threshold, ignore this objects.
                    continue
                nc1,nr1,nc2,nr2 = map(int,result[0][subidx][l][:-1])
                pred = result[1][subidx][l]
                interarea = compute_intersect_area([c1,r1,c2,r2],[nc1,nr1,nc2,nr2])
                nsize = (nr2-nr1) * (nc2-nc1)
                if interarea / nsize > 0.3:                                      # masking the subcategory object if the subcategory box overlaps more than 30% of its depended main object box(person).
                    x1,y1,x2,y2 = min(x1,nc1), min(y1,nr1), max(x2,nc2), max(y2,nr2)
                    for i in range(nr1,nr2):
                        for j in range(nc1,nc2):
                            if pred[i][j]:
                                coor.add((i,j))
        
        for i,j in coor:
            mask[i][j] = 255
        
        objects['box'].append([x1,y1,x2,y2])
        objects['coor'].append(sorted(list(coor)))

    # cv2.imwrite(os.path.join(args.imgdir,args.fname+'.'+args.ext), img)
    copy(args.imgpath,os.path.join(args.imgdir,fname+'.'+args.ext))
    cv2.imwrite(os.path.join(args.maskdir,fname+'.png'), mask)
    with open(os.path.join(args.objdir,fname+'.json'),"w") as f:
        json.dump(objects,f)


if os.path.isdir(args.src):
    if(args.mode==1):
        segmentation_with_predefined_mask(args)
    else:
        if args.device == None:
            args.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        args.config = 'mmdetection/configs/mask2former/mask2former_swin-s-p4-w7-224_lsj_8x2_50e_coco.py'
        args.checkpoint = 'mmdetection/checkpoints/mask2former_swin-s-p4-w7-224_lsj_8x2_50e_coco_20220504_001756-743b7d99.pth'
        model_m2f = init_detector(args.config, args.checkpoint, device=args.device)

        datadir = args.dstdir                
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
            segmentation_with_model(args, model_m2f)
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