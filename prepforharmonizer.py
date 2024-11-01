import os
import cv2
import numpy as np
import json
from glob import glob
from tqdm import tqdm
import torch
import torchvision.transforms as transforms
from PIL import Image
from util.option_relocate import args, Relocator
def relocate_objects_and_save_mask(imgdir, objdir, resultdir, mode=args.mode):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    modes = ['original', 'offset', 'dynamic']
    mode_idx = modes.index(mode) if mode in modes else 0

    # Initialize Relocator with args configuration
    args.device = device
    args.mode = mode_idx

    # Get file lists
    #flist = sorted(glob(os.path.join(bimgdir, '*.png')) + glob(os.path.join(bimgdir, '*.jpg')))
    ilist = sorted(glob(os.path.join(imgdir, '*.png')) + glob(os.path.join(imgdir, '*.jpg')))
    olist = sorted(glob(os.path.join(objdir, '*.json')))

    if ilist:
        sample_img = cv2.imread(ilist[0], cv2.IMREAD_COLOR)
        h, w, _ = sample_img.shape
    else:
        # Set a default size if no images are available
        h, w = 480, 854
    bimg = np.zeros((h, w, 3), dtype=np.uint8)

    
    args.h, args.w, _ = bimg.shape
    #args.new_w = int(np.ceil(args.h * 16 / 9))

    relocator = Relocator(args)
    
    print("Start Relocating....")
    os.makedirs(resultdir, exist_ok=True)
    
    for i in tqdm(range(len(ilist))):
        fname = os.path.basename(ilist[i])
        name, _ = os.path.splitext(fname)  # Remove existing extension
        jpg_fname = f"{name}.jpg"  # Set the output filename to .jpg
        
        # Create a black background for each image
        bimg = np.zeros((args.height, args.width, 3), dtype=np.uint8)
        bimg = cv2.resize(bimg, dsize=(args.width, args.height), interpolation=cv2.INTER_CUBIC)

        img = cv2.imread(ilist[i], cv2.IMREAD_COLOR)
        with open(olist[i], "r") as f:
            objects = json.load(f)
        
        frame = relocator.relocate(bimg, img, objects)
        
        # Save only in .jpg format
        cv2.imwrite(os.path.join(resultdir, jpg_fname), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    mask_dir = os.path.join(os.path.dirname(resultdir), 'mask')
    os.makedirs(mask_dir, exist_ok=True)
    
    for file in os.listdir(resultdir):
        old_file = os.path.join(resultdir, file)
        new_file = os.path.join(mask_dir, file)
        os.rename(old_file, new_file)

    # Remove the old result directory
    os.rmdir(resultdir)
    print(f"Object Relocated Images are stored in {resultdir}")
    print("Complete")

def resize_image_opencv(image_tensor, new_width, new_height):
    image_np = image_tensor.permute(1, 2, 0).numpy()
    resized_image_np = cv2.resize(image_np, dsize=(new_width, new_height), interpolation=cv2.INTER_CUBIC)
    resized_image_tensor = transforms.ToTensor()(resized_image_np)
    return resized_image_tensor

def copy_images_and_masks(destination_base_path, masks_base_path):
    for foldernameA in os.listdir(args.src):
        folderA_path = os.path.join(args.src, foldernameA)
        if os.path.isdir(folderA_path):
            for foldernameB in os.listdir(folderA_path):
                folderB_path = os.path.join(folderA_path, foldernameB)
                if os.path.isdir(folderB_path):
                    for foldernameC in os.listdir(folderB_path):
                        folderC_path = os.path.join(folderB_path, foldernameC)
                        if os.path.isdir(folderC_path):
                            source_images_path = folderC_path
                            destination_images_path = os.path.join(destination_base_path, foldernameA, 'composite')
                            
                            source_masks_path = os.path.join(masks_base_path, foldernameA, 'masks')
                            destination_masks_path = os.path.join(destination_base_path, foldernameA, 'masks')

                            os.makedirs(destination_images_path, exist_ok=True)
                            os.makedirs(destination_masks_path, exist_ok=True)

                            for root, _, files in os.walk(source_images_path):
                                for file in files:
                                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                                        source_file = os.path.join(root, file)
                                        destination_file = os.path.join(destination_images_path, file)
                                        image_tensor = transforms.ToTensor()(Image.open(source_file))
                                        #resized_image_tensor = resize_image_opencv(image_tensor, new_width, new_height)
                                        transforms.ToPILImage()(image_tensor).save(destination_file)

                            
                            # Apply relocation on masks
                            relocate_objects_and_save_mask(
                                imgdir=source_masks_path,
                                objdir=os.path.join(masks_base_path, foldernameA, 'objects'),
                                resultdir=destination_masks_path,
                                mode='original'
                            )

                            print(f"Copied and resized images to: {destination_images_path}")
                            print(f"Copied and resized masks to: {destination_masks_path}")

#source_base_path = 'result/'
destination_base_path = 'harmonize/'
masks_base_path = 'dataset/'

copy_images_and_masks(destination_base_path, masks_base_path)


