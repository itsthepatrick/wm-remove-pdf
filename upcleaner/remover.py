import fitz  # PyMuPDF
from tkinter import Tk, Canvas, Button, Frame, Label
from PIL import Image, ImageTk, ImageFilter

from scipy.ndimage import binary_dilation, gaussian_filter
import numpy as np
import os

# Load PDF file paths from a .txt file
def load_pdf_paths(file_path):
    with open(file_path, 'r') as file:
        pdf_paths = eval(file.read())
    return pdf_paths

# Convert a PDF page to an image
def pdf_page_to_image(pdf_path, page_num):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    pix = page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img, pix.width, pix.height

# Replace selected color in the region

def color_distance(c1, c2):
    """Compute the Euclidean distance between two RGB colors."""
    return np.sqrt(np.sum((np.array(c1) - np.array(c2))**2))

def replace_color_in_region(image, region, target_color, tolerance=80, iterations=5, dilation_radius=3, blur_radius=5):
    """Replace watermark color with surrounding pixels over multiple iterations."""
    image_np = np.array(image)  # Convert image to numpy array
    x_start, y_start, x_end, y_end = region

    # Ensure the region coordinates are ordered correctly
    if x_start > x_end:
        x_start, x_end = x_end, x_start
    if y_start > y_end:
        y_start, y_end = y_end, y_start

    # Extract the selected region
    region_image = image_np[y_start:y_end, x_start:x_end]

    # Calculate the absolute difference from the target color
    diff = np.abs(region_image - target_color)
    
    # Create a mask where all RGB channels are within tolerance
    mask = np.all(diff <= tolerance, axis=-1)  # Match pixels within tolerance

    # Debugging: Check how many pixels match the target color
    print(f"Mask shape: {mask.shape}, Matching pixels: {np.count_nonzero(mask)}")
    
    if np.count_nonzero(mask) == 0:
        print("No matching pixels found.")
        return image

    # Apply multiple iterations of replacement and smoothing
    for _ in range(iterations):
        region_image = apply_blending(region_image, mask, blur_radius)
    
    # Apply dilation to the mask to ensure we cover nearby pixels
    mask = dilate_mask(mask, dilation_radius)
    
    # Replace matching pixels with the blended region
    for y in range(region_image.shape[0]):
        for x in range(region_image.shape[1]):
            if mask[y, x]:
                # Get valid neighbors for averaging
                neighbors = []
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < region_image.shape[0] and 0 <= nx < region_image.shape[1]:
                            if not mask[ny, nx]:  # If neighbor is not the target color
                                neighbors.append(region_image[ny, nx])

                # Replace the target pixel with the average of valid neighbors
                if neighbors:
                    region_image[y, x] = np.mean(neighbors, axis=0).astype(np.uint8)
                else:
                    # If no valid neighbors, replace with white or fallback color
                    region_image[y, x] = [255, 255, 255]

    # Update the image with the modified region
    image_np[y_start:y_end, x_start:x_end] = region_image
    return Image.fromarray(image_np)  # Convert back to Image object

def apply_blending(region_image, mask, blur_radius):
    """Apply a smooth blending filter to the region."""
    region_image = Image.fromarray(region_image)
    blurred_region = region_image.filter(ImageFilter.GaussianBlur(blur_radius))  # Apply blur
    blurred_region_np = np.array(blurred_region)

    # Ensure the dimensions match
    assert blurred_region_np.shape == region_image.size[::-1] + (3,), "Dimensions mismatch in the image and blurred region."

    # For each pixel in the selected region, apply blending using the blurred version
    for y in range(region_image.height):
        for x in range(region_image.width):
            if mask[y, x]:  # Only process matching pixels
                region_image.putpixel((x, y), tuple(blurred_region_np[y, x]))  # Replace with blurred pixel
    
    return np.array(region_image)

def dilate_mask(mask, radius):
    """Dilate the mask to cover nearby pixels to ensure a smooth transition."""
    dilated_mask = binary_dilation(mask, structure=np.ones((radius, radius)))
    return dilated_mask.astype(np.bool)

# Tkinter GUI for region and color selection
class RegionSelector:
    def __init__(self, pdf_paths):
        self.pdf_paths = pdf_paths
        self.selected_region = None
        self.selected_color = None
        self.root = Tk()
        self.root.title("PDF Watermark Replacer")
        self.init_gui()

    def init_gui(self):
        """Initialize the GUI components."""
        # Top frame for buttons
        self.top_frame = Frame(self.root)
        self.top_frame.pack(fill="x", pady=5)

        self.info_label = Label(self.top_frame, text="Select a region and color on Page 2 of the first PDF.")
        self.info_label.pack(side="left", padx=10)

        self.next_button = Button(self.top_frame, text="Next", command=self.process_pdfs, state="disabled")
        self.next_button.pack(side="right", padx=5)

        self.pick_color_button = Button(self.top_frame, text="Pick Color", command=self.pick_color, state="disabled")
        self.pick_color_button.pack(side="right", padx=5)

        self.clear_button = Button(self.top_frame, text="Clear Selection", command=self.clear_selection)
        self.clear_button.pack(side="right", padx=5)

        # Canvas for displaying the PDF page image
        self.canvas = Canvas(self.root)
        self.canvas.pack(fill="both", expand=True)

        # Bind mouse click events for region selection
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Load the second page of the first PDF
        self.load_second_page()

    def load_second_page(self):
        """Load the second page of the first PDF for selection."""
        pdf_path = self.pdf_paths[0]
        img, width, height = pdf_page_to_image(pdf_path, 1)  # Page 2 is at index 1
        self.image = img
        self.tk_image = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")
        self.canvas.config(scrollregion=(0, 0, width, height))

    def on_canvas_click(self, event):
        """Handle mouse clicks for selecting a region."""
        if self.selected_region is None:
            # Start of selection rectangle
            self.selected_region = [event.x, event.y, None, None]
        else:
            # End of selection rectangle
            self.selected_region[2], self.selected_region[3] = event.x, event.y

            # Ensure the selected region has valid coordinates
            if self.selected_region[0] > self.selected_region[2]:
                self.selected_region[0], self.selected_region[2] = self.selected_region[2], self.selected_region[0]
            if self.selected_region[1] > self.selected_region[3]:
                self.selected_region[1], self.selected_region[3] = self.selected_region[3], self.selected_region[1]

            self.draw_region()

            # Print the selected region for debugging
            print(f"Region selected: {self.selected_region}")

            self.pick_color_button.config(state="normal")


    def draw_region(self):
        """Draw the selection rectangle on the canvas."""
        if self.selected_region and None not in self.selected_region:
            self.canvas.delete("region")
            x_start, y_start, x_end, y_end = self.selected_region
            self.canvas.create_rectangle(x_start, y_start, x_end, y_end, outline="red", width=2, tags="region")


    def clear_selection(self):
        """Clear the current region and color selection."""
        self.selected_region = None
        self.selected_color = None
        self.canvas.delete("region")
        self.pick_color_button.config(state="disabled")
        self.next_button.config(state="disabled")

    def pick_color(self):
        """Pick a color within the selected region."""
        def on_color_pick(event):
            x, y = event.x, event.y
            self.selected_color = self.image.getpixel((x, y))
            print(f"Selected color: {self.selected_color}")
            self.next_button.config(state="normal")
            self.canvas.unbind("<Button-1>")

        self.canvas.bind("<Button-1>", on_color_pick)

    def calculate_surrounding_color(image, region, margin=10):
        """Calculate the average color from the region around the watermark."""
        x_start, y_start, x_end, y_end = region

        # Create a margin around the selected region to calculate the surrounding color
        surrounding_x_start = max(x_start - margin, 0)
        surrounding_y_start = max(y_start - margin, 0)
        surrounding_x_end = x_end + margin
        surrounding_y_end = y_end + margin

        # Ensure that the surrounding region is within image bounds
        surrounding_x_end = min(surrounding_x_end, image.width)
        surrounding_y_end = min(surrounding_y_end, image.height)

        surrounding_region = image.crop((surrounding_x_start, surrounding_y_start, surrounding_x_end, surrounding_y_end))

        # Convert surrounding region to numpy array and calculate average color
        surrounding_np = np.array(surrounding_region)

        # Calculate the average color (mean of all pixels in the region)
        avg_color = np.mean(surrounding_np, axis=(0, 1)).astype(int)
        return tuple(avg_color)  # Return the average color as a tuple (R, G, B)

    def process_pdfs(self):
        """Apply region and color replacement to all pages of all PDFs."""
        if not self.selected_region or not self.selected_color:
            print("No region or color selected!")
            return

        output_folder = "output_images"
        os.makedirs(output_folder, exist_ok=True)

        for pdf_index, pdf_path in enumerate(self.pdf_paths):
            doc = fitz.open(pdf_path)
            print(f"Processing {pdf_path}...")

            # Process all pages, but skip page 1 (index 0) for the first PDF (file1.pdf)
            for page_num in range(len(doc)):
                # If this is the first PDF, skip the first page (index 0)
                if pdf_index == 0 and page_num == 0:
                    continue  # Skip the first page of the first PDF

                img, _, _ = pdf_page_to_image(pdf_path, page_num)
                img = replace_color_in_region(img, self.selected_region, self.selected_color)

                # Save the image as JPG with quality control
                jpg_path = f"{output_folder}/{os.path.basename(pdf_path)}_page_{page_num + 1}.jpg"
                img.save(jpg_path, "JPEG", quality=90, optimize=True, progressive=True)  # You can adjust the quality (0-100)

            print(f"Processing complete! Images saved in {output_folder}")
    
        self.root.quit()
    
    def start(self):
        """Start the Tkinter event loop."""
        self.root.mainloop()

# Main function
def main():
    pdf_paths = load_pdf_paths("output.txt")  # Update path to your .txt file
    selector = RegionSelector(pdf_paths)
    selector.start()

def run():
    main()

if __name__ == "__main__":
    main()
