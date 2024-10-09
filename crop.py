import cv2
import os
import argparse
import shutil

def crop_center(image, target_width, target_height):
    """Crop the center of the image to the target width and height."""
    h, w = image.shape[:2]
    x_center, y_center = w // 2, h // 2
    x1 = x_center - target_width // 2
    x2 = x_center + target_width // 2
    y1 = y_center - target_height // 2
    y2 = y_center + target_height // 2
    return image[y1:y2, x1:x2]

def create_directory(directory):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def move_already_cropped_images(sample_name):
    """Move already cropped images from 'cropped' to 'dataset' directory."""
    already_cropped_dir = os.path.join("cropped", sample_name)
    images_dir = os.path.join("dataset", sample_name, "images")
    create_directory(images_dir)

    for filename in os.listdir(already_cropped_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):  # Adjust extensions as needed
            source_file = os.path.join(already_cropped_dir, filename)
            destination_file = os.path.join(images_dir, filename)
            try:
                shutil.move(source_file, destination_file)
                print(f"Moved: {source_file} to {destination_file}")
            except Exception as e:
                print(f"Error moving file {source_file}: {e}")

def preprocess_images(input_dir, target_width, target_height, mode):
    """Preprocess all image files in the input directory by cropping the center and saving them."""
    sample_name = os.path.basename(input_dir)
    
    if mode == 1:
        move_already_cropped_images(sample_name)

    cropped_dir = os.path.join("cropped", sample_name) if mode == 0 else os.path.join("dataset", sample_name, "masks")
    create_directory(cropped_dir)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):  # Adjust extensions as needed
            image_path = os.path.join(input_dir, filename)
            image = cv2.imread(image_path)

            if image is None:
                print(f"Error reading image {filename}. Skipping.")
                continue

            # Crop the center of the image
            cropped_image = crop_center(image, target_width, target_height)

            # Save the cropped image
            output_path = os.path.join(cropped_dir, filename)
            cv2.imwrite(output_path, cropped_image)
            print(f"Processed image saved to {output_path}")

    print("Processing completed.")

def main():
    parser = argparse.ArgumentParser(description="Crop the center of images to a specified size.")
    parser.add_argument('input_dir', type=str, help="Directory containing the input image files.")
    parser.add_argument('--width', type=int, default=640, help="Target width of the cropped images.")
    parser.add_argument('--height', type=int, default=480, help="Target height of the cropped images.")
    parser.add_argument('--mode', type=int, default=0, help="0 for cropped directory, 1 for dataset directory.")
    args = parser.parse_args()
    
    preprocess_images(args.input_dir, args.width, args.height, args.mode)

if __name__ == '__main__':
    main()
