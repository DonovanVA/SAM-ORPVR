#!/bin/bash

# Ensure correct number of arguments
if [ "$#" -lt 3 ]; then
  echo "Usage: $0 <parent_directory> <model_type> <mode> [--no-mask-model]"
  echo "Model types: aotgan, e2fgvi, e2fgvi_hq"
  echo "Modes: 0 (original), 1 (offset), 2 (dynamic)"
  exit 1
fi

# Assign variables from arguments
PARENT_DIR="$1"  # This can now be a relative path
MODEL_TYPE="$2"
MODE="$3"

# Optional flag for no-mask-model
NO_MASK_MODEL=0
HAS_MASK_MODEL="has-0model"
if [ "$#" -eq 4 ] && [ "$4" == "--no-mask-model" ]; then
  NO_MASK_MODEL=1
  HAS_MASK_MODEL="no-model"
fi

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
    echo "Processing directory: $SAMPLE_NAME" # SAMPLE_NAME:"...DAVIS-test\JPEGImages\480p\bmx-bumps"
    echo "Annotation directory: $ANNOTATION_NAME" # ANNOTATION_NAME: "...DAVIS-test\Annotations\480p\bmx-bumps"
    # Step 1: Crop images
    echo "Running crop.py on $SAMPLE_NAME..."
    python crop.py "$SAMPLE_NAME" --width 640 --height 480 --mode 0

    # Step 2: Run masking only if --no-mask-model flag is NOT provided
    if [ "$NO_MASK_MODEL" -eq 1 ]; then
        echo "No mask model is selected, cropping mask..."
        python crop.py "$ANNOTATION_NAME" --width 640 --height 480 --mode 1
        echo "Running masking.py without model on cropped/${SAMPLE_NAME##*/}/masks..."
        python masking.py "dataset/${SAMPLE_NAME##*/}/masks" --mode 1 
    else
        echo "Running masking.py with model on cropped/${SAMPLE_NAME##*/}..."
        python masking.py "cropped/${SAMPLE_NAME##*/}" --mode 0
    fi

    #Step 3: Inpaint images using the specified model
    echo "Running inpainting.py on dataset/${SAMPLE_NAME##*/} with model $MODEL_TYPE..."
    python inpainting.py "dataset/${SAMPLE_NAME##*/}" --model "$MODEL_TYPE"
    
    #Step 4: Relocate images using the specified mode
    echo "Running relocating.py on result_inpaint/${SAMPLE_NAME##*/}/$MODEL_TYPE with mode $MODE..."
    python relocating.py "result_inpaint/${SAMPLE_NAME##*/}/$MODEL_TYPE" --mode "$MODE"

    #Step 5: Encode images with the corresponding result type based on the mode
    echo "Running encoding.py on result/${SAMPLE_NAME##*/}/$MODEL_TYPE/$RESULT_TYPE..."
    python encoding.py "result/${SAMPLE_NAME##*/}/$MODEL_TYPE/$RESULT_TYPE"

    echo "Completed processing for directory: $SAMPLE_NAME"
done

echo "Pipeline execution completed for all directories."
