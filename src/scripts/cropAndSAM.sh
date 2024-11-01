#!/bin/bash
cd ../src
# Ensure at least one argument
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <image_parent_directory> [--width <width>] [--height <height>]"
  exit 1
fi

# Assign the first argument to PARENT_DIR
PARENT_DIR="$1"
shift

# Default values for width and height
WIDTH=640
HEIGHT=480

# Parse additional arguments for width and height
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --width)
      shift
      WIDTH="$1"
      ;;
    --height)
      shift
      HEIGHT="$1"
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
  shift
done

# Step 0: Move SAM2segmenter.py to sam2 folder, replacing any existing file
if [ -f "movetosam2-override/SAM2segmenter.py" ]; then
  echo "Moving SAM2segmenter.py from movetosam2-override to sam2 folder..."
  cp -f "movetosam2-override/SAM2segmenter.py" "sam2/SAM2segmenter.py"
  echo "SAM2segmenter.py moved successfully."
else
  echo "SAM2segmenter.py not found in movetosam2-override. Exiting."
  exit 1
fi

# Process each subdirectory in the parent directory
for SAMPLE_DIR in "$PARENT_DIR"/*/; do
  SAMPLE_DIR=${SAMPLE_DIR%/}
  SAMPLE_NAME="$SAMPLE_DIR"
  ANNOTATION_NAME="${SAMPLE_DIR/JPEGImages/Annotations}"  
  echo "Processing directory: $SAMPLE_NAME"
  echo "Annotation directory: $ANNOTATION_NAME"

  # Step 1: Crop images
  echo "Running crop.py on $SAMPLE_NAME with width $WIDTH and height $HEIGHT..."
  python crop.py "$SAMPLE_NAME" --width "$WIDTH" --height "$HEIGHT" --mode 0

  echo "Completed cropping for directory: $SAMPLE_NAME"
done

# Step 2: Run the sam2 script
echo "Running SAM2 on the cropped images"
python sam2/SAM2segmenter.py cropped
echo "Cropping completed for all directories."
echo "Completed..."
sleep 3

