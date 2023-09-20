import os
import cv2
import numpy as np
import argparse
import logging
from shutil import copy2
from collections import defaultdict

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_mask_images(folder_path):
    """Load grayscale images from the specified folder based on the base file name."""
    images = []
    for filename in os.listdir(folder_path):
        img = cv2.imread(os.path.join(folder_path, filename), cv2.IMREAD_GRAYSCALE)
        if img is not None:
            images.append(img)
        else:
            logging.warning(f"Failed to read image: {filename}")
    return images

def copy_corresponding_files(corresponding_files_dir, output_dir, filename_base):
    """Copy files that correspond to the mask based on the filename."""
    for file in os.listdir(corresponding_files_dir):
        if file.startswith(filename_base):
            source_file_path = os.path.join(corresponding_files_dir, file)
            destination_file_path = os.path.join(output_dir, file)
            copy2(source_file_path, destination_file_path)
            logging.info(f"Copied corresponding file: {file}")

def combine_masks(mask_images):
    """Combine multiple mask images into a single image with distinct object IDs."""
    height, width = mask_images[0].shape
    combined_mask = np.zeros((height, width), dtype=np.uint16)
    object_id = 1
    
    for mask in mask_images:
        indices = np.where(mask > 0)
        combined_mask[indices] = object_id
        object_id += 1

    return combined_mask

def create_directory(directory_path):
    """Create a directory if it does not exist."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        logging.info(f"Created directory: {directory_path}")

def split_data(directory_path, val_pattern, test_pattern):
    """Split data into train, validation, and test sets based on specific string patterns."""
    data = defaultdict(list)

    for dirname in os.listdir(directory_path):
        if val_pattern in dirname:
            data["valid"].append(os.path.join(directory_path, dirname))
        elif test_pattern in dirname:
            data["test"].append(os.path.join(directory_path, dirname))
        else:
            data["train"].append(os.path.join(directory_path, dirname))

    return data

def process_masks(input_path, output_dir, corresponding_files_dir, val_pattern, test_pattern, format, exclude_class=["Unidentified"]):
    """Process and save combined mask images."""
    if not os.path.exists(input_path):
        logging.error(f"The input path {input_path} does not exist.")
        return
    
    # Split data into train, validation, and test sets
    data = split_data(input_path, val_pattern, test_pattern)
    
    # Process and save combined masks for each split
    for split_name, split_files in data.items():

        for dirpath in split_files:

            filename_base = os.path.basename(dirpath)

            all_masks = []
            all_masks_output_dir = os.path.join(output_dir, format, "all", split_name)
            create_directory(all_masks_output_dir)
            logging.info(f"Processing {dirpath}...")
            
            for class_name in os.listdir(dirpath):
                
                if class_name in exclude_class:
                    logging.info(f"Skipping {class_name}...")
                    continue

                mask_images = load_mask_images(os.path.join(dirpath, class_name))
                class_masks = combine_masks(mask_images)
                all_masks.extend(class_masks)

                # Create output directory structure: output_dir/class_name/split_name
                output_dir_class_split = os.path.join(output_dir, format, class_name, split_name)
                create_directory(output_dir_class_split)

                save_filepath = os.path.join(output_dir_class_split, f"{filename_base}_masks.{format}")
                cv2.imwrite(save_filepath, class_masks)
                logging.info(f"Combined mask image saved as {save_filepath}")

                # Copy the corresponding files based on the filename of the mask
                copy_corresponding_files(corresponding_files_dir, output_dir_class_split, filename_base)

            combined_mask = combine_masks(mask_images)
            save_filepath = os.path.join(all_masks_output_dir, f"{filename_base}_masks.{format}")
            cv2.imwrite(save_filepath, combined_mask)
            logging.info(f"Combined mask image saved as {save_filepath}")

            # Copy the corresponding files based on the filename of the mask
            copy_corresponding_files(corresponding_files_dir, all_masks_output_dir, filename_base)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process and combine mask images.')
    parser.add_argument('-i', '--input_path', type=str, help='Path to the input directory containing mask images.')
    parser.add_argument('-o', '--output_dir', type=str, help='Path to the output directory to save combined masks.')
    parser.add_argument('-c', '--corresponding_files_dir', type=str, help='Path to the directory containing files corresponding to the masks.')
    parser.add_argument('-v', '--val_pattern', type=str, default='ST_I06', help='String pattern to identify validation files.')
    parser.add_argument('-t', '--test_pattern', type=str, default='ST_K07', help='String pattern to identify test files.')
    parser.add_argument('-f', '--format', type=str, default='png', help='File formats to save the masks.')
    
    args = parser.parse_args()

    setup_logging()

    if os.path.exists(args.output_dir):
        logging.error(f"The output path {args.output_dir} already exists.")
        exit()
        
    process_masks(args.input_path, args.output_dir, args.corresponding_files_dir, args.val_pattern, args.test_pattern, args.format)