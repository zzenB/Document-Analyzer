import tkinter as tk
from tkinter import filedialog
import shutil
import os

def select_files_and_move(destination_folder):
    # Create a root window and hide it
    root = tk.Tk()
    root.withdraw()
    
    # Open the file dialog to select files
    file_paths = filedialog.askopenfilenames(title="Select files to import")
    
    # Create the destination folder if it doesn't exist
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    
    # Move each selected file to the destination folder
    for file_path in file_paths:
        try:
            shutil.copy(file_path, destination_folder)
            print(f"Moved: {file_path} to {destination_folder}")
        except Exception as e:
            print(f"Error moving {file_path}: {e}")

if __name__ == "__main__":
    # Specify the destination folder
    destination_folder = "data"
    
    # Call the function
    select_files_and_move(destination_folder)
