#!/bin/bash

# Check if the main directory argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <main_directory>"
    exit 1
fi

# Define directories and CSV file
MAIN_DIR="$1"  # The main directory is now an argument
METRICS_DIR="metrics"
CSV_FILE="$METRICS_DIR/properties.csv"

# Create the metrics directory if it doesn't exist
mkdir -p "$METRICS_DIR"

# Add header to CSV file
> "$CSV_FILE"
echo "ImageSetID,N_frames" > "$CSV_FILE"

# Loop through each folder in the main directory
for FOLDER in "$MAIN_DIR"/*; do
    if [ -d "$FOLDER" ]; then
        FOLDER_NAME=$(basename "$FOLDER")  # Get the name of the folder

        # Count the number of images in the folder
        FRAME_COUNT=$(find "$FOLDER" -type f -iname '*.jpg' -o -iname '*.png' | wc -l)

        # Write data to CSV with the frame count for each image in this folder
        echo "$FOLDER_NAME,$FRAME_COUNT" >> "$CSV_FILE"
        echo "Processed $FOLDER_NAME has $FRAME_COUNT frames."
    fi
done

echo "Image properties written to $CSV_FILE."
