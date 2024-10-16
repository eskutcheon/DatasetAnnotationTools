import os
import json
import argparse
import vlc
# vlc docs: https://www.olivieraubert.net/vlc/python-ctypes/doc/vlc.Instance-class.html
import time
import numpy as np
from dataclasses import dataclass, asdict
from tqdm import tqdm


MAX_NUM_FRAMES = 1000

@dataclass
class Ripper:
    """ dataclass for storing the parameters of the frame extraction process """
    vid_path: str
    frames_path: str
    num_frames: int
    start_time: int
    end_time: int
    time_step: int
    duration: int


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
    parser.add_argument('--start_time', type=float, default=0, help='start time in milliseconds')
    parser.add_argument('--end_time', type=float, default=None, help='end time in milliseconds')
    parser.add_argument('--time_step', type=float, default=1000, help='time step between extracted frames in milliseconds')
    return parser.parse_args()

def sanitize_inputs(args: argparse.Namespace, vid_duration: int) -> Ripper:
    """ input namespace from above parser and output sanitized inputs in a dataclass """
    def bound_times(val, t1, t2):
        #bounded_times = int(np.clip([val], t1, t2).astype(int)[0])
        #print(f"times t1={t1} and t2={t2} bounded to {bounded_times}")
        return int(np.clip([val], t1, t2).astype(int)[0])

    # ? NOTE: all times are in milliseconds
    # initialize the dataclass with the parser (converted to dict then unpacked) then sanitize its values
    params = Ripper(**vars(args), duration=vid_duration)
    # adjusting vid_duration slightly so that extract_frames can read the last frame index - had to experiment w/ this
    vid_duration -= 1 # time in milliseconds formatted as an int
    # if the start time is somehow negative or greater than the actual video duration, clip to correct interval
    params.start_time = bound_times(params.start_time, 0, vid_duration)
    # if end_time not specified, set to end of video, else clip to correct interval
    if params.end_time is None:
        params.end_time = vid_duration
    else:
        params.end_time = bound_times(params.end_time, 0, vid_duration)
    if params.end_time <= params.start_time:
        raise ValueError(f"end_time cannot be less than the start time; got {params.end_time} and {params.start_time}, respectively")
    # duration of interval meant to be read may be different than vid_duration
    read_duration = params.end_time - params.start_time
    if params.num_frames is None:
        # if num_frames wasn't specified and time_step is given
        if params.time_step > read_duration:
            # time_step must be at most end-start with at least 2 frames
            params.time_step = bound_times(params.time_step, 10, read_duration)
            print(f"time step not in range; adjusting to time_step={params.time_step}")
        params.num_frames = min(int(read_duration/params.time_step) + 1, MAX_NUM_FRAMES)
    else:
        # if num_frames was specified, assume it takes precedence over any specified time_step
        params.num_frames = bound_times(params.num_frames, 2, MAX_NUM_FRAMES)
    # FIXME: messed up the logic a little so that time_step changes whether it's valid or not - num_frames works though
    params.time_step = int(read_duration/(params.num_frames - 1)) if params.num_frames > 1 else read_duration
    print(f"Number of frames to be extracted: {params.num_frames} (with time step {params.time_step/1000} seconds)")
    return params


def get_video_duration(vid_path: str) -> int:
    """ get the duration of the video in milliseconds """
    # initialize VLC instance without console output
    #print(vid_path)
    instance = vlc.Instance('--quiet', '--no-video-title-show', '--intf', 'dummy')
    media = instance.media_new(vid_path)
    #media = instance.media_new_path(vid_path)
    media.parse_with_options(vlc.MediaParseFlag.network, -1)
    while not media.is_parsed():
        time.sleep(0.1)
    duration = media.get_duration()
    if duration == -1 or duration == 0:
        raise ValueError("Could not retrieve video duration.")
    return duration


def extract_frames(ripper: Ripper):
    """ extract frames from the video and save them to the specified directory """
    # initialize VLC instance without console output
    # add '--no-xlib' to suppress window appearing
    instance = vlc.Instance('--quiet', '--no-video-title-show', '--intf', 'dummy')
    player = instance.media_player_new()
    media = instance.media_new(ripper.vid_path)
    player.set_media(media)
    # start the player with 1 second delay
    player.play()
    time.sleep(1)
    # get frame indices to extract
    # FIXME: need to change the logic for dealing with either a time step or a constant number of frames to use
    frame_times = np.arange(ripper.start_time, ripper.end_time + 1, step=ripper.time_step)
    #time_step_s = ripper.time_step/1000 # was going to use this for the new sleep time, but I'm not sure if that's actually causing the stuttering problem or not
    print(f"start: {ripper.start_time/1000}s, end: {ripper.end_time/1000}s, step size: {ripper.time_step/1000}s")
    with tqdm(total=ripper.num_frames, desc="Iterating over frames") as pbar:
        for idx, frame_time in enumerate(frame_times):
            frame_filepath = os.path.join(ripper.frames_path, f"frame_{frame_time}.png")
            # seek to the specific time
            player.set_time(frame_time)
            time.sleep(1)  # giving 1 second for the frame to render
            frame = player.video_take_snapshot(0, frame_filepath, 0, 0)
            pbar.update()
            if frame == -1: # player.video_get_snapshot returns -1 as error code
                print(f"Error: Could not extract frame at {frame_time} seconds")
                continue
    player.stop()
    print(f"FINISHED: Frames extracted and saved to {ripper.frames_path}")

# borrowed from main project's utils
def get_matching_filenames(input_dir, substr):
    """ get all filenames in a directory that contain a substring """
    return list(filter(lambda x: (substr in x) and (not os.path.isdir(os.path.join(input_dir, x))), os.listdir(input_dir)))

if __name__ == "__main__":
    args: argparse.Namespace = read_cli()
    ### handle file existence, path creation, and confirmation of path existences
    if not os.path.exists(args.vid_path) or not os.path.isfile(args.vid_path):
        raise FileNotFoundError(f"Couldn't find the file at {args.vid_path}")
    # set default directory value
    if args.frames_path is None:
        args.frames_path = os.path.join(os.path.dirname(args.vid_path), "frames")
    # create inner frames directory in the video directory - shouldn't exist by default unless you're re-running it
    if not os.path.exists(args.frames_path):
        os.makedirs(args.frames_path)
    elif len(os.listdir(args.frames_path)) > 0:
        print(f"WARNING: directory '{args.frames_path}' already exists with {len(os.listdir(args.frames_path))} files.")
        if not get_user_confirmation("Continue anyway?"):
            raise KeyboardInterrupt("program terminated by user")
    ### handle the actual frame extraction process
    duration: int = get_video_duration(args.vid_path)
    ripper: Ripper = sanitize_inputs(args, duration)
    # save parameters to JSON for documentation
    metadata_path: str = os.path.join(os.path.dirname(args.vid_path), "frame_rip_metadata.json")
    if os.path.exists(metadata_path):
        filename_base = os.path.splitext(os.path.basename(metadata_path))[0]
        parent_dir = os.path.dirname(metadata_path)
        new_filename = f"{filename_base}_{len(get_matching_filenames(parent_dir, filename_base)) + 1}.json"
        metadata_path = os.path.join(parent_dir, new_filename)
    with open(metadata_path, 'w') as fptr:
        json.dump(asdict(ripper), fptr, indent=4)
    extract_frames(ripper)

# ? NOTE: still don't have access to FFMPEG since IT is kinda incompetent