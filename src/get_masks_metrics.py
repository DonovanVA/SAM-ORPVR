import os
import cv2
import csv
import numpy as np

def calculate_mask_area(mask_path):
    # Read the mask image in grayscale mode
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    # Count the number of white pixels (255) in the mask, which represents the mask area
    mask_area = np.sum(mask == 255)
    # Get the width and height of the image
    height, width = mask.shape
    return mask_area, width, height

def process_directory(base_dir):
    # Define the path to save the metrics CSV file in the 'metrics' folder next to the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    metrics_dir = os.path.join(script_dir, "metrics")
    metrics_file = os.path.join(metrics_dir, "mask_metrics.csv")
    
    # Ensure the metrics directory exists
    os.makedirs(metrics_dir, exist_ok=True)

    # Open the CSV file to append mask areas
    with open(metrics_file, mode='a', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["ImageSetID", "Frame_ID", "Area", "Mask_Img_width", "Mask_Img_height"])
        
        # Check if the file is empty and write the header if necessary
        if csv_file.tell() == 0:  # File is empty
            writer.writeheader()
        
        # Loop through each subdirectory in the base directory
        for folder in os.listdir(base_dir):
            folder_path = os.path.join(base_dir, folder)
            # Only process if it's a directory
            if os.path.isdir(folder_path):
                # Get the last part of the folder path
                folder_name = os.path.basename(folder_path)
                
                masks_dir = os.path.join(folder_path, "masks")
                
                # Check if the masks directory exists
                if os.path.exists(masks_dir):
                    # Loop through each image file in the masks directory
                    for mask_file in os.listdir(masks_dir):
                        mask_path = os.path.join(masks_dir, mask_file)
                        if os.path.isfile(mask_path) and mask_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                            # Calculate the area of the mask and get image width and height
                            mask_area, width, height = calculate_mask_area(mask_path)
                            
                            # Write the data to the CSV file
                            writer.writerow({
                                "ImageSetID": folder_name,  # Use only the last folder name
                                "Frame_ID": os.path.splitext(mask_file)[0],  # Exclude file extension
                                "Area": mask_area,
                                "Mask_Img_width": width,
                                "Mask_Img_height": height
                            })
                            print(f"Processed {mask_file} in {folder_name}, Area: {mask_area} pixels, Width: {width}, Height: {height}")
    
    print(f"Metrics saved to {metrics_file}")

# Set base_directory_path to the 'dataset' folder in the same directory as this script
base_directory_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset")
process_directory(base_directory_path)


