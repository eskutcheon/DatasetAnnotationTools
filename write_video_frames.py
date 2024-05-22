import torchvision,io as IO
import os
import sys


# !! DONT RUN THIS SCRIPT YET - NOT SAFE FOR LARGE VIDEOS
# in case nobody reads this:
print("NOT SAFE TO RUN - READ COMMENTS")
sys.exit(1)


allowed_ext = ["mp4", "avi", "mkv", "wmv", "mov"]
# video root directory - hardcoded to work at CAVS with Windows-style separators
video_dir = r"I:\projects\ARC\Project1.38\new_val_dataset\vids"
# get video ID as a command line argument that follows this file's name (need to double check the default indexing to make sure python isn't counted)
video_id = sys.argv[1]
# path to search for the video file
video_path = os.path.join(video_dir, video_id)
# if directory I:\projects\ARC\Project1.38\new_val_dataset\vids\{video_id} not found, throw error
if not os.path.isdir(video_path):
    raise NotADirectoryError(f"DIRECTORY '{video_path}' NOT FOUND")

# destination directory for the video frames - intended to be I:\projects\ARC\Project1.38\new_val_dataset\frames\{video_id}
new_frames_dir = os.path.abspath(os.path.join(video_dir, "..", "frames", video_id))
if not os.path.isdir(new_frames_dir):
    os.makedirs(new_frames_dir)

# read video into a 4D video tensor of shape (T,C,H,W) - returns only the frames, not audio or metadata also returned by read_video

def get_video_tensor():
    for dir_contents in os.listdir(video_path):
        if any([dir_contents == f"{video_id}.{ext}" for ext in allowed_ext]):
            # https://pytorch.org/vision/stable/generated/torchvision.io.read_video.html#torchvision.io.read_video
            frames, _, _ = IO.read_video(os.path.join(video_path, dir_contents), output_format="TCHW")
            return frames
    # if loop finished without returning a value, throw error
    raise FileNotFoundError(f"NO SUITABLE VIDEO FILE FOUND WITH PREFIX '{video_id}'")

frames = get_video_tensor()
# optional second command line argument following the video ID = number of frames you want to keep total; default is all of them
num_frames = sys.argv[2] if len(sys.argv) > 2 else frames.shape[0]
# sample interval - the total frames read divided by the number you want to keep
sample_int = frames.shape[0]//num_frames

# iterate over frames with specified sample interval, saving files as PNG named with left 0 padding for proper ordering
for idx in range(0, frames.shape[0], step=sample_int):
    filename = f"{str(idx).rjust(8, 0)}.png"
    IO.write_png(frames[idx], os.path.join(new_frames_dir, filename), compression_level=3)


