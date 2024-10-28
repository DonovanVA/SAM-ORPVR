#!/bin/bash

# Ensure correct number of arguments
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <parent_directory>"
  exit 1
fi

# Assign variables from arguments
PARENT_DIR="$1"  # This can now be a relative path

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
    # Remove trailing slash from SAMPLE_DIR
    SAMPLE_DIR=${SAMPLE_DIR%/}
    
    # Get the full path for SAMPLE_NAME including parent directory
    SAMPLE_NAME="$SAMPLE_DIR"  
    ANNOTATION_NAME="${SAMPLE_DIR/JPEGImages/Annotations}"  
    echo "Processing directory: $SAMPLE_NAME"
    echo "Annotation directory: $ANNOTATION_NAME"

    # Step 1: Crop images
    echo "Running crop.py on $SAMPLE_NAME..."
    python crop.py "$SAMPLE_NAME" --width 640 --height 480 --mode 0

    echo "Completed cropping for directory: $SAMPLE_NAME"
done

# Step 2: Run the sam2 script
echo "Running SAM2 on the cropped images"
python sam2/SAM2segmenter.py cropped
echo "Cropping completed for all directories."
