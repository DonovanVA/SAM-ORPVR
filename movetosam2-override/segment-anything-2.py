from sam2.build_sam import build_sam2_video_predictor
import os
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import cv2
# Define the paths
current_dir = os.getcwd()
checkpoint = os.path.join(current_dir, "sam2", "checkpoints", "sam2.1_hiera_large.pt")
model_cfg = "configs/sam2.1/sam2.1_hiera_l.yaml"
video_dir = os.path.join(current_dir, "DAVIS-test", "JPEGImages", "480p", "bmx-bumps")
points,labels=[],[]
# Check if video directory exists
if not os.path.exists(video_dir):
    raise FileNotFoundError(f"Video directory does not exist: {video_dir}")

# Initialize the predictor
predictor = build_sam2_video_predictor(model_cfg, checkpoint)


# Display mask
def show_mask(mask, ax, obj_id=None, random_color=False):
    if random_color:
        color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
    else:
        cmap = plt.get_cmap("tab10")
        cmap_idx = 0 if obj_id is None else obj_id
        color = np.array([*cmap(cmap_idx)[:3], 0.6])
    h, w = mask.shape[-2:]
    mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
    ax.imshow(mask_image)
## Display points
def show_points(coords, labels, ax, marker_size=200):
    pos_points = coords[labels == 1]
    neg_points = coords[labels == 0]
    ax.scatter(pos_points[:, 0], pos_points[:, 1], color='green', marker='*', s=marker_size, edgecolor='white', linewidth=1.25)
    ax.scatter(neg_points[:, 0], neg_points[:, 1], color='red', marker='*', s=marker_size, edgecolor='white', linewidth=1.25)

def on_click(event, frame_idx,points,labels):
    # Check if the click is inside the axes
    if event.inaxes:
        # Add the clicked point
        point = np.array([event.xdata, event.ydata], dtype=np.float32)
        points.append(point)
        labels.append(1)  # Add a positive click label

        # Print the added point and the current labels for debugging
        print(f"Point added: {point}, Labels: {labels}")
def renderFrame(frame_idx):
    plt.figure(figsize=(9, 6))
    plt.title(f"Processed Frame {frame_idx}")
    frame_image = Image.open(os.path.join(video_dir, frame_names[frame_idx]))
    plt.imshow(frame_image)
   
def renderMasks(frame_idx):
    plt.axis('off')
    # Connect mouse click event handler
    plt.gcf().canvas.mpl_connect('button_press_event', lambda event: on_click(event, frame_idx,points,labels))
    plt.show()  # Display the processed frame  
def highlight_segments(frame_idx,points,labels):

    # Reset state for each frame
    predictor.reset_state(inference_state)

    # Show the results on the current frame
    renderFrame(frame_idx)  
    # Adding points to get segmentation masks
    if points:
        # Convert points and labels to the correct format
        np_points = np.array(points, dtype=np.float32)
        np_labels = np.array(labels, dtype=np.int32)
        
        _, out_obj_ids, out_mask_logits = predictor.add_new_points_or_box(
            inference_state=inference_state,
            frame_idx=frame_idx,
            obj_id=None,  # Highlight all segments
            points=np_points,
            labels=np_labels,
        )
        # Highlight all detected segments in the current frame
        for i, out_obj_id in enumerate(out_obj_ids):
            mask = (out_mask_logits[i] > 0.0).cpu().numpy()  # Convert mask to numpy
            show_mask(mask, plt.gca(), obj_id=out_obj_id)  # Use the corresponding object ID
        
        show_points(np_points, np_labels, plt.gca())  # Show clicked points  
    renderMasks(frame_idx)
   
# Load frame names
frame_names = [
    p for p in os.listdir(video_dir)
    if os.path.splitext(p)[-1].lower() in [".jpg", ".jpeg"]
]

# Initialize inference state
inference_state = predictor.init_state(video_path=video_dir)

# Process each frame to highlight all segments
for idx in range(len(frame_names)):
    highlight_segments(idx,points,labels)

## main program loop
# idx=0
# while True:
#     highlight_segments(idx,points,labels)
#     key = cv2.waitKey(1)
#     if key==ord('q'):
#         break
#     elif key==ord('d'):
#         if(idx<len(frame_names)-1):
#             idx+=1
#         highlight_segments(idx,points,labels)
#         continue
#     elif key== ord('a'):
#         if(idx>0):
#             idx-=1
#         highlight_segments(idx,points,labels)
#         continue