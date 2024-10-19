import os
import numpy as np
from PIL import Image, ImageTk,ImageDraw, ImageFont
import tkinter as tk
from tkinter import Label, Button, Text
import cv2
from sam2.build_sam import build_sam2_video_predictor

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
      label=Label(self.root, text = self.frame_label)
      label.grid(row=0, column=0, columnspan=3)
      if self.img_label is None:
        self.img_label = Label(self.root, image=img_tk)
        self.img_label.image = img_tk
        self.img_label.grid(row=2, column=0, columnspan=3)
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
        self.predictor.reset_state(self.inference_state)
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
      label=Label(self.root, text = self.frame_label)
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
    def reset_frame(self):
       print("reset!")
    def run(self):
      self.read_from_vid_dir(self.video_dir)
      self.render_frame()
      next_button = Button(self.root, text="Next Frame", command=self.next_frame)
      reset_button = Button(self.root, text="Reset Frame", command=self.reset_frame)
      prev_button = Button(self.root, text="Previous Frame", command=self.prev_frame)
      next_button.grid(row=1, column=2)
      reset_button.grid(row=1, column=1)
      prev_button.grid(row=1, column=0)

      self.root.mainloop()

# Define the paths
current_dir = os.getcwd()
checkpoint = os.path.join(current_dir, "sam2", "checkpoints", "sam2.1_hiera_large.pt")
model_cfg = "configs/sam2.1/sam2.1_hiera_l.yaml"
video_dir = os.path.join(current_dir, "DAVIS-test", "JPEGImages", "480p", "bmx-bumps")
points, labels = [], []

segmenter_ui = SAM2segmenterUI(points, labels, model_cfg, video_dir, checkpoint)
segmenter_ui.run()