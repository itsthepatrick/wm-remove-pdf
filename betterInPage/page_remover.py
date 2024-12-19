import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from collections import defaultdict
import imagehash

# Global path to output_images folder
LOCKED_FOLDER_PATH = os.path.expanduser("output_images")  # Set your folder path here

class ImageManagerApp:
    def __init__(self, root, folder_path):
        self.root = root
        self.root.title("Image Manager")

        # Store the locked folder path
        self.folder_path = folder_path
        self.image_files = []  # List of image files in folder
        self.duplicates = defaultdict(list)  # To store repeated images

        self.selected_for_deletion = []  # Files to delete
        self.check_vars = {}  # Checkbox variables for selection

        # Status flag to track if user proceeds
        self.process_done = False  # Assume true unless user processes but exits early
        self.started_processing = False  # To track processing state

        # UI Setup
        self.create_initial_buttons()

    def create_initial_buttons(self):
        """Create the first step buttons: Proceed and Skip."""
        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=20)

        # Intro label
        tk.Label(frame, text="Image Manager", font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(frame, text="Do you want to proceed with image cleanup?", font=("Arial", 12)).pack(pady=5)

        # Proceed button
        proceed_btn = tk.Button(frame, text="Proceed", width=15, command=self.start_cleanup)
        proceed_btn.pack(pady=5)

        # Skip button (closes the app)
        skip_btn = tk.Button(frame, text="Skip", width=15, command=self.skip_cleanup)
        skip_btn.pack(pady=5)

    def skip_cleanup(self):
        """Handles skipping the process."""
        self.process_done = True  # User skipped cleanup
        self.root.destroy()  # Close the app

    def start_cleanup(self):
        """Proceed to load and display duplicates for cleanup."""
        self.started_processing = True  # Mark that processing has started

        # Destroy the initial UI
        for widget in self.root.winfo_children():
            widget.destroy()

        # Setup scrollable UI
        self.canvas = tk.Canvas(self.root)
        self.frame = tk.Frame(self.canvas)
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Load images and prepare UI
        self.load_images()
        self.display_images()

        # Add button to finalize deletion
        self.delete_button = tk.Button(self.root, text="Delete Selected and Close", command=self.delete_selected)
        self.delete_button.pack(pady=10)

    def load_images(self):
        """Load all images in the folder and group duplicates."""
        if not os.path.exists(self.folder_path):
            messagebox.showerror("Error", f"Folder not found: {self.folder_path}")
            self.root.quit()

        # Identify duplicates using perceptual hashing
        hash_table = {}
        for file in os.listdir(self.folder_path):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                full_path = os.path.join(self.folder_path, file)
                try:
                    img = Image.open(full_path)
                    img_hash = str(imagehash.average_hash(img))  # Generate perceptual hash

                    # Check for duplicates using the perceptual hash
                    if img_hash in hash_table:
                        self.duplicates[img_hash].append(full_path)
                    else:
                        hash_table[img_hash] = full_path
                        self.duplicates[img_hash] = [full_path]

                except Exception as e:
                    print(f"Error processing {full_path}: {e}")

        # Filter to only repeated images
        self.image_files = [files for files in self.duplicates.values() if len(files) > 1]

    def display_images(self):
        """Display duplicated images with checkboxes."""
        tk.Label(self.frame, text="Select images to delete:", font=("Arial", 12, "bold")).pack(pady=5)

        for duplicate_set in self.image_files:
            # Group header
            group_frame = tk.Frame(self.frame, relief="groove", borderwidth=2)
            group_frame.pack(pady=10, padx=10, fill="x")

            tk.Label(group_frame, text="Repeated Images:", font=("Arial", 10, "bold")).pack(anchor="w")

            for image_path in duplicate_set:
                # Image Preview
                img = Image.open(image_path)
                img.thumbnail((100, 100))  # Resize image to thumbnail
                photo = ImageTk.PhotoImage(img)

                img_label = tk.Label(group_frame, image=photo)
                img_label.image = photo  # Keep reference to avoid garbage collection
                img_label.pack(side="left", padx=5, pady=5)

                # Checkbox
                var = tk.BooleanVar()
                check = tk.Checkbutton(group_frame, text=os.path.basename(image_path), variable=var)
                check.pack(anchor="w")

                # Store checkbox state and path
                self.check_vars[image_path] = var

    def delete_selected(self):
        """Delete checked images and close the app."""
        for image_path, var in self.check_vars.items():
            if var.get():  # Checked for deletion
                try:
                    os.remove(image_path)
                    print(f"Deleted: {image_path}")
                except Exception as e:
                    print(f"Error deleting {image_path}: {e}")

        messagebox.showinfo("Done", "Selected images have been deleted.")
        self.process_done = True  # Mark as done only after deletion
        self.root.destroy()


def main():
    root = tk.Tk()

    if not os.path.exists(LOCKED_FOLDER_PATH):
        messagebox.showerror("Error", f"Folder path '{LOCKED_FOLDER_PATH}' does not exist!")
        return None  # Explicitly return None if the folder is missing

    app = ImageManagerApp(root, LOCKED_FOLDER_PATH)
    root.mainloop()
    return app  # Return the app instance to check the `process_done` status


def run():
    return main()  # Return the `ImageManagerApp` instance


if __name__ == "__main__":
    run()