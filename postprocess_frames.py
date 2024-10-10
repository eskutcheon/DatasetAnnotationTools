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
    parser.add_argument('--overwrite', action='store_true', help='overwrite the original images')
    parser.add_argument('--top_offset', type=int, default=None, help='vertical offset (essentually the amount to trim from the top)')
    parser.add_argument('--bottom_offset', type=int, default=None, help='vertical offset (essentually the amount to trim from the bottom)')
    parser.add_argument('--brightness_mult', type=float, default=None, help='brightness factor to scale brightness by (<1.0 darkens, >1.0 brightens)')
    parser.add_argument('--undo_motion_blur', action='store_true', help='undo motion blur')
    return parser.parse_args()

def wiener_filter(blurred_img, kernel, K=0.01):
    blurred_fft = torch.fft.fft2(blurred_img)
    kernel_fft = torch.fft.fft2(kernel, s=blurred_img.shape[-2:])
    kernel_fft_conj = torch.conj(kernel_fft)
    denominator = torch.abs(kernel_fft) ** 2 + K
    restored_fft = blurred_fft * kernel_fft_conj / denominator
    restored_img = torch.fft.ifft2(restored_fft).real
    return restored_img


if __name__ == "__main__":
    args: argparse.Namespace = read_cli()
    ### handle file existence, path creation, and confirmation of path existences
    if not os.path.exists(args.dir_path):
        raise FileNotFoundError(f"Couldn't find the directory at {args.dir_path}")
    if not os.path.isdir(args.dir_path):
        raise NotADirectoryError(f"{args.dir_path} is not a directory.")
    # adding a check because I keep screwing up frames when giving the wrong path and want a warning each time
    _ = get_user_confirmation(f"Processing {args.dir_path}. Continue?")
    dest_dir = os.path.join(args.dir_path, 'processed')
    os.makedirs(dest_dir, exist_ok=True)
    
    transforms = []
    if args.top_offset is not None or args.bottom_offset is not None:
        if args.top_offset is None:
            args.top_offset = 0
        if args.bottom_offset is None:
            args.bottom_offset = 0
        transforms.append(TT.Lambda(lambda x: x[:, args.top_offset:(x.shape[1] - args.bottom_offset)]))
    if args.undo_motion_blur:
        transforms.append(TT.Lambda(lambda x: wiener_filter(x, torch.tensor([[1, 4, 6, 4, 1], [4, 16, 24, 16, 4], [6, 24, 36, 24, 6], [4, 16, 24, 16, 4], [1, 4, 6, 4, 1]], dtype=torch.float32) / 256)))
    if args.brightness_mult is not None:
        transforms.append(TT.ToDtype(torch.float32, scale=True))
        transforms.append(TT.Lambda(lambda x: TT.functional.adjust_brightness(x, args.brightness_mult).clip(0,1)))
        transforms.append(TT.ToDtype(torch.uint8, scale=True))
    transforms.append(TT.ToDtype(torch.uint8, scale=True))
    postprocessor = TT.Compose(transforms)
    # get all image filenames in the directory
    file_paths = [os.path.join(args.dir_path, p) for p in os.listdir(args.dir_path)]
    file_paths = list(filter(lambda x: not os.path.isdir(x), file_paths))[:20]
    with tqdm(total=len(file_paths), desc="Processing images") as pbar:
        for path in file_paths:
            pbar.set_description(f"processing {os.path.basename(path)}", refresh=False)
            img = IO.read_image(path, IO.ImageReadMode.RGB)
            img = postprocessor(img)
            print(f"pixel value range for {os.path.basename(path)}: {img.min().item()} to {img.max().item()}")
            if args.overwrite:
                IO.write_png(img, path, compression_level=3)
            else:
                dest_path = os.path.join(dest_dir, os.path.basename(path))
                IO.write_png(img, dest_path, compression_level=2)
            #print(img.unique())
            pbar.update()