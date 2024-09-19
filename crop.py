import cv2
import os
import argparse

def crop_center(image, target_width, target_height):
    """
    Crop the center of the image to the target width and height.
    """
    h, w = image.shape[:2]
    x_center, y_center = w // 2, h // 2
    x1 = x_center - target_width // 2
    x2 = x_center + target_width // 2
    y1 = y_center - target_height // 2
    y2 = y_center + target_height // 2
    return image[y1:y2, x1:x2]

def preprocess_images(input_dir, output_dir, target_width, target_height):
    """
    Preprocess all image files in the input directory by cropping the center
    and save them to the output directory.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):  # Adjust extensions as needed
            image_path = os.path.join(input_dir, filename)
            image = cv2.imread(image_path)

            if image is None:
                print(f"Error reading image {filename}. Skipping.")
                continue

            # Crop the center of the image
            cropped_image = crop_center(image, target_width, target_height)
            
            output_path = os.path.join(output_dir, filename)
            cv2.imwrite(output_path, cropped_image)
            print(f"Processed image saved to {output_path}")

    print("Processing completed.")

def main():
    parser = argparse.ArgumentParser(description="Crop the center of images to a specified size.")
    parser.add_argument('input_dir', type=str, help="Directory containing the input image files.")
    parser.add_argument('output_dir', type=str, help="Directory to save the processed image files.")
    parser.add_argument('--width', type=int, default=640, help="Target width of the cropped images.")
    parser.add_argument('--height', type=int, default=480, help="Target height of the cropped images.")
    
    args = parser.parse_args()
    
    preprocess_images(args.input_dir, args.output_dir, args.width, args.height)

if __name__ == '__main__':
    main()
