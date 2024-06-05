import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QLineEdit, QPushButton, QWidget, QHBoxLayout, QVBoxLayout, QScrollArea, QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, QPoint
from qfluentwidgets import ListWidget, ComboBox, PrimaryPushButton

WINDOW_WIDTH = 1366
WINDOW_HEIGHT = 768
SIDEBAR_WIDTH = 200
SIDEBAR_HEIGHT = 400

class ChatGPTUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Document Analyzer")
        self.setGeometry(100, 100, 1600, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        central_layout = QHBoxLayout()
        main_layout.addLayout(central_layout)

        self.create_left_sidebar(central_layout)
        self.create_right_main_area(central_layout)

    def create_left_sidebar(self, parent_layout):
        sidebar_layout = QVBoxLayout()

        self.chat_list = self.create_list_widget()
        self.doc_list = self.create_list_widget()

        sidebar_layout.addWidget(self.chat_list)
        sidebar_layout.addWidget(self.doc_list)

        sidebar_layout.addStretch()

        self.create_sidebar_buttons(sidebar_layout)
        parent_layout.addLayout(sidebar_layout)

    def create_list_widget(self):
        widget = ListWidget(self)
        widget.setMaximumWidth(SIDEBAR_WIDTH)
        widget.setMinimumHeight(SIDEBAR_HEIGHT)
        widget.setStyleSheet("""
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
        # stands = [
        #     "chat1", "chat2", "chat3", "chat4",
        #     "chat5", "chat6", "chat7", "chat8",
        # ]
        # for stand in stands:
        #     item = QListWidgetItem(stand)
        #     widget.addItem(item)
        return widget

    def create_sidebar_buttons(self, sidebar_layout):
        button_layout = QVBoxLayout()
        sidebar_layout.addLayout(button_layout)

        buttons = [
            ("Upload Documents", self.upload_documents),
            ("New Chat", self.new_chat),
            ("Settings", self.open_settings)
        ]

        for text, func in buttons:
            button = PrimaryPushButton(text, self)
            button.clicked.connect(func)
            button_layout.addWidget(button)
            button_layout.addSpacing(5)

        sidebar_layout.addStretch()

    def upload_documents(self):
        print("Upload Documents")

    def new_chat(self):
        print("New Chat")

    def open_settings(self):
        print("Open Settings")

    def create_right_main_area(self, parent_layout):
        right_layout = QVBoxLayout()
        parent_layout.addLayout(right_layout)

        self.model_combo_box = ComboBox(self)
        self.model_combo_box.setPlaceholderText("Select Model")
        model_items = ['Model A', 'Model B', 'Model C', 'Model D']
        self.model_combo_box.addItems(model_items)
        self.model_combo_box.setCurrentIndex(-1)
        self.model_combo_box.currentTextChanged.connect(self.model_changed)
        right_layout.addWidget(self.model_combo_box)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none;")

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("background-color: white; border: none;")
        self.scroll_area.setWidget(self.chat_display)
        right_layout.addWidget(self.scroll_area)

        input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your message here...")
        input_layout.addWidget(self.chat_input)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        right_layout.addLayout(input_layout)

    def send_message(self):
        user_message = self.chat_input.text()
        if user_message:
            self.chat_display.append(f"User: {user_message}")
            self.chat_input.clear()
            self.chat_display.append("ChatGPT: This is a response.")

    def model_changed(self, text):
        print(f"Selected Model: {text}")
    
    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    window = ChatGPTUI()
    window.show()
    sys.exit(app.exec_())
