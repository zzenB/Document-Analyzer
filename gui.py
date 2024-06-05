import os
import sys
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QFileDialog, QComboBox, QListWidget, QListWidgetItem, QLabel
from PyQt5.QtGui import QIcon, QPixmap
import time

# Import existing code
from upload_files import select_files_and_move
from summarize_docs import summarize_docs
from query_data_v2 import query_rag
from populate_database import run_database, clear_database
from db_utils import create_db, generate_session_id, display_chat_history

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Document Summarizer and Chat Bot")
        self.setGeometry(100, 100, 1366, 768)

        # Create main layout
        main_layout = QHBoxLayout()

        # Left Sidebar
        left_sidebar = QWidget()
        left_sidebar_layout = QVBoxLayout()
        left_sidebar.setLayout(left_sidebar_layout)

        self.chat_list = QListWidget()
        left_sidebar_layout.addWidget(QLabel("Chat History"))
        left_sidebar_layout.addWidget(self.chat_list)

        # Right Sidebar
        right_sidebar = QWidget()
        right_sidebar_layout = QVBoxLayout()
        right_sidebar.setLayout(right_sidebar_layout)

        self.model_combo = QComboBox()
        self.model_combo.addItems(["gpt-3.5-turbo-0125", "Other Model"])
        right_sidebar_layout.addWidget(QLabel("Select Model"))
        right_sidebar_layout.addWidget(self.model_combo)

        upload_button = QPushButton("Upload Documents")
        upload_button.clicked.connect(self.upload_documents)
        right_sidebar_layout.addWidget(upload_button)

        # Main Window
        main_window = QWidget()
        main_window_layout = QVBoxLayout()
        main_window.setLayout(main_window_layout)

        self.chat_text = QTextEdit()
        self.chat_text.setReadOnly(True)
        main_window_layout.addWidget(self.chat_text)

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        input_layout.addWidget(self.input_field)
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        main_window_layout.addLayout(input_layout)

        # Floating Button
        floating_button = QPushButton("Summarize Documents")
        floating_button.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 20px; padding: 10px 20px;")
        floating_button.clicked.connect(self.summarize_documents)

        # Add widgets to main layout
        main_layout.addWidget(left_sidebar)
        main_layout.addWidget(main_window)
        main_layout.addWidget(right_sidebar)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Add floating button to the main window
        floating_button_layout = QHBoxLayout()
        floating_button_layout.addStretch()
        floating_button_layout.addWidget(floating_button)
        floating_button_layout.addStretch()
        main_window_layout.addLayout(floating_button_layout)

        self.documents = []
        self.selected_model = "gpt-3.5-turbo-0125"
        self.session_id = None

    def upload_documents(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            for file_path in selected_files:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                self.documents.append(file_content)
            print(f"Uploaded {len(selected_files)} documents.")

    def send_message(self):
        message = self.input_field.text()
        if message:
            self.chat_text.append(f"Human: {message}")
            self.input_field.clear()

            response = query_rag(self.selected_model, message, self.session_id)
            self.chat_text.append(f"AI: {response}")

    def summarize_documents(self):
        if not self.documents:
            return

        selected_model = self.model_combo.currentText()
        summary = summarize_docs(selected_model, self.documents)
        self.chat_text.append(f"Summary: {summary}")

    def create_new_session(self):
        self.session_id = str(int(time.time()))
        item = QListWidgetItem(self.session_id)
        self.chat_list.addItem(item)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('path/to/icon.png'))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())