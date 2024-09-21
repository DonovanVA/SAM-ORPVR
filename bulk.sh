#!/bin/bash

# Ensure correct number of arguments
if [ "$#" -lt 3 ]; then
  echo "Usage: $0 <parent_directory> <model_type> <mode>"
  echo "Model types: aotgan, e2fgvi, e2fgvi_hq"
  echo "Modes: 0 (original), 1 (offset), 2 (dynamic)"
  exit 1
fi

# Assign variables from arguments
PARENT_DIR="$1"  # This can now be a relative path
MODEL_TYPE="$2"
MODE="$3"

# Validate model type
if [[ "$MODEL_TYPE" != "aotgan" && "$MODEL_TYPE" != "e2fgvi" && "$MODEL_TYPE" != "e2fgvi_hq" ]]; then
  echo "Invalid model type: $MODEL_TYPE"
  echo "Valid options: aotgan, e2fgvi, e2fgvi_hq"
  exit 1
fi

# Validate mode as an integer
if ! [[ "$MODE" =~ ^[0-2]$ ]]; then
  echo "Invalid mode: $MODE"
  echo "Valid options: 0 (original), 1 (offset), 2 (dynamic)"
  exit 1
fi

# Map mode to the corresponding result folder (original, offset, dynamic)
case "$MODE" in
  0)
    RESULT_TYPE="original"
    ;;
  1)
    RESULT_TYPE="offset"
    ;;
  2)
    RESULT_TYPE="dynamic"
    ;;
esac

# Process each subdirectory in the parent directory
for SAMPLE_DIR in "$PARENT_DIR"/*/; do
    # Remove trailing slash from SAMPLE_DIR
    SAMPLE_DIR=${SAMPLE_DIR%/}
    
    # Get the full path for SAMPLE_NAME including parent directory
    SAMPLE_NAME="$SAMPLE_DIR"  # Now SAMPLE_NAME includes the full path

    echo "Processing directory: $SAMPLE_NAME"

    # Step 1: Crop images
    echo "Running crop.py on $SAMPLE_NAME..."
    python crop.py "$SAMPLE_NAME" --width 640 --height 480

    # Step 2: Mask images
    echo "Running masking.py on cropped/${SAMPLE_NAME##*/}..."
    python masking.py "cropped/${SAMPLE_NAME##*/}"

    # Step 3: Inpaint images using the specified model
    echo "Running inpainting.py on dataset/${SAMPLE_NAME##*/} with model $MODEL_TYPE..."
    python inpainting.py "dataset/${SAMPLE_NAME##*/}" --model "$MODEL_TYPE"
    # Step 4: Relocate images using the specified mode
    echo "Running relocating.py on result_inpaint/${SAMPLE_NAME##*/}/$MODEL_TYPE with mode $MODE..."
    python relocating.py "result_inpaint/${SAMPLE_NAME##*/}/$MODEL_TYPE" --mode "$MODE"

    # Step 5: Encode images with the corresponding result type based on the mode
    echo "Running encoding.py on result/${SAMPLE_NAME##*/}/$MODEL_TYPE/$RESULT_TYPE..."
    python encoding.py "result/${SAMPLE_NAME##*/}/$MODEL_TYPE/$RESULT_TYPE"

    echo "Completed processing for directory: $SAMPLE_NAME"
done

echo "Pipeline execution completed for all directories."
