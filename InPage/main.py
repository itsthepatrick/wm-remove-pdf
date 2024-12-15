import splitter  # Assuming splitter.py is in the same directory
import wmremv2  # Assuming wmremv2.py is in the same directory
import pdfer  # Assuming pdfer.py is in the same directory
import os
import shutil

def cleanup():
    """
    Removes the folders "temp_cut", "output_images", and "temp_sticking",
    as well as the file "output.txt", if they exist.
    """
    folders_to_delete = ["temp_cut", "output_images", "temp_sticking", "__pycache__"]
    file_to_delete = "output.txt"
    
    # Remove folders
    for folder in folders_to_delete:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)  # Delete the folder and all its contents
                print(f"Folder '{folder}' has been deleted.")
            except Exception as e:
                print(f"Error deleting folder '{folder}': {e}")
        else:
            print(f"Folder '{folder}' does not exist.")
    
    # Remove file
    if os.path.exists(file_to_delete):
        try:
            os.remove(file_to_delete)
            print(f"File '{file_to_delete}' has been deleted.")
        except Exception as e:
            print(f"Error deleting file '{file_to_delete}': {e}")
    else:
        print(f"File '{file_to_delete}' does not exist.")

if __name__ == "__main__":
    try:
        cleanup()  # Call the cleanup function to delete the folders and file before starting the process

        # Run splitter.py - First step
        print("Running PdfSplitterApp...")
        splitter.run()  # Calls the function in splitter.py to start the app
        print("PdfSplitterApp completed.")
        
        # After splitter completes, run wmremv2.py - Second step
        print("Opening wmremv2 UI...")
        wmremv2.run()  # Calls the function in wmremv2.py to open the UI
        print("wmremv2 UI closed.")
        
        # After wmremv2 completes, run pdfer.py - Third step
        print("Generating PDF...")
        pdfer.run()  # Calls the function in pdfer.py to start PDF generation
        print("PDF generation completed.")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Always perform cleanup after all steps, even if an error occurs
        print("Performing cleanup...")
        cleanup()
