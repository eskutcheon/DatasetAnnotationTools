import os
import argparse
from tqdm import tqdm
import torch
import torchvision.io as IO
import torchvision.transforms.v2 as TT

# borrowed from the main repo just in case there's danger of redownloading a bunch
def get_user_confirmation(prompt):
    answers = {'y': True, 'n': False}
    # ! WARNING: walrus operator below only works in Python 3.8+
    while (response := input(f"{prompt} [Y/n] ").lower()) not in answers:
        print("Invalid input. Please enter 'y' or 'n' (not case sensitive).")
    return answers[response]

def read_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crop all images in a directory to a specified size according to offset from the bottom edge.")
    parser.add_argument('dir_path', type=str, help='path to frame directory')
    parser.add_argument('--top_offset', type=int, default=None, help='vertical offset (essentually the amount to trim from the top)')
    parser.add_argument('--bottom_offset', type=int, default=None, help='vertical offset (essentually the amount to trim from the bottom)')
    parser.add_argument('--brightness_mult', type=float, default=None, help='brightness factor to scale brightness by (<1.0 darkens, >1.0 brightens)')
    return parser.parse_args()



if __name__ == "__main__":
    args: argparse.Namespace = read_cli()
    ### handle file existence, path creation, and confirmation of path existences
    if not os.path.exists(args.dir_path):
        raise FileNotFoundError(f"Couldn't find the directory at {args.dir_path}")
    if not os.path.isdir(args.dir_path):
        raise NotADirectoryError(f"{args.dir_path} is not a directory.")
    # adding a check because I keep screwing up frames when giving the wrong path and want a warning each time
    _ = get_user_confirmation(f"Processing {args.dir_path}. Continue?")
    transforms = []
    if args.top_offset is not None or args.bottom_offset is not None:
        if args.top_offset is None:
            args.top_offset = 0
        if args.bottom_offset is None:
            args.bottom_offset = 0
        transforms.append(TT.Lambda(lambda x: x[:, args.top_offset:(x.shape[1] - args.bottom_offset)]))
    if args.brightness_mult is not None:
        transforms.append(TT.ToDtype(torch.float32, scale=True))
        transforms.append(TT.Lambda(lambda x: TT.functional.adjust_brightness(x, args.brightness_mult).clip(0,1)))
        transforms.append(TT.ToDtype(torch.uint8, scale=True))
    postprocessor = TT.Compose(transforms)
    # get all image filenames in the directory
    file_paths = [os.path.join(args.dir_path, p) for p in os.listdir(args.dir_path)]
    file_paths = list(filter(lambda x: not os.path.isdir(x), file_paths))
    with tqdm(total=len(file_paths), desc="Processing images") as pbar:
        for path in file_paths:
            pbar.set_description(f"processing {os.path.basename(path)}", refresh=False)
            img = IO.read_image(path, IO.ImageReadMode.RGB)
            img = postprocessor(img)
            IO.write_png(img, path, compression_level=3)
            #print(img.unique())
            pbar.update()