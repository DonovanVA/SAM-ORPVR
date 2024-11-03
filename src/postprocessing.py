import os
import shutil
import argparse
import time

def move_directories(src_folder, name):
    # Create the target directory with the timestamp
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    target_folder = os.path.join(os.path.dirname(src_folder), "runs", f"{name}-{timestamp}")

    # List of directories to move
    directories_to_move = [
        "harmonize",
        "cropped",
        "dataset",
        "result",
        "result_inpaint",
        "video",
        "videoHarmonized",
        "videoHarmonizedMOV",
        "videoMOV"
    ]

    # Create the target directory
    os.makedirs(target_folder, exist_ok=True)

    for directory in directories_to_move:
        src_dir = os.path.join(src_folder, directory)
        if os.path.exists(src_dir) and os.path.isdir(src_dir):
            # Move the directory
            shutil.move(src_dir, target_folder)
            print(f"Moved: {src_dir} to {target_folder}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Move specified directories to a runs folder.")
    parser.add_argument("--name", type=str, required=True, help="Name for the runs folder.")
    args = parser.parse_args()

    # Get the current directory (where the script is located)
    src_folder = os.path.dirname(os.path.abspath(__file__))
    
    move_directories(src_folder, args.name)