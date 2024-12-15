import logging
import os
from pdf2image import convert_from_path
from PIL import Image
import numpy as np
from tqdm import tqdm
from datetime import datetime
import ast
import tkinter as tk
from tkinter import simpledialog
from tkinter import messagebox


# Configure the logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def hex_to_rgb(hex_color):
    """
    Convert HEX color code (e.g., #RRGGBB) to RGB tuple (R, G, B).
    """
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]
    
    if len(hex_color) == 6:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    else:
        raise ValueError(f"Invalid HEX color code: {hex_color}")


def replace_color(image, target_color, tolerance=50):
    """
    Replace a specific color in the image with white, given a tolerance range.
    """
    logging.info("Starting color replacement process.")
    img = image.convert("RGBA")
    data = np.array(img)
    
    lower_bound = np.array([max(0, c - tolerance) for c in target_color])
    upper_bound = np.array([min(255, c + tolerance) for c in target_color])
    
    mask = np.all(np.logical_and(data[..., :3] >= lower_bound, data[..., :3] <= upper_bound), axis=-1)
    data[mask] = [255, 255, 255, 255]  # White
    image_with_replacement = Image.fromarray(data)
    
    logging.info(f"Color replacement completed for image with target color {target_color}.")
    return image_with_replacement


def convert_pdf_to_jpg(input_pdf_path):
    """
    Convert a PDF to JPG images with a progress bar.
    """
    images = convert_from_path(input_pdf_path, dpi=300)
    for i in tqdm(range(len(images)), desc="Converting PDF to Images", unit="page"):
        logging.info(f"Page {i + 1} converted to image.")
    return images


def save_image(image, output_folder, image_counter):
    """
    Save the processed image as a JPG file.
    """
    image_rgb = image.convert("RGB")  # Convert RGBA to RGB (removes alpha channel)
    output_image_path = os.path.join(output_folder, f"page_{image_counter}.jpg")
    image_rgb.save(output_image_path, "JPEG")
    logging.info(f"Processed image {image_counter} saved to {output_image_path}")


def process_pdf(input_pdf_path, output_folder, target_color=(0, 0, 0), tolerance=50):
    """
    Full process: Convert PDF to JPGs, replace color, and save the images in the output folder.
    """
    images = convert_pdf_to_jpg(input_pdf_path)
    image_counter = 1  # Start from image 1
    for image in tqdm(images, desc="Processing Pages", unit="page"):
        image_with_replaced_color = replace_color(image, target_color, tolerance)
        save_image(image_with_replaced_color, output_folder, image_counter)
        image_counter += 1


def process_multiple_pdfs(input_pdf_paths, output_folder, target_color=(0, 0, 0), tolerance=50):
    """
    Process multiple PDF files and save the output images in the specified output folder.
    """
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    image_counter = 1  # Counter to keep track of image names across all PDFs
    for input_pdf_path in input_pdf_paths:
        images = convert_pdf_to_jpg(input_pdf_path)
        for image in images:
            image_with_replacement = replace_color(image, target_color, tolerance)
            save_image(image_with_replacement, output_folder, image_counter)
            image_counter += 1


def read_pdf_list_from_txt(file_path):
    """
    Read a list of PDFs from a .txt file (with the format ['input1.pdf', 'input2.pdf', ...]).
    """
    with open(file_path, 'r') as file:
        pdf_list_str = file.read().strip()
    try:
        pdf_list = ast.literal_eval(pdf_list_str)
        if not isinstance(pdf_list, list):
            raise ValueError("The file content is not a valid list.")
    except (SyntaxError, ValueError) as e:
        logging.error(f"Error reading the list from the file: {e}")
        pdf_list = []
    return pdf_list


def open_ui():
    """
    Open a simple Tkinter UI to allow the user to set target color and tolerance.
    """
    def on_start_button_click():
        # Set default values for PDF list and output folder
        input_pdfs = read_pdf_list_from_txt("output.txt")  # Default PDF list file
        output_folder = "output_images"  # Default output folder
        
        # Get the color input
        color_input = color_entry.get().strip()
        
        try:
            # If the input starts with "#" it's HEX, otherwise it's assumed to be RGB
            if color_input.startswith('#'):
                target_color = hex_to_rgb(color_input)
            else:
                # Default to RGB input format
                target_color = tuple(map(int, color_input.split(',')))
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid color input: {e}")
            return
        
        # Get the tolerance value
        try:
            tolerance = int(tolerance_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid tolerance value.")
            return
        
        if input_pdfs:
            logging.info("Starting PDF processing for multiple files...")
            process_multiple_pdfs(input_pdfs, output_folder, target_color, tolerance)
            window.quit()  # Quit the application after completion
        else:
            messagebox.showerror("Error", "No valid PDF files found to process.")
    
    window = tk.Tk()
    window.title("Watermark remover tool")
    
    # Set window size to make it larger
    window.geometry("500x400")  # Width x Height

    # Color input instructions
    tk.Label(window, text="Enter Watermark Color (HEX or RGB):", font=("Arial", 12)).pack(pady=10)
    
    # Entry field for color (either HEX or RGB)
    color_entry = tk.Entry(window, width=20, font=("Arial", 14))
    color_entry.insert(0, "#000000")  # Default HEX value (black)
    color_entry.pack(pady=5)

    # Input for the tolerance
    tk.Label(window, text="Tolerance:", font=("Arial", 12)).pack(pady=10)
    tolerance_entry = tk.Entry(window, width=10, font=("Arial", 14))
    tolerance_entry.insert(0, "50")
    tolerance_entry.pack(pady=10)

    # Start button
    start_button = tk.Button(window, text="Start Processing", font=("Arial", 14), command=on_start_button_click)
    start_button.pack(pady=20)

    # User shouldn't close instruction
    tk.Label(window, text="This window might look freezed,it's normal", font=("Arial", 12)).pack(pady=10)
    tk.Label(window, text="DON'T CLOSE IT,it will close itself", font=("Arial", 12)).pack(pady=10)


    window.mainloop()

def run():
    open_ui()

if __name__ == "__main__":
    run()