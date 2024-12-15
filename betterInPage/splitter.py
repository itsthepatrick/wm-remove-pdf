import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import PyPDF2
import os

class PdfSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Splitter")
        self.root.geometry("400x200")

        # Create UI elements
        self.create_widgets()

    def create_widgets(self):
        # Choose PDF Button
        self.choose_button = tk.Button(self.root, text="Choose PDF File", command=self.choose_file)
        self.choose_button.pack(pady=10)

        # Label to show the selected file
        self.file_label = tk.Label(self.root, text="No file selected")
        self.file_label.pack(pady=5)

        # Progress bar
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=10)

    def choose_file(self):
        # Open file dialog to select a PDF
        file_name = filedialog.askopenfilename(title="Open PDF File", filetypes=[("PDF Files", "*.pdf")])

        if file_name:
            self.file_label.config(text=f"Selected file: {os.path.basename(file_name)}")
            self.split_pdf(file_name)

    def split_pdf(self, input_pdf, pages_per_split=20):
        try:
            # Ensure the "temp_cut" folder exists
            temp_cut_folder = "temp_cut"
            os.makedirs(temp_cut_folder, exist_ok=True)

            # Open the input PDF file
            with open(input_pdf, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                total_pages = len(reader.pages)

                # Determine how many split files are needed
                num_splits = total_pages // pages_per_split + (1 if total_pages % pages_per_split != 0 else 0)

                # Set progress bar maximum
                self.progress["maximum"] = num_splits

                # Initialize a list to keep track of the output filenames
                output_filenames = []

                # Process each split
                for split_num in range(num_splits):
                    writer = PyPDF2.PdfWriter()

                    # Determine the start and end page for this split
                    start_page = split_num * pages_per_split
                    end_page = min(start_page + pages_per_split, total_pages)

                    # Add pages to the writer
                    for page_num in range(start_page, end_page):
                        writer.add_page(reader.pages[page_num])

                    # Name the output PDF file with "input" followed by the part number
                    output_pdf = f"{temp_cut_folder}/input{split_num + 1}.pdf"
                    output_filenames.append(f"'{output_pdf}'")

                    # Write the output PDF to a file in the "temp_cut" folder
                    with open(output_pdf, "wb") as output_file:
                        writer.write(output_file)

                    print(f"Created: {output_pdf}")

                    # Update progress bar
                    self.progress["value"] = split_num + 1
                    self.root.update_idletasks()

                # Save the list of output filenames in the required format to a text file
                with open("output.txt", "w", encoding="utf-8") as txt_file:
                    txt_file.write(f"[{', '.join(output_filenames)}]")
                print(f"Output filenames saved to output.txt")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            # Close the app after completion
            self.root.destroy()

def run():
    root = tk.Tk()
    app = PdfSplitterApp(root)
    root.mainloop()

if __name__ == "__main__":
    run()