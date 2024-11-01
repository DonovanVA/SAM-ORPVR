#!/bin/bash
cd ../src
# Ensure the script is executed from the correct parent directory
if [ ! -d "Harmonizer" ]; then
    echo "Harmonizer directory not found. Please run this script from the correct parent directory."
    exit 1
fi
echo "Usage: $0 [--width <width>] [--height <height>]"
# Default values for width and height
WIDTH=854
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

# Prepare for harmonizer
echo "Running prepforharmonizer.py to prepare for harmonization with width $WIDTH and height $HEIGHT..."
python prepforharmonizer.py result --mode 0 --height "$HEIGHT" --width "$WIDTH"

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
    echo "Running encodingHarmonized.py on ${HARMONIZE_DIR}harmonized..."
    python encodingHarmonized.py "${HARMONIZE_DIR}harmonized"

    # Optional delay between iterations
    echo "Completed harmonisation for ${HARMONIZE_DIR}harmonized...proceeding to the next image set"
done

echo "Harmonization process completed for all directories."
sleep 3
