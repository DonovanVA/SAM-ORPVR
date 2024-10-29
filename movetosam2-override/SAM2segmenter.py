import os
import numpy as np
from PIL import Image, ImageTk,ImageDraw, ImageFont, ImageOps
import tkinter as tk
from tkinter import Label, Button, Text
import cv2
from sam2.build_sam import build_sam2_video_predictor
import matplotlib.pyplot as plt
import json
import shutil
import argparse
class SAM2segmenterUI:
    def __init__(self, points, labels, model_cfg, video_dir, checkpoint):
        self.points = points
        self.labels = labels
        self.model_cfg = model_cfg
        self.video_dir = video_dir
        self.checkpoint = checkpoint
        self.predictor = build_sam2_video_predictor(model_cfg, checkpoint)
        self.inference_state = self.predictor.init_state(video_path=video_dir)
        self.frame_names = []
        self.current_frame_idx = 0
        self.img_label = None
        self.img_mask = None
        self.frame_label="undefined frame"
        self.root = tk.Tk()
        self.root.title("SAM2 Segmenter UI")

    def read_from_vid_dir(self, video_dir):
        self.frame_names = [p for p in os.listdir(video_dir) if os.path.splitext(p)[-1].lower() in [".jpg", ".jpeg"]]
        if not os.path.exists(video_dir):
            raise FileNotFoundError(f"Video directory does not exist: {video_dir}")

    def on_click(self, event):
        x = event.x
        y = event.y
        point = np.array([x, y], dtype=np.float32)
        self.points.append(point)
        self.labels.append(1)  # Positive label for now
        print(f"Point added: {point}")
        self.update_frame()

    def render_frame(self):
      frame_image = Image.open(os.path.join(self.video_dir, self.frame_names[self.current_frame_idx]))
      img_tk = ImageTk.PhotoImage(frame_image)
      img_masked = np.asarray(Image.open(os.path.join(self.video_dir, self.frame_names[self.current_frame_idx])))
      black_background = Image.fromarray(np.full(img_masked.shape, 0, dtype=np.uint8))
      self.frame_label="Frame"+str(self.current_frame_idx+1)
      helper = Label(self.root, text = "Find a reference frame to mask")
      helper.grid(row=0, column=0, columnspan=3)
      label=Label(self.root, text = self.frame_label)
      label.grid(row=1, column=0, columnspan=3)
      if self.img_label is None:
        self.img_label = Label(self.root, image=img_tk)
        self.img_label.image = img_tk
        self.img_label.grid(row=3, column=0, columnspan=3)
        self.img_label.bind("<Button-1>", self.on_click)  # Click event
      else:
        self.img_label.configure(image=img_tk)
        self.img_label.image = img_tk
      
      if self.img_mask is None:
        self.img_mask = Label(self.root, image=ImageTk.PhotoImage(black_background))
        self.img_mask.image = black_background
        self.img_mask.grid(row=5, column=0, columnspan=3)
      else:
        self.img_mask.configure(image=ImageTk.PhotoImage(black_background))
        self.img_mask.image = black_background

    def highlight_segments(self):
        np_points = np.array(self.points, dtype=np.float32)
        np_labels = np.array(self.labels, dtype=np.int32)

        _, out_obj_ids, out_mask_logits = self.predictor.add_new_points_or_box(
            inference_state=self.inference_state,
            frame_idx=self.current_frame_idx,
            obj_id=None,
            points=np_points,
            labels=np_labels,
        )
        
        # Convert the current frame to a numpy array
        frame = np.asarray(Image.open(os.path.join(self.video_dir, self.frame_names[self.current_frame_idx])))
        highlighted_frame = np.copy(frame)  # Create a writable copy of the frame

        # Create a black background the same size as the frame
        black_background = np.full(frame.shape, 0, dtype=np.uint8)

        # Loop through each detected segment and apply the mask
        for i, out_obj_id in enumerate(out_obj_ids):
            mask = (out_mask_logits[i] > 0.0).cpu().numpy()  # Convert mask to numpy
            mask = np.squeeze(mask)
            # Ensure that mask shape matches the height and width of the frame
            if mask.shape[:2] != frame.shape[:2]:
                raise ValueError(f"Mask shape {mask.shape} does not match frame shape {frame.shape}")
            highlighted_frame[mask > 0] = [255, 255, 255]  # Highlight the non detected areas of the mask in black
            highlighted_frame[mask <= 0] = [0,0,0] # Highlight the non detected areas of the mask in black
        # Convert the highlighted frame back to a PIL image
        frame_image = Image.fromarray(highlighted_frame)
        try:
          # Create an Image object for the black background
          segment_image = Image.fromarray(black_background)
          # Paste the highlighted image on top of the black background
          segment_image.paste(frame_image, (0, 0))
        except:
            print("Failed to create image")
            defaultImage=Image.fromarray(np.full(frame.shape, 0, dtype=np.uint8))
            draw = ImageDraw.Draw(defaultImage)
            draw.text((0, 0),"Failed to create image",(0,0,0))
        return Image.fromarray(frame),segment_image  # Return the combined image with black background and highlighted segments
    def update_frame(self):
      frame_image,segment_image = self.highlight_segments()
      self.frame_label="Frame"+str(self.current_frame_idx+1)
      img_tk = ImageTk.PhotoImage(frame_image)
      self.img_label.configure(image=img_tk)
      self.img_label.image = img_tk
      img_masked=ImageTk.PhotoImage(segment_image)
      self.img_mask.configure(image=img_masked)
      self.img_mask.image = img_masked

    def next_frame(self):
      self.current_frame_idx = (self.current_frame_idx + 1) % len(self.frame_names)
      self.points.clear()  # Reset points for each frame
      self.labels.clear()
      self.render_frame()

    def prev_frame(self):
      self.current_frame_idx = (self.current_frame_idx - 1) % len(self.frame_names)
      self.points.clear()  # Reset points for each frame
      self.labels.clear()
      self.render_frame()

    def play(self):
      ## End the tkinter application and begin generating the video
      # Get the parent directory of the current script (Repo)
      parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
      output_dir = os.path.join(parent_dir, "dataset")
      
      # Create the output directory if it doesn't exist
      images_output_dir = os.path.join(output_dir, os.path.basename(self.video_dir),"images")
      masks_output_dir = os.path.join(output_dir, os.path.basename(self.video_dir),"masks")
      objects_output_dir = os.path.join(output_dir, os.path.basename(self.video_dir),"objects")
      if not os.path.exists(output_dir):
        os.makedirs(output_dir)
      if not os.path.exists(masks_output_dir):
        os.makedirs(masks_output_dir)
      if not os.path.exists(objects_output_dir):
        os.makedirs(objects_output_dir)
      if not os.path.exists(images_output_dir):
        os.makedirs(images_output_dir)
      self.close_app()
      for image_file in os.listdir(self.video_dir):
        image_path = os.path.join(self.video_dir, image_file)
        if os.path.isfile(image_path) and image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
            shutil.copy(image_path, images_output_dir)
      video_segments={}
      for out_frame_idx,out_obj_ids,out_mask_logits in self.predictor.propagate_in_video(self.inference_state):
         video_segments[out_frame_idx]={
            out_obj_id:(out_mask_logits[i]>0.0).cpu().numpy() 
            for i, out_obj_id in enumerate(out_obj_ids)
         }
      vis_frame_stride = 1
      #print("Generated frame indices:", list(video_segments.keys()))
      for out_frame_idx in range(0, len(self.frame_names), vis_frame_stride):
        # Load the current frame as background
        if out_frame_idx in video_segments:
          for out_obj_id, out_mask in video_segments[out_frame_idx].items():
            # Ensure mask is 2D (height, width)
            if out_mask.ndim == 3 and out_mask.shape[0] == 1:
                out_mask = out_mask.squeeze(0)  # Convert to shape (h, w)
            # Convert mask to Image and resize to match frame
            mask_image = Image.fromarray((out_mask * 255).astype("uint8"))
            mask_image = ImageOps.colorize(mask_image, black="black", white="white").convert("RGBA")
          # Save frame with overlayed mask
          mask_image.save(os.path.join(masks_output_dir, f"{str(out_frame_idx).zfill(5)}.png"))
      
          objects = {'box': [], 'coor': []}
          # Create a binary mask from the predefined mask
          mask_binary = (out_mask > 0).astype(np.uint8)
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
          fname = os.path.splitext(os.path.basename(str(out_frame_idx).zfill(5)))[0]
          with open(os.path.join(objects_output_dir, fname + '.json'), "w") as f:
              json.dump(objects, f)
        else:
          print(f"Warning: Frame index {out_frame_idx} not found in video_segments")

    def reset_frame(self):
      print("reset!")
      self.points.clear()
      self.labels.clear()
      self.render_frame()
      self.predictor.reset_state(self.inference_state)

    def run(self):
      self.read_from_vid_dir(self.video_dir)
      self.render_frame()
      #next_button = Button(self.root, text="Next Frame", command=self.next_frame)
      reset_button = Button(self.root, text="Reset Frame", command=self.reset_frame)
      #prev_button = Button(self.root, text="Previous Frame", command=self.prev_frame)
      play_button = Button(self.root, text="Play", command=self.play)
      play_button.grid(row=2, column=3)
      #next_button.grid(row=2, column=2)
      reset_button.grid(row=2, column=1)
      #prev_button.grid(row=2, column=0)
      self.root.mainloop()

    def close_app(self):
      self.root.quit()  # This will exit the main loop and close the app
      self.root.destroy()  # This ensures that the Tkinter window is properly destroyed
if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser(description="Run SAM2 segmenter on video directories.")
    parser.add_argument("video_parent_dir", type=str, help="Path to the parent directory containing video subdirectories")
    args = parser.parse_args()

    # Paths and variables
    current_dir = os.getcwd()
    checkpoint = os.path.join(current_dir, "sam2", "checkpoints", "sam2.1_hiera_large.pt")
    model_cfg = "configs/sam2.1/sam2.1_hiera_l.yaml"
    video_parent_dir = args.video_parent_dir
    points, labels = [], []

    for video_dir in os.listdir(video_parent_dir):
        full_video_dir = os.path.join(video_parent_dir, video_dir)
        if os.path.isdir(full_video_dir):
            try:
                segmenter_ui.close_app()
            except:
                print("App has already been destroyed, continuing to the next image")
            segmenter_ui = SAM2segmenterUI(points, labels, model_cfg, full_video_dir, checkpoint)
            segmenter_ui.run()
            try:
                segmenter_ui.close_app()
            except:
                print("App has already been destroyed, continuing to the next image")
