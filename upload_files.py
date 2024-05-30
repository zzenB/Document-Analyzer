import tkinter as tk
from tkinter import filedialog
import shutil

def select_files_and_move(destination_folder):
    # Create a root window and hide it
    root = tk.Tk()
    root.withdraw()
    
    # Open the file dialog to select files
    file_paths = filedialog.askopenfilenames(title="Select PDF files", filetypes=[("PDF Files", "*.pdf")])

    if not file_paths:
        print("Error: No files were selected.")
        return
    
    # Move each selected file to the destination folder
    for file_path in file_paths:
        try:
            shutil.copy(file_path, destination_folder)
            print(f"Moved: {file_path} to {destination_folder}")
        except Exception as e:
            print(f"Error moving {file_path}: {e}")

    return file_path

# if __name__ == "__main__":
#     select_files_and_move("data")