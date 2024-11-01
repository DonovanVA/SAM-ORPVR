import os
import argparse
import cv2

def convert_mp4_to_mov(parent_directory, target_directory):
    for root, dirs, files in os.walk(parent_directory):
        relative_path = os.path.relpath(root, parent_directory)
        output_directory = os.path.join(target_directory, relative_path)
        os.makedirs(output_directory, exist_ok=True)

        for file in files:
            if file.endswith('.mp4'):
                mp4_file_path = os.path.join(root, file)
                mov_file_path = os.path.join(output_directory, file.replace('.mp4', '.mov'))

                print(f'Converting: {mp4_file_path} to {mov_file_path}')
                
                # Open the video file with OpenCV
                cap = cv2.VideoCapture(mp4_file_path)
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Specify codec

                # Extract frame dimensions and FPS
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)

                # Define the video writer object
                out = cv2.VideoWriter(mov_file_path, fourcc, fps, (width, height))

                try:
                    while cap.isOpened():
                        ret, frame = cap.read()
                        if not ret:
                            break
                        out.write(frame)
                    print(f'Converted: {mp4_file_path} to {mov_file_path}')
                except Exception as e:
                    print(f'Failed to convert {mp4_file_path}: {e}')
                finally:
                    cap.release()
                    out.release()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert MP4 files to MOV format.')
    parser.add_argument('parent_directory', type=str, help='The parent directory to search for MP4 files.')
    parser.add_argument('target_directory', type=str, help='The directory where converted MOV files will be stored.')

    args = parser.parse_args()
    convert_mp4_to_mov(args.parent_directory, args.target_directory)
