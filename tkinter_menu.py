import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import os
import threading

from upload_files import select_files_and_move
from summarize_docs import summarize_docs
from query_data_v2 import query_rag
from populate_database import run_database

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Analyzer")
        self.geometry("400x300")
        self.model = ""
        self.model_options = ["Llama2", "Llama3", "Phi3-Mini", "GPT-3.5 Turbo (Online)"]
        self.model = self.model_options[3]  # Set the default option

        self.menu_frame = tk.Frame(self)
        self.menu_frame.pack(pady=20)

        self.upload_button = tk.Button(self.menu_frame, text="1. Upload PDF files", command=self.upload_files)
        self.upload_button.pack(pady=5)

        self.summarize_button = tk.Button(self.menu_frame, text="2. Summarize PDF content", command=self.summarize_docs)
        self.summarize_button.pack(pady=5)

        self.chat_button = tk.Button(self.menu_frame, text="3. Chat with the bot", command=self.chat_bot)
        self.chat_button.pack(pady=5)

        self.model_label = tk.Label(self.menu_frame, text="4. Select model:")
        self.model_label.pack(pady=5)

        self.model_dropdown = ttk.Combobox(self.menu_frame, textvariable=self.model, values=self.model_options, state="readonly")
        self.model_dropdown.pack(pady=5)
        self.model_dropdown.bind("<<ComboboxSelected>>", lambda event: self.select_model())

        self.exit_button = tk.Button(self.menu_frame, text="5. Exit", command=self.quit)
        self.exit_button.pack(pady=5)

        self.selected_pdf_label = tk.Label(self.menu_frame, text="", wraplength=275)
        self.selected_pdf_label.pack(pady=5)
        self.update_selected_pdf_label()

    def upload_files(self):
        check = select_files_and_move("data")
        if check:
            messagebox.showinfo("Success", "PDF files uploaded successfully.")
            self.update_selected_pdf_label()

             # Create a popup window that can't be closed
            loading_popup = tk.Toplevel(self)
            loading_popup.title("Processing")
            loading_popup.geometry("200x100")
            tk.Label(loading_popup, text="Running database... Please wait.").pack(pady=20)
            loading_popup.transient(self)
            loading_popup.grab_set()
            loading_popup.protocol("WM_DELETE_WINDOW", lambda: None)

            # Run the database function in a separate thread to avoid blocking the main thread
            def run_and_close():
                run_database()
                loading_popup.destroy()
            
            threading.Thread(target=run_and_close).start()
        else:
            messagebox.showerror("Error", "No files uploaded.")
    
    def summarize_docs(self):   
        if self.model:
            summary = summarize_docs(self.model)
            if summary:
                messagebox.showinfo("Summary", summary)
            else:
                messagebox.showwarning("Warning", "Failed to summarize documents.")
        else:
            messagebox.showwarning("Warning", "Please select a model first.")

    def chat_bot(self):
        if self.model:
            query = tk.simpledialog.askstring("Chat with the bot", "Enter your question:")
            if query:
                answer = query_rag(query, self.model)
                if answer:
                    messagebox.showinfo("Answer", answer)
                else:
                    messagebox.showwarning("Warning", "Failed to get an answer.")
        else:
            messagebox.showwarning("Warning", "Please select a model first.")

    def show_loading(self, is_loading):
        if is_loading:
            self.loading_label.pack(side="left", padx=5)
        else:
            self.loading_label.pack_forget()

    def select_model(self):
        selected_model = self.model_dropdown.get()
        if selected_model:
            if selected_model == self.model_options[0]:
                self.model = "llama2"
            elif selected_model == self.model_options[1]:
                self.model = "llama3"
            elif selected_model == self.model_options[2]:
                self.model = "phi3:mini"
            elif selected_model == self.model_options[3]:
                self.model = "gpt-3.5-turbo-0125"
        messagebox.showinfo("Model Selected", f"You have selected the {selected_model} model.")
    
    def update_selected_pdf_label(self):
        pdf_files = [file for file in os.listdir("data") if file.endswith(".pdf")]
        if pdf_files:
            pdfs = ", ".join(pdf_files)

            if len(pdfs) > 110:
                pdfs = pdfs[:110] + "..."
            self.selected_pdf_label.config(text=f"Selected PDF: {pdfs}")
        else:
            self.selected_pdf_label.config(text="No PDF selected.")

if __name__ == "__main__":
    app = App()
    app.mainloop()