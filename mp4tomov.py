import os
import argparse
from moviepy.editor import VideoFileClip

def convert_mp4_to_mov(parent_directory):
    # Traverse through the directory
    for root, dirs, files in os.walk(parent_directory):
        # Create a corresponding output directory in videomov
        relative_path = os.path.relpath(root, parent_directory)
        output_directory = os.path.join("videomov", relative_path)

        # Create the output directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)

        for file in files:
            if file.endswith('.mp4'):
                mp4_file_path = os.path.join(root, file)
                # Create a corresponding path in the output directory
                mov_file_path = os.path.join(output_directory, file.replace('.mp4', '.mov'))

                print(f'Converting: {mp4_file_path} to {mov_file_path}')
                
                # Convert the video
                try:
                    with VideoFileClip(mp4_file_path) as video:
                        # Specify the codec as 'libx264' or 'libx265' for .mov files
                        video.write_videofile(mov_file_path, codec="libx264")
                    print(f'Converted: {mp4_file_path} to {mov_file_path}')
                except Exception as e:
                    print(f'Failed to convert {mp4_file_path}: {e}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert MP4 files to MOV format.')
    parser.add_argument('parent_directory', type=str, help='The parent directory to search for MP4 files.')

    args = parser.parse_args()

    convert_mp4_to_mov(args.parent_directory)


