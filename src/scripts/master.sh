#!/bin/bash
cd ../src
# Ensure correct number of arguments
if [ "$#" -lt 3 ]; then
  echo "Usage: $0 <image_parent_directory> <model_type> <mode> [--no-mask-model] [--sam2-segment] [--harmonize] [--crop_to_width <crop_to_width>] [--crop_to_height <crop_to_height>] [--target_width <target_width>] [--target_height <target_height>]"
  echo "Model types: aotgan, e2fgvi, e2fgvi_hq"
  echo "Modes: 0 (original), 1 (offset), 2 (dynamic)"
  exit 1
fi

# Assign variables from arguments
PARENT_DIR="$1"  # This can now be a relative path
MODEL_TYPE="$2"
MODE="$3"

# Optional flags and parameters
NO_MASK_MODEL=0 #default is no mask model
SAM2_SEGMENT=0 # default is no sam2
HAS_MASK_MODEL="m2f"
HARMONIZE=0 # default is no harmonization
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
    --sam2-segment)
      SAM2_SEGMENT=1
      ;;
    --harmonize)
      HARMONIZE=1
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

## Use SAM2 to segment if the flag is set (SAM2)
if [ "$SAM2_SEGMENT" -eq 1 ]; then
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
        python crop.py "$SAMPLE_NAME" --width "$CROP_TO_WIDTH" --height "$CROP_TO_HEIGHT" --mode 0

        echo "Completed cropping for directory: $SAMPLE_NAME"
    done

    # Step 2: Run the sam2 script
    echo "Running SAM2 on the cropped images"
    python sam2/SAM2segmenter.py cropped
    echo "Cropping completed for all directories."
    echo "Completed..."
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

    # Step 1 and Step 2: Crop and mask images without SAM2 (default)
    if [ "$SAM2_SEGMENT" -eq 0 ]; then
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

    # Step 3: Inpaint images using the specified model
    echo "Running inpainting.py on dataset/${SAMPLE_NAME##*/} with model $MODEL_TYPE..."
    python inpainting.py "dataset/${SAMPLE_NAME##*/}" --model "$MODEL_TYPE"
    
    # Step 4: Relocate images using the specified mode
    echo "Running relocating.py on result_inpaint/${SAMPLE_NAME##*/}/$MODEL_TYPE with mode $MODE... to width $TARGET_WIDTH and height $TARGET_HEIGHT"
    python relocating.py "result_inpaint/${SAMPLE_NAME##*/}/$MODEL_TYPE" --mode "$MODE" --width "$TARGET_WIDTH" --height "$TARGET_HEIGHT"

    
    if [ "$HARMONIZE" -eq 0 ]; then
        # Step 5: Encode images with the corresponding result type based on the mode
        echo "Running encoding.py on result/${SAMPLE_NAME##*/}/$MODEL_TYPE/$RESULT_TYPE..."
        python encoding.py "result/${SAMPLE_NAME##*/}/$MODEL_TYPE/$RESULT_TYPE"
        
    fi
done

if [ "$HARMONIZE" -eq 1 ]; then
    # Step 5: Harmonize the images before converting to video
    # Prepare for harmonizer
    echo "Running prepforharmonizer.py to prepare for harmonization with mode $MODE... to width $TARGET_WIDTH and height $TARGET_HEIGHT"
    python prepforharmonizer.py result --mode "$MODE" --width "$TARGET_WIDTH" --height "$TARGET_HEIGHT"

    # Navigate to the harmonized directories and run harmonization
    for HARMONIZE_DIR in harmonize/*/; do  # The trailing slash ensures we only get directories
        echo "Processing directory: $HARMONIZE_DIR"
        
        # Navigate to the Harmonizer directory
        cd Harmonizer || exit  # Exit if we can't navigate to Harmonizer

        # Run the harmonization
        echo "Running harmonization on $HARMONIZE_DIR..."
        python -m demo.image_harmonization.run --example-path "../$HARMONIZE_DIR"
        
        # Navigate back to the parent directory
        cd .. || exit

        # Run encoding on harmonized images
        echo "Running encoding.py on ${HARMONIZE_DIR}harmonized..."
        python encoding.py "${HARMONIZE_DIR}harmonized" --harmonize

        # Optional delay between iterations
        echo "Completed harmonisation for ${HARMONIZE_DIR}harmonized...proceeding to the next image set"
    done
fi

NAME_PREFIX="sam2"
if [ "$SAM2_SEGMENT" -eq 0 ]; then
    NAME_PREFIX="$HAS_MASK_MODEL"
fi
NAME="${NAME_PREFIX}_${HARMONIZE}_${CROP_TO_WIDTH}x${CROP_TO_HEIGHT}to${TARGET_WIDTH}x${TARGET_HEIGHT}"

##  Step 6: Postprocessing
python postprocessing.py --name "$NAME"

echo "Pipeline execution completed for all directories."
sleep 3
