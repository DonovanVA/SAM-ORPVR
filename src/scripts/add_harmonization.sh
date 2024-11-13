#!/bin/bash
cd ../src
# Ensure the script is executed from the correct parent directory
if [ ! -d "Harmonizer" ]; then
    echo "Harmonizer directory not found. Please run this script from the correct parent directory."
    exit 1
fi
echo "Usage: $0 [--width <width>] [--height <height>] [--mode <mode>]"
# Default values for width and height
WIDTH=854
HEIGHT=480
MODE=0
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
    --mode)
      shift
      MODE="$1"
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
  shift
done
# CSV output file
mkdir -p metrics
CSV_FILE="metrics/harmonization_metrics.csv"
# Add header to CSV file if it doesn't exist
if [ ! -f "$CSV_FILE" ]; then
    echo "ImageSetID,T_harmonize,T_encoding,T_wt,T_ht" > "$CSV_FILE"
fi
# Prepare for harmonizer
echo "Running prepforharmonizer.py to prepare for harmonization with width $WIDTH and height $HEIGHT..."
python prepforharmonizer.py result --mode "$MODE" --height "$HEIGHT" --width "$WIDTH"

# Navigate to the harmonized directories and run harmonization
for HARMONIZE_DIR in harmonize/*/; do  # The trailing slash ensures we only get directories
    DIR_NAME=$(basename "$HARMONIZE_DIR")  # Extract only the final directory name
    echo "Processing directory: $HARMONIZE_DIR"
    
    # Navigate to the Harmonizer directory
    cd Harmonizer || exit  # Exit if we can't navigate to Harmonizer

    # Run the harmonization
    echo "Running harmonization on $HARMONIZE_DIR..."
    START_TIME=$(date +%s)
    python -m demo.image_harmonization.run --example-path "../$HARMONIZE_DIR"
    END_TIME=$(date +%s)
    T_HARMONIZE=$((END_TIME - START_TIME))  # Calculate time taken for harmonization
    echo "Time taken for harmonization (Tharmonize) on $HARMONIZE_DIR: ${T_HARMONIZE}s"
    
    # Navigate back to the parent directory
    cd .. || exit

    # Run encoding on harmonized images
    echo "Running encoding.py on ${HARMONIZE_DIR}harmonized..."
    E_START_TIME=$(date +%s)
    python encoding.py "${HARMONIZE_DIR}harmonized" --mode "$MODE" --harmonize
    E_END_TIME=$(date +%s)
    T_ENCODING=$((E_END_TIME - E_START_TIME))
    # Append metrics to CSV file with WIDTH and HEIGHT columns
    echo "Completed harmonisation for ${DIR_NAME} harmonized...proceeding to the next image set, time taken: ${T_ENCODING}s"
    echo "${DIR_NAME},${T_HARMONIZE},${T_ENCODING},${WIDTH},${HEIGHT}" >> "$CSV_FILE"
done

echo "Harmonization process completed for all directories."
sleep 3
