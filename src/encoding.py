import argparse
import cv2
from tqdm import tqdm
from glob import glob
import os

# Set up argument parser
parser = argparse.ArgumentParser()
parser.add_argument('src', help='Frame Directory')
parser.add_argument('--harmonize', action='store_true', help='Harmonize the video output')
parser.add_argument('--mode', type=str, default=None, help='Mode for harmonized output (optional)')

args = parser.parse_args()

# Check if harmonize flag is set and adjust variables accordingly
if args.harmonize:
    viddir = './videoHarmonized'
    path = args.src
    _, clip, model = args.src.split('/')
    dstdir = os.path.join(viddir, clip + "_harmonized")
    mode_list = ['original', 'offset', 'dynamic','wtp','ptw']
    if args.mode:
        pathOut = os.path.join(dstdir, f'{clip}_{model}_{mode_list[int(args.mode)]}.mp4')
    else:
        pathOut = os.path.join(dstdir, f'{clip}_{model}.mp4')
else:
    viddir = './video'
    path = args.src
    _, clip, model, mode = args.src.split('/')
    dstdir = os.path.join(viddir, clip)
    pathOut = os.path.join(dstdir, f'{model}_{mode}.mp4')

# Create destination directory if it doesn't exist
os.makedirs(dstdir, exist_ok=True)

# Gather all images in the specified path
img_list = []
for ext in ['*.jpg', '*.png']: 
    img_list.extend(glob(os.path.join(path, ext)))
img_list.sort()

# Set up video writer properties
fps = 20
frame_array = []
for idx, path in tqdm(enumerate(img_list)):
    img = cv2.imread(path)
    height, width, layers = img.shape
    size = (width, height)
    frame_array.append(img)

# Initialize VideoWriter and write frames
out = cv2.VideoWriter(pathOut, cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), fps, size)
for i in range(len(frame_array)):
    out.write(frame_array[i])
out.release()
