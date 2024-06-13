import tkinter as tk
from tkinter import filedialog
import shutil

def select_files_and_move(destination_folder, selectedFiles):
    for file_path in selectedFiles:
        try:
            shutil.copy(file_path, destination_folder)
            print(f"Moved: {file_path} to {destination_folder}")
            return True
        except Exception as e:
            print(f"Error moving {file_path}: {e}")
            return False

# if __name__ == "__main__":
#     select_files_and_move("data")