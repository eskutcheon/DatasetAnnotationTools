import os

""" used this script to rename all the frames in the subdirectories of the root directory that already existed - made it easier to keep track of which frames belonged to which video """

def rename_frames_in_subdirs(root_dir):
    # Iterate over all subdirectories within the root directory
    for subdir in os.listdir(root_dir):
        subdir_path = os.path.join(root_dir, subdir)
        
        # Ensure we're dealing with a directory
        if os.path.isdir(subdir_path):
            frames_dir = os.path.join(subdir_path, 'frames')
            
            # Check if the 'frames' subdirectory exists
            if os.path.exists(frames_dir) and os.path.isdir(frames_dir):
                print(f"Processing frames in: {frames_dir}")
                
                # Iterate over all files in the frames directory
                for filename in os.listdir(frames_dir):
                    file_path = os.path.join(frames_dir, filename)
                    
                    # Check if it's a file (could add more checks for image types if needed)
                    if os.path.isfile(file_path):
                        # Construct the new file name with the prefix
                        prefix = f"{subdir}_"
                        # Skip renaming if the file already has the correct prefix
                        if filename.startswith(prefix):
                            print(f"Skipping {filename}, already renamed.")
                            continue
                        
                        new_filename = f"{prefix}{filename}"
                        new_file_path = os.path.join(frames_dir, new_filename)
                        
                        # Rename the file
                        os.rename(file_path, new_file_path)
                        print(f"Renamed {filename} to {new_filename}")

if __name__ == "__main__":
    # Replace 'your_directory_path' with the path to your root directory
    root_directory = r"C:\Users\Jacob\Documents\MSU Thesis Work\dirtydashcams"
    rename_frames_in_subdirs(root_directory)
