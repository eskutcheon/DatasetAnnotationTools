import os
import argparse
import vlc
# vlc docs: https://www.olivieraubert.net/vlc/python-ctypes/doc/vlc.Instance-class.html
import time
import numpy as np
from dataclasses import dataclass
from PIL import Image


MAX_NUM_FRAMES = 1000

@dataclass
class Ripper:
    vid_path: str
    frames_path: str
    num_frames: int
    start_time: float
    end_time: float
    time_step: float


# borrowed from the main repo just in case there's danger of redownloading a bunch
def get_user_confirmation(prompt):
    answers = {'y': True, 'n': False}
    # ! WARNING: walrus operator below only works in Python 3.8+
    while (response := input(f"{prompt} [Y/n] ").lower()) not in answers:
        print("Invalid input. Please enter 'y' or 'n' (not case sensitive).")
    return answers[response]

def read_cli():
    parser = argparse.ArgumentParser(description="Extract frames from a video using VLC.")
    parser.add_argument('vid_path', type=str, help='path to the video file')
    parser.add_argument('--frames_path', type=str, default=None, help='destination path for frames')
    parser.add_argument('--num_frames', type=int, default=None, help='total number of frames to extract')
    parser.add_argument('--start_time', type=float, default=0, help='start time in seconds')
    parser.add_argument('--end_time', type=float, default=None, help='end time in seconds')
    parser.add_argument('--time_step', type=float, default=1, help='time step between extracted frames in seconds')
    return parser.parse_args()

def sanitize_inputs(args: argparse.Namespace, vid_duration) -> Ripper:
    """ input namespace from above parser and output sanitized inputs in a dataclass """
    params = Ripper(**vars(args)) # initialize the dataclass with the parser then sanitize its values
    # if the start time is somehow negative or greater than the actual video duration, reset to 0
    if vid_duration <= params.start_time < 0:
        params.start_time = 0
    # same boundary checks as above and ensuring initialization besides NoneType, defaults to the end of the video
    if params.end_time is None or params.end_time < 0 or params.end_time > vid_duration:
        params.end_time = vid_duration
    # time_step must be at most end-start for 1-2 frames total
    if params.time_step > abs(params.end_time - params.start_time):
        params.time_step = int(params.end_time - params.start_time)
    # else if time step is negative, reset it to 0 - might change this to just get absolute value, but then the above needs to be changed
    elif params.time_step < 0:
        params.time_step = 1
    # if num_frames is set
    if params.num_frames is not None:
        pass
    else:
        if params.time_step == 1:
            params.num_frames = min(MAX_NUM_FRAMES, vid_duration)


def extract_frames(args):
    # initialize VLC instance
    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(args.vid_path)
    duration = media.get_duration()/1000
    ripper = sanitize_inputs(args, duration)
    player.set_media(media)
    # start the player with 1 second delay
    player.play()
    time.sleep(1)
    
    # get frame indices to extract
    # FIXME: need to change the logic for dealing with either a time step or a constant number of frames to use
    if ripper.time_step is not None:
        frame_times = np.arange(ripper.start_time, ripper.end_time, ripper.time_step)
    else:
        frame_times = np.linspace(ripper.start_time, ripper.end_time, ripper.num_frames)
    for idx, frame_time in enumerate(frame_times):
        # seek to the specific time
        player.set_time(int(frame_time * 1000))
        time.sleep(1)  # giving 1 second for the frame to render
        frame = player.video_get_snapshot(0, os.path.join(ripper.frames_path, f"frame_{idx:05d}.png"), 0, 0)
        if frame == -1:
            print(f"Error: Could not extract frame at {frame_time} seconds")
            continue
    player.stop()
    print(f"Frames extracted and saved to {ripper.frames_path}")



if __name__ == "__main__":
    args = read_cli()
    if args.frames_path is None:
        args.frames_path = os.path.join(os.path.dirname(args.vid_path), "frames")
    # create inner frames directory in the video directory - shouldn't exist by default unless you're re-running it
    # not sure yet if I want to move this to sanitize_input
    if not os.path.exists(args.frames_path):
        os.makedirs(args.frames_path)
    else:
        print(f"WARNING: directory '{args.frames_path}' already exists with {len(os.listdir(args.frames_path))} files.")
        if not get_user_confirmation("Continue anyway?"):
            raise KeyboardInterrupt("program terminated by user")
    extract_frames(args.vid_path, args.frames_path, args.num_frames, args.start_time, args.end_time, args.time_step)



# ? NOTE: still don't have access to FFMPEG since IT is kinda incompetent