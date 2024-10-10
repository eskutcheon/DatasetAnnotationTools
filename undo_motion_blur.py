import os
import cv2
import numpy as np
import numpy.fft as fft
from skimage.registration import optical_flow_tvl1
from skimage.filters import wiener


def load_images_from_directory(directory, num_frames=20):
    image_files = sorted([f for f in os.listdir(directory) if f.endswith('.png')],
                         key=lambda x: int(x.split('_')[-1].split('.')[0]))[:num_frames]  # Extract frame index
    print("number of files to use: ", len(image_files))
    images = []
    timestamps = []
    for idx, img_file in enumerate(image_files):
        img_path = os.path.join(directory, img_file)
        frame_index = int(img_file.split('_')[-1].split('.')[0])
        image = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)/255.0  # Load as grayscale
        print(f"image {idx} value range: {np.min(image), np.max(image)}")
        images.append(image)
        timestamps.append(frame_index)
    print("number of images to use: ", len(images))
    print("number of timestamps to use: ", len(timestamps))
    return images, timestamps


def estimate_motion_blur(images, timestamps, time_step=500):
    kernels = []
    for i in range(1, len(images)):
        # Only estimate flow between frames if within the 500ms window
        if timestamps[i] - timestamps[i-1] <= time_step:
            flow = optical_flow_tvl1(images[i-1], images[i], attachment=10, prefilter=True, num_iter=20)
            print("optical_flow_shape: ", flow.shape)
            print("optical flow values: ", np.min(flow), np.max(flow))
            # Normalize optical flow to [-1, 1] range
            flow_min, flow_max = np.min(flow), np.max(flow)
            flow = 2 * (flow - flow_min) / (flow_max - flow_min) - 1
            print("optical_flow_shape: ", flow.shape)
            print("optical flow values: ", np.min(flow), np.max(flow))
            #kernel_x = np.mean(flow[0], axis=0)
            #kernel_y = np.mean(flow[1], axis=0)
            #kernel = np.sqrt(kernel_x**2 + kernel_y**2)
            kernel = np.sqrt(flow[0]**2 + flow[1]**2)  # Combine flow in x and y
            print("kernel_shape: ", kernel.shape)
            print("kernel values: ", np.min(kernel), np.max(kernel))
            # Scale the kernel by the mean pixel intensity of the image
            # scale_factor = np.mean(images[i])
            # kernel *= scale_factor / np.mean(kernel)
            # Normalize the kernel so that it has similar intensity to the image
            #kernel_min, kernel_max = np.min(kernel), np.max(kernel)
            #kernel = (kernel - kernel_min) / (kernel_max - kernel_min) * 255  # Normalize to [0, 255]
            print(f"Kernel min/max values after scaling: {kernel.min()}, {kernel.max()}")
            kernels.append(kernel)
        else:
            # Use an identity kernel if no blur is detected
            kernels.append(np.ones((images[i].shape[0], images[i].shape[1])))
    return kernels


def wiener_filter(input_image, kernel, snr=1e-2):
    # pad_width = [(0, input_image.shape[0] - kernel.shape[0]), (0, input_image.shape[1] - kernel.shape[1])]
    # kernel_padded = np.pad(kernel, pad_width, mode='reflect')
    # # Compute Fourier transforms
    # if kernel.shape != input_image.shape:
    #     raise ValueError(f"Kernel shape {kernel.shape} does not match input image shape {input_image.shape}")
    # # Compute Fourier transforms after padding the kernel
    # image_fft = fft.fft2(input_image)
    # kernel_fft = fft.fft2(kernel_padded)
    # print(f"value range of image_fft: {image_fft.min()} {image_fft.max()}")
    # print(f"value range of kernel_fft: {kernel_fft.min()} {kernel_fft.max()}")
    # # Wiener filtering in frequency domain
    # kernel_abs = np.abs(kernel_fft) ** 2
    # denominator = kernel_abs + snr
    # wiener_filter = np.conj(kernel_fft) / denominator
    # result_fft = image_fft * wiener_filter
    # # Inverse Fourier transform to get the result
    # restored_image = np.real(fft.ifft2(result_fft))
    # Apply Wiener filtering directly using skimage
    restored_image = wiener(input_image, kernel, balance=1e-2)  # Adjust balance as needed
    return restored_image


def apply_kernels_to_images(images, kernels):
    restored_images = []
    for i in range(1, len(images)):
        restored_image = wiener_filter(images[i], kernels[i-1])
        #restored_image = (restored_image - np.min(restored_image))/(np.max(restored_image) - np.min(restored_image))
        restored_images.append(restored_image)
    return restored_images


def save_restored_images(images, timestamps, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for img, timestamp in zip(images, timestamps):
        output_path = os.path.join(output_dir, f"frame_{timestamp}.png")
        #print("img value range right before saving: ", np.min(img), np.max(img))
        #img = img.clip(0,1)
        print("img value range right before saving (after clipping): ", np.min(img), np.max(img))
        cv2.imwrite(output_path, np.clip(img, 0, 255).astype(np.uint8))


def process_image_directory(input_dir, output_dir, num_frames=20):
    # Step 1: Load images and their timestamps
    images, timestamps = load_images_from_directory(input_dir, num_frames)
    # Step 2: Estimate motion blur kernels based on timestamps
    kernels = estimate_motion_blur(images, timestamps, 2001)
    print("number of kernels: ", len(kernels))
    print("kernel value range: ", np.min(kernels), np.max(kernels))
    # Step 3: Apply the kernels to each image
    restored_images = apply_kernels_to_images(images, kernels)
    print("value range of restored images: ", np.min(restored_images), np.max(restored_images))
    # Step 4: Save the restored images
    save_restored_images(restored_images, timestamps, output_dir)


if __name__ == "__main__":
    input_dir = r"C:\Users\Jacob\Documents\DatasetAnnotationTools\videos\7GpUBRvRgdk\frames"
    output_dir = r"C:\Users\Jacob\Documents\DatasetAnnotationTools\videos\7GpUBRvRgdk\frames\processed"
    process_image_directory(input_dir, output_dir, 3)