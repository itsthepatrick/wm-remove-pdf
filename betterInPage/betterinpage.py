import logging
import os
import ast
from pdf2image import convert_from_path
from PIL import Image
import numpy as np
from tqdm import tqdm
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk  # Import ttk for the progress bar


# Configure the logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BetterInpage:
    def __init__(self, root):
        self.root = root
        root.title("Watermark remover tool")
        # Set window size to make it larger
        root.geometry("500x800")  # Width x Height

        # Variable to track process completion
        self.process_done = False

        # Create UI elements
        self.create_widgets()

    def create_widgets(self):
        # Color input instructions (Target Color)
        tk.Label(self.root, text="Enter Watermark Color (HEX or RGB):", font=("Arial", 12)).pack(pady=10)
        self.color_entry = tk.Entry(self.root, width=20, font=("Arial", 14))
        self.color_entry.insert(0, "#000000")  # Default HEX value (black)
        self.color_entry.pack(pady=5)

        # Replacement color input instructions
        tk.Label(self.root, text="Enter Replacement Color (HEX or RGB):", font=("Arial", 12)).pack(pady=10)
        self.replacement_color_entry = tk.Entry(self.root, width=20, font=("Arial", 14))
        self.replacement_color_entry.insert(0, "#FFFFFF")  # Default HEX value (white)
        self.replacement_color_entry.pack(pady=5)

        # Input for the tolerance
        tk.Label(self.root, text="Tolerance:", font=("Arial", 12)).pack(pady=10)
        self.tolerance_entry = tk.Entry(self.root, width=10, font=("Arial", 14))
        self.tolerance_entry.insert(0, "50")
        self.tolerance_entry.pack(pady=10)

        # DPI input field
        tk.Label(self.root, text="Enter DPI for PDF Conversion:", font=("Arial", 12)).pack(pady=10)
        self.dpi_entry = tk.Entry(self.root, width=10, font=("Arial", 14))
        self.dpi_entry.insert(0, "150")  # Default DPI value
        self.dpi_entry.pack(pady=5)

        # Add a progress bar to the window(root)
        self.progress_bar = ttk.Progressbar(self.root, length=400, mode="determinate")
        self.progress_bar.pack(pady=20)

        # Start button
        self.start_button = tk.Button(self.root, text="Start Processing", font=("Arial", 14), command=self.on_start_button_click)
        self.start_button.pack(pady=20)

        # User shouldn't close instruction
        tk.Label(self.root, text="This window might look freezed, it's normal", font=("Arial", 12)).pack(pady=10)
        tk.Label(self.root, text="DON'T CLOSE IT, it will close itself", font=("Arial", 12)).pack(pady=10)

    def hex_to_rgb(self, hex_color):
        """
        Convert HEX color code (e.g., #RRGGBB) to RGB tuple (R, G, B).
        """
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        
        if len(hex_color) == 6:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        else:
            raise ValueError(f"Invalid HEX color code: {hex_color}")

    def replace_color(self, image, target_color, replacement_color, tolerance=50):
        """
        Replace a specific color in the image with the replacement color, given a tolerance range.
        Optimized to speed up the process using vectorized NumPy operations.
        """
        logging.info("Starting color replacement process.")
        
        # Convert the image to RGBA format
        img = image.convert("RGBA")
        data = np.array(img)
        
        # Create bounds for the target color based on tolerance
        lower_bound = np.array([max(0, c - tolerance) for c in target_color])
        upper_bound = np.array([min(255, c + tolerance) for c in target_color])
        
        # Use NumPy to create a mask for the target color range
        mask = np.all(np.logical_and(data[..., :3] >= lower_bound, data[..., :3] <= upper_bound), axis=-1)
        
        # Replace matched pixels with the replacement color (e.g., white)
        data[mask] = replacement_color + (255,)  # Set alpha to fully opaque
        
        image_with_replacement = Image.fromarray(data)
        logging.info(f"Color replacement completed for image with target color {target_color}.")
        return image_with_replacement

    def convert_pdf_to_jpg(self, input_pdf_path, dpi):
        """
        Convert a PDF to JPG images with a progress bar.
        Optimized by reducing DPI (less resolution = faster conversion).
        """
        images = convert_from_path(input_pdf_path, dpi=dpi)  # Reduced DPI to speed up conversion
        for i in tqdm(range(len(images)), desc="Converting PDF to Images", unit="page"):
            logging.info(f"Page {i + 1} converted to image.")
        return images

    def save_image(self, image, output_folder, image_counter):
        """
        Save the processed image as a JPG file.
        """
        image_rgb = image.convert("RGB")  # Convert RGBA to RGB (removes alpha channel)
        output_image_path = os.path.join(output_folder, f"image_{image_counter}.jpg")  # Unique filename
        image_rgb.save(output_image_path, "JPEG")
        logging.info(f"Processed image {image_counter} saved to {output_image_path}")

    def process_pdf(self, input_pdf_path, output_folder, target_color=(0, 0, 0), replacement_color=(255, 255, 255), tolerance=50, progress_bar=None, total_images=None):
        """
        Full process: Convert PDF to JPGs, replace color, and save the images in the output folder.
        Optimized to process PDFs in parallel.
        """
        # Get DPI value from the entry widget
        dpi = int(self.dpi_entry.get())  # Get the DPI entered by the user

        images = self.convert_pdf_to_jpg(input_pdf_path, dpi)  # Pass DPI to the conversion function
        image_counter = total_images  # Start from the passed counter for global image tracking
        total_images += len(images)  # Update total image count

        for i, image in enumerate(tqdm(images, desc="Processing Pages", unit="page", total=len(images))):
            image_with_replaced_color = self.replace_color(image, target_color, replacement_color, tolerance)
            self.save_image(image_with_replaced_color, output_folder, image_counter)
            image_counter += 1

            if progress_bar:
                progress_bar['value'] = (image_counter / total_images) * 100  # Update the progress bar
                progress_bar.update()  # Force the update to be displayed

        return total_images


    def process_multiple_pdfs(self, input_pdf_paths, output_folder, target_color=(0, 0, 0), replacement_color=(255, 255, 255), tolerance=50, progress_bar=None):
        """
        Process multiple PDF files and save the output images in the specified output folder.
        """
        # Ensure the output folder exists
        os.makedirs(output_folder, exist_ok=True)

        total_images = 0  # Total image counter across all PDFs
        for input_pdf_path in input_pdf_paths:
            logging.info(f"Processing PDF: {input_pdf_path}")
            total_images = self.process_pdf(input_pdf_path, output_folder, target_color, replacement_color, tolerance, progress_bar, total_images)

        return total_images

    def read_pdf_list_from_txt(self, file_path):
        """
        Read a list of PDFs from a .txt file (with the format ['input1.pdf', 'input2.pdf', ...]).
        """
        with open(file_path, 'r') as file:
            pdf_list_str = file.read().strip()
        try:
            pdf_list = ast.literal_eval(pdf_list_str)  # Safe evaluation of the string into a list
            if not isinstance(pdf_list, list):
                raise ValueError("The file content is not a valid list.")
        except (SyntaxError, ValueError) as e:
            logging.error(f"Error reading the list from the file: {e}")
            pdf_list = []
        return pdf_list

    def on_start_button_click(self):
        # Set default values for PDF list and output folder
        input_pdfs = self.read_pdf_list_from_txt("output.txt")  # Default PDF list file
        output_folder = "output_images"  # Default output folder
        
        # Get the color input (target color)
        color_input = self.color_entry.get().strip()
        
        try:
            # If the input starts with "#" it's HEX, otherwise it's assumed to be RGB
            if color_input.startswith('#'):
                target_color = self.hex_to_rgb(color_input)
            else:
                # Default to RGB input format
                target_color = tuple(map(int, color_input.split(',')))
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid color input: {e}")
            return
        
        # Get the replacement color input
        replacement_color_input = self.replacement_color_entry.get().strip()
        try:
            # If the input starts with "#" it's HEX, otherwise it's assumed to be RGB
            if replacement_color_input.startswith('#'):
                replacement_color = self.hex_to_rgb(replacement_color_input)
            else:
                # Default to RGB input format
                replacement_color = tuple(map(int, replacement_color_input.split(',')))
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid replacement color input: {e}")
            return
        
        # Get the tolerance value
        try:
            tolerance = int(self.tolerance_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid tolerance value.")
            return
        
        if input_pdfs:
            # Initialize the progress bar with the total number of images (initially unknown)
            self.progress_bar['value'] = 0
            self.progress_bar['maximum'] = 100  # Start with a percentage-based bar
            
            logging.info("Starting PDF processing for multiple files...")
            total_images = self.process_multiple_pdfs(input_pdfs, output_folder, target_color, replacement_color, tolerance, self.progress_bar)


            # Set process_done to True after all PDFs are processed
            self.process_done = True
            

            self.progress_bar['maximum'] = total_images  # Update to the total number of pages
            self.root.destroy()  # Quit the application after completion
            
        else:
            messagebox.showerror("Error", "No valid PDF files found to process.")

    def open(self):
        """
        Open the main application UI.
        """
        self.root.mainloop()

def run():
    root = tk.Tk()
    app = BetterInpage(root)
    app.open()
    return app 

if __name__ == "__main__":
    run()
