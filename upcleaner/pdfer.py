import logging
from fpdf import FPDF
from PIL import Image
import os
import natsort  # Import the natsort library
from PyPDF2 import PdfMerger  # To merge PDFs
def run():
# --------------- USER INPUT -------------------- #
    folder = r"output_images"  # Folder containing all the images (relative path).
    name = "output.pdf"        # Name of the output PDF file.

# Create the 'temp_sticking' directory if it doesn't exist
    temp_sticking_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_sticking")
    if not os.path.exists(temp_sticking_dir):
        os.makedirs(temp_sticking_dir)

# Set up logging to save the log file in 'temp_sticking' folder
    log_file_path = os.path.join(temp_sticking_dir, "batch_processing.log")
    logging.basicConfig(
        filename=log_file_path,  # Log file to store the logs
        level=logging.INFO,      # Log level (INFO level for general info)
        format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
    )
    
# Get the absolute path of the folder
    folder = os.path.abspath(folder)

# Ensure the folder exists
    if not os.path.exists(folder):
        logging.error(f"The folder {folder} does not exist.")
        exit(1)

# ------------- ADD ALL THE IMAGES IN A LIST ------------- #
    imagelist = []  # Contains the list of all images to be converted to PDF.

    for dirpath, dirnames, filenames in os.walk(folder):
        for filename in [f for f in filenames if f.endswith(".jpg")]:
            full_path = os.path.join(dirpath, filename)
            imagelist.append(full_path)

# Sort the images using natural sorting (numerical order in filenames)
    imagelist = natsort.natsorted(imagelist)

# Log all image paths
    logging.info(f"Found {len(imagelist)} images to process.")
    for img_path in imagelist:
        logging.debug(f"Image: {img_path}")

# --------------- ROTATE ANY LANDSCAPE MODE IMAGE IF PRESENT ----------------- #
    for i in range(len(imagelist)):
        im1 = Image.open(imagelist[i])  # Open the image.
        width, height = im1.size       # Get the width and height of that image.
        
    # If the image is in landscape mode (width > height), rotate it.
        if width > height:
            im2 = im1.transpose(Image.ROTATE_270)  # Rotate the image.
            os.remove(imagelist[i])                # Delete the original image.
            im2.save(imagelist[i])                  # Save the rotated image back.
            logging.info(f"Rotated image: {imagelist[i]}")

    logging.info(f"\nFound {len(imagelist)} image files. Converting to PDF....\n")

# --------------- BATCH PDF CREATION AND MERGING ---------------- #
    pdf_merger = PdfMerger()  # To merge the PDF files.

    batch_size = 30  # Number of pages per PDF batch.
    batch_count = len(imagelist) // batch_size + (1 if len(imagelist) % batch_size != 0 else 0)

# Process images in batches and create PDFs
    for batch_index in range(batch_count):
        pdf = FPDF()
        start_index = batch_index * batch_size
        end_index = min((batch_index + 1) * batch_size, len(imagelist))
    
    # Add images for the current batch
        for image in imagelist[start_index:end_index]:
            pdf.add_page()
            pdf.image(image, 0, 0, 210, 297)  # 210 and 297 are the dimensions of an A4 size sheet.
    
    # Save the batch PDF in the 'temp_sticking' subfolder
        batch_pdf_name = f"batch_{batch_index + 1}.pdf"
        batch_pdf_path = os.path.join(temp_sticking_dir, batch_pdf_name)
        pdf.output(batch_pdf_path, "F")
        pdf_merger.append(batch_pdf_path)  # Add this batch PDF to the merger
    
    # Log progress
        logging.info(f"Batch {batch_index + 1} processed, containing images {start_index + 1} to {end_index}.")
    
    # Close the file and then delete it
        try:
            pdf.close()  # Close the PDF file properly
            os.remove(batch_pdf_path)  # Optionally delete the batch PDF after merging
            logging.info(f"Deleted temporary PDF: {batch_pdf_path}")
        except Exception as e:
            logging.error(f"Error deleting file {batch_pdf_path}: {e}")

# Final merged PDF (saved in the original directory)
    final_pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    pdf_merger.write(final_pdf_path)
    pdf_merger.close()

    logging.info(f"PDF generated successfully and saved as {final_pdf_path}")
    print(f"PDF generated successfully and saved as {final_pdf_path}")
    pass

if __name__ == "__main__":
    run()