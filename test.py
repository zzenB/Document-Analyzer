import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QToolButton, QLabel, QScrollArea, QListWidgetItem
from PyQt5.QtCore import Qt, QPoint
from qfluentwidgets import ListWidget, ComboBox
from qfluentwidgets import PrimaryPushButton
from qfluentwidgets import FluentIcon as FIF


class ChatGPTUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set the main window size and remove window borders
        self.setWindowTitle("Document Analyzer")
        self.setGeometry(100, 100, 1366, 768)

        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)

        # Central layout (left sidebar and right main area)
        central_layout = QHBoxLayout()
        main_layout.addLayout(central_layout)

        # Left sidebar for chat list using qfluentwidgets ListWidget
        self.chat_list = ListWidget(self)
        self.chat_list.setMaximumWidth(200)  # Set width of the sidebar (1/3 of 1366px)
        self.chat_list.setMinimumHeight(400)  # Set height of the sidebar
        self.chat_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #D3D3D3;  /* Soft grey border */
                border-radius: 5px;  /* Rounded corners */
                padding: 5px;  /* Add some padding inside the border */
                background-color: transparent;  /* Set background to transparent */
            }
            QListWidget::item {
                padding: 5px 5px 5px 5px 20px;  /* Add some padding to the list items */
            }
        """)

        stands = [
            "chat1", "chat2", "chat3", "chat4",
            "chat5", "chat6", "chat7", "chat8",
        ]
        for stand in stands:
            item = QListWidgetItem(stand)
            self.chat_list.addItem(item)

        # Left sidebar (bottom) for uploaded documents using qfluentwidgets ListWidget
        self.doc_list = ListWidget(self)
        self.doc_list.setMaximumWidth(200)  # Set width of the sidebar (1/3 of 1366px)
        self.doc_list.setMaximumHeight(400)  # Set height of the sidebar
        self.doc_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #D3D3D3;  /* Soft grey border */
                border-radius: 5px;  /* Rounded corners */
                padding: 5px;  /* Add some padding inside the border */
                background-color: transparent;  /* Set background to transparent */
            }
            QListWidget::item {
                padding: 5px 5px 5px 5px 20px;  /* Add some padding to the list items */
            }

        """)

        stands_doc = [
            "doc1", "doc2", "doc3", "doc4",
            "doc5", "doc6", "doc7", "doc8",
        ]
        for stand in stands_doc:
            item = QListWidgetItem(stand)
            self.doc_list.addItem(item)

        # Button layout for the sidebar
        button_layout = QVBoxLayout()

        # Add the primary color push buttons
        upload_button = PrimaryPushButton("Upload Documents", self)
        button_layout.addWidget(upload_button)
        button_layout.addSpacing(5)

        new_chat_button = PrimaryPushButton("New Chat", self)
        button_layout.addWidget(new_chat_button)
        button_layout.addSpacing(5)

        settings_button = PrimaryPushButton("Settings", self)
        button_layout.addWidget(settings_button)

        sidebar_layout = QVBoxLayout()

        # Create a new layout for the chat_list and doc_list
        sidebar_sub_layout = QVBoxLayout()
        sidebar_sub_layout.addWidget(self.chat_list)
        sidebar_sub_layout.addWidget(self.doc_list, stretch=1)  # Add doc_list with a stretch

        sidebar_layout.addLayout(sidebar_sub_layout)
        sidebar_layout.addStretch()  # Add a stretch to align the sidebar_sub_layout to the top

        # Add the button layout
        sidebar_layout.addLayout(button_layout)
        sidebar_layout.addStretch()
    
        central_layout.addLayout(sidebar_layout)


        # Right main area layout
        right_layout = QVBoxLayout()

        # ComboBox for model selection
        self.model_combo_box = ComboBox(self)
        self.model_combo_box.setPlaceholderText("Select Model")
        model_items = ['Model A', 'Model B', 'Model C', 'Model D']
        self.model_combo_box.addItems(model_items)
        self.model_combo_box.setCurrentIndex(-1)
        self.model_combo_box.currentTextChanged.connect(self.model_changed)
        right_layout.addWidget(self.model_combo_box)

        # Scroll area for the chat display
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none;")

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("background-color: white; border: none;")
        self.scroll_area.setWidget(self.chat_display)
        right_layout.addWidget(self.scroll_area)

        # Input area
        input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your message here...")
        input_layout.addWidget(self.chat_input)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        right_layout.addLayout(input_layout)

        central_layout.addLayout(right_layout)

    def send_message(self):
        user_message = self.chat_input.text()
        if user_message:
            self.chat_display.append(f"User: {user_message}")
            self.chat_input.clear()
            # Placeholder for ChatGPT response
            self.chat_display.append("ChatGPT: This is a response.")

    # def toggle_maximize_restore(self):
    #     if self.isMaximized():
    #         self.showNormal()
    #         self.maximize_button.setIcon(QIcon("path/to/maximize-icon.png"))
    #     else:
    #         self.showMaximized()
    #         self.maximize_button.setIcon(QIcon("path/to/restore-icon.png"))

    def model_changed(self, text):
        print(f"Selected Model: {text}")
    
    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint (event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

if __name__ == "__main__":
    # enable dpi scale
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    window = ChatGPTUI()
    window.show()
    sys.exit(app.exec_())
