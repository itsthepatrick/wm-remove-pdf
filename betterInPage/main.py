import splitter  # Assuming splitter.py is in the same directory
import betterinpage  # Assuming wmremv2.py is in the same directory
import time
import page_remover
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
        splitter_app = splitter.run()
        if not splitter_app.process_done:
            print("Splitter process was not completed successfully. Exiting...")
            cleanup()
            exit()
        else:
            print("the spilitting process was successfull")

        time.sleep(0.5) #so the ui s don't mix up
        
        # After splitter completes, run betterinpage.py - Second step
        print("Opening betterinpage UI...")
        BetterInpage_app = betterinpage.run()
        if not BetterInpage_app.process_done:
            print("BetterInpage Core process was not completed successfully. Exiting...")
            cleanup()
            exit()
        else:
            print("the cleaning process was successfull")

        time.sleep(0.5) #so the ui s don't mix up

        # After betterinpage.py completes, run page_remover.py - third step
        print("Opening page_remover UI...")
        ImageManagerApp_app = page_remover.run()
        if not ImageManagerApp_app.process_done:
            print("Processing started but incomplete. Exiting...")
            cleanup()
            exit()
        else:
            print("User skipped or completed the cleanup.")

        
        # After page_remover completes, run pdfer.py - fourth step
        print("Generating PDF...")
        pdfer_app = pdfer.run()
        if not pdfer_app.process_done:
            print("PDF generation process was not completed successfully. Exiting...")
            cleanup()
            exit()
        else:
            print("PDF generating process was successfull")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Always perform cleanup after all steps, even if an error occurs
        print("Performing cleanup...")
        cleanup()
