#!/bin/bash
cd ../src
# Ensure correct number of arguments
if [ "$#" -lt 3 ]; then
  echo "Usage: $0 <image_parent_directory> <model> <mode> [--inpaint-only] [--relocating-only] [--no-mask-model] [--crop_to_width] <ct_width> [--crop_to_height] <ct_height> [--target_width] <t_width> [--target_height] <t_height>"
  echo "Model types: aotgan, e2fgvi, e2fgvi_hq"
  echo "Modes: 0 (original), 1 (offset), 2 (dynamic)"
  exit 1
fi

# Assign variables from arguments
PARENT_DIR="$1"  # This can now be a relative path
MODEL_TYPE="$2"
MODE="$3"

# Optional flags and parameters
NO_MASK_MODEL=0
INPAINT_ONLY=0
RELOCATING_ONLY=0
HAS_MASK_MODEL="m2f"
CROP_TO_WIDTH=640  # Default width
CROP_TO_HEIGHT=480  # Default height
TARGET_WIDTH=854 # Default target width
TARGET_HEIGHT=480 # Default target height
# Parse additional flags and parameters
shift 3
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --no-mask-model)
      NO_MASK_MODEL=1
      HAS_MASK_MODEL="no-model"
      ;;
    --inpaint-only)
      INPAINT_ONLY=1
      ;;
    --relocating-only)
      RELOCATING_ONLY=1
      ;;
    --crop_to_width)
      shift
      CROP_TO_WIDTH="$1"
      ;;
    --crop_to_height)
      shift
      CROP_TO_HEIGHT="$1"
      ;;
    --target_width)
      shift
      TARGET_WIDTH="$1"
      ;;
    --target_height)
      shift
      TARGET_HEIGHT="$1"
      ;;
    *)
      echo "Unknown flag: $1"
      exit 1
      ;;
  esac
  shift
done

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
    SAMPLE_NAME="$SAMPLE_DIR"  
    ANNOTATION_NAME="${SAMPLE_DIR/JPEGImages/Annotations}"  
    echo "Processing directory: $SAMPLE_NAME"
    echo "Annotation directory: $ANNOTATION_NAME"

    # Step 1 and Step 2: Crop and mask images (skip if --inpaint-only OR --relocating-only is set)
    if [ "$RELOCATING_ONLY" -eq 0 ] && [ "$INPAINT_ONLY" -eq 0 ]; then
        # Step 1: Crop images
        echo "Running crop.py on $SAMPLE_NAME with width $CROP_TO_WIDTH and height $CROP_TO_HEIGHT..."
        python crop.py "$SAMPLE_NAME" --width "$CROP_TO_WIDTH" --height "$CROP_TO_HEIGHT" --mode 0

        # Step 2: Run masking and any preprocessing step depending on --no-mask-model flag
        if [ "$NO_MASK_MODEL" -eq 1 ]; then
            echo "No mask model is selected, cropping mask..."
            python crop.py "$ANNOTATION_NAME" --width "$CROP_TO_WIDTH" --height "$CROP_TO_HEIGHT" --mode 1
            echo "Running masking.py without model on cropped/${SAMPLE_NAME##*/}/masks..."
            python masking.py "dataset/${SAMPLE_NAME##*/}/masks" --mode 1 
        else
            echo "Running masking.py with model on cropped/${SAMPLE_NAME##*/}..."
            python masking.py "cropped/${SAMPLE_NAME##*/}" --mode 0
        fi
    fi

    if [ "$RELOCATING_ONLY" -eq 0 ]; then
        # Step 3: Inpaint images using the specified model
        echo "Running inpainting.py on dataset/${SAMPLE_NAME##*/} with model $MODEL_TYPE..."
        python inpainting.py "dataset/${SAMPLE_NAME##*/}" --model "$MODEL_TYPE"
    else
        echo "Skipping inpainting step as --relocating-only flag is set."
    fi

    # Step 4: Relocate images using the specified mode
    echo "Running relocating.py on result_inpaint/${SAMPLE_NAME##*/}/$MODEL_TYPE with mode $MODE... to width $TARGET_WIDTH and height $TARGET_HEIGHT"
    python relocating.py "result_inpaint/${SAMPLE_NAME##*/}/$MODEL_TYPE" --mode "$MODE" --width "$TARGET_WIDTH" --height "$TARGET_HEIGHT"

    # Step 5: Encode images with the corresponding result type based on the mode
    echo "Running encoding.py on result/${SAMPLE_NAME##*/}/$MODEL_TYPE/$RESULT_TYPE..."
    python encoding.py "result/${SAMPLE_NAME##*/}/$MODEL_TYPE/$RESULT_TYPE" --mode "$MODE"

    echo "Completed processing for directory: $SAMPLE_NAME"
done

echo "Pipeline execution completed for all directories."
sleep 3
