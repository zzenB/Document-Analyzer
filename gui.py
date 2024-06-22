import sys
import markdown
import os
import dotenv
from dotenv import load_dotenv
load_dotenv()

import openai
from openai import OpenAI

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qfluentwidgets import *

from upload_files import select_files_and_move
from summarize_docs import summarize_docs
from query_data_v2 import query_rag
from vector_store import run_database, docs_used_in_chroma
from db_utils import generate_session_id, return_chat_history, create_db
from llm_utils import list_local_models

WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 900
SIDEBAR_WIDTH = 200
SIDEBAR_HEIGHT = 400

class WorkerSignals(QObject):
    finished = pyqtSignal(bool)
    result = pyqtSignal(list)
    summary = pyqtSignal(str)

class Worker(QRunnable):
    """
    A worker class that represents a task to be executed in a separate thread (in this case the llm query and database operations).

    Args:
        fn (function): The function to be executed by the worker.
        *args: Variable length argument list to be passed to the function.
        **kwargs: Arbitrary keyword arguments to be passed to the function.

    Attributes:
        fn (function): The function to be executed by the worker.
        args (tuple): The arguments to be passed to the function.
        kwargs (dict): The keyword arguments to be passed to the function.
        signals (WorkerSignals): The signals used for communication between the worker and the main thread.
    """

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        """
        Executes the function in a separate thread.

        Emits the `finished` signal with the result if the function returns a boolean value,
        otherwise emits the `result` signal with the result.
        """
        result = self.fn(*self.args, **self.kwargs)
        if type(result) == bool:
            self.signals.finished.emit(result)
        elif type(result) == list:
            self.signals.result.emit(result)
        else:
            self.signals.summary.emit(result)
            
class SettingsBox(MessageBoxBase):
    """
    A dialog box for managing settings, specifically the OpenAI API key.

    Inherits from MessageBoxBase.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel('OpenAI API Key', self)
        self.apiKey = LineEdit(self)

        if os.getenv('OPENAI_API_KEY') is not None:
            self.apiKey.setText(os.getenv('OPENAI_API_KEY'))
        else:
            self.apiKey.setPlaceholderText('Enter your OpenAI API key here...')
        self.apiKey.setClearButtonEnabled(True)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.apiKey)

        self.yesButton.setText('Apply')
        self.cancelButton.setText('Cancel')

        self.widget.setMinimumWidth(350)
        self.yesButton.setDisabled(True)
        self.apiKey.textChanged.connect(self.enable_apply_button)
        self.yesButton.clicked.connect(self.check_openai_api_key)  

    def enable_apply_button(self, text):
        """
        Enable the 'Apply' button if the API key text field is not empty.

        Args:
            text (str): The current text in the API key text field.
        """
        self.yesButton.setEnabled(bool(text.strip()))  
    
    def accept(self):
        """
        Override the accept method to save the API key and close the dialog box.
        """
        api_key = self.apiKey.text().strip()
        if self.check_openai_api_key(api_key):
            # Save the API key to .env file
            dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
            if not os.path.isfile(dotenv_path):
                with open(dotenv_path, 'w') as f:
                    f.write('OPENAI_API_KEY=\n')

            dotenv.set_key(dotenv_path, 'OPENAI_API_KEY', api_key)

            super().accept()
            
    def check_openai_api_key(self, text):
        """
        Check if the provided OpenAI API key is valid.

        Args:
            text (str): The OpenAI API key to check.

        Returns:
            bool: True if the API key is valid, False otherwise.
        """
        key = text
        client = OpenAI(api_key=key)
        try:
            client.models.list()
        except openai.AuthenticationError as e:
            self.createWarningInfoBar(
                "Error", "The OpenAI API key you entered is invalid. Please enter a valid API key."
            )
            return False
        else:
            return True
        
    def createWarningInfoBar(self, title, content):
        """
        Create a warning info bar with the given title and content.

        Args:
            title (str): The title of the info bar.
            content (str): The content of the info bar.
        """
        InfoBar.warning(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.NONE,
            duration=20000,
            parent=self,
        )

class DocAnalyzerUI(QMainWindow):
    """
    The main user interface class for the Document Analyzer application.

    This class extends the QMainWindow class from the PyQt5 library and provides
    the graphical user interface for the application. It includes methods for
    initializing the UI, loading chats and PDFs, creating the left sidebar,
    creating sidebar buttons, uploading documents, handling database operations,
    creating information bars, creating new chats, opening settings, creating the
    right main area, displaying chat content, checking and sending messages.

    Attributes:
        chat_list (QListWidget): The list widget for displaying chat names.
        doc_list (QListWidget): The list widget for displaying document names.
        chat_contents (dict): A dictionary to store the contents of each chat.
        selected_model (str): The currently selected AI model.
        selected_chat (str): The currently selected chat.

    Methods:
        __init__(): Initializes the DocAnalyzerUI class.
        init_ui(): Initializes the user interface.
        load_chats(): Loads the chat history into the chat list.
        load_pdfs(): Loads the available PDFs into the document list.
        create_left_sidebar(parent_layout): Creates the left sidebar layout.
        create_list_widget(str): Creates a list widget with custom styling.
        create_sidebar_buttons(sidebar_layout): Creates buttons for the sidebar.
        upload_documents(): Opens a file dialog for uploading documents.
        database_operation_finished(result): Handles the completion of database operations.
        createWarningInfoBar(title, content): Creates a warning information bar.
        createSuccessInfoBar(title, content): Creates a success information bar.
        createErrorInfoBar(title, content): Creates an error information bar.
        new_chat(): Creates a new chat.
        open_settings(): Opens the settings dialog.
        create_right_main_area(parent_layout): Creates the right main area layout.
        display_chat_content(item): Displays the content of a selected chat.
        check_and_send(): Checks and sends a message.
    """
    def __init__(self):
        super().__init__()

        self.init_ui()
        self.load_chats()
        self.load_pdfs()
        if self.chat_list.count() < 1:
            self.new_chat()

        self.threadpool = QThreadPool()
        print(
            "Multithreading with maximum %d threads" % self.threadpool.maxThreadCount()
        )

        self.chat_list.itemClicked.connect(self.display_chat_content)
        self.chat_list.itemClicked.connect(self.update_chat)

    def init_ui(self):
        self.setWindowTitle("Document Analyzer")
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowIcon(QIcon("assets/doc_logo.png"))

        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #f9f9f9;")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        central_layout = QHBoxLayout()
        main_layout.addLayout(central_layout)

        self.chat_contents = {}
        self.selected_model = None
        self.selected_chat = None

        self.create_left_sidebar(central_layout)
        self.create_right_main_area(central_layout)

    def load_chats(self):
        chats = return_chat_history()
        chats_id = list(chats.keys())

        for chat_id in chats_id:
            chat_name = "Chat_" + str(chat_id)
            item = QListWidgetItem(chat_name)
            self.chat_list.addItem(item)
            self.chat_contents[chat_name] = chats.get(chat_id)

    def load_pdfs(self):
        sources = docs_used_in_chroma()
        self.doc_list.addItems(sources)

    def create_left_sidebar(self, parent_layout):
        sidebar_layout = QVBoxLayout()

        self.chat_list = self.create_list_widget("Chat_")
        self.doc_list = self.create_list_widget("")

        sidebar_layout.addWidget(self.chat_list)
        sidebar_layout.addWidget(self.doc_list)

        sidebar_layout.addStretch()

        self.create_sidebar_buttons(sidebar_layout)
        parent_layout.addLayout(sidebar_layout)

    def create_list_widget(self, str):
        widget = ListWidget(self)
        widget.setMaximumWidth(SIDEBAR_WIDTH)
        widget.setMinimumHeight(SIDEBAR_HEIGHT)
        widget.setStyleSheet(
            """
           QListWidget {
               border: 1px solid #D3D3D3;  /* Soft grey border */
               border-radius: 5px;  /* Rounded corners */
               padding: 5px;  /* Add some padding inside the border */
               background-color: #f9f9f9;  /* Set background to transparent */
           }
           QListWidget::item {
               padding: 5px 5px 5px 5px 20px;  /* Add some padding to the list items */
           }
       """
        )

        return widget

    def create_sidebar_buttons(self, sidebar_layout):
        button_layout = QVBoxLayout()
        sidebar_layout.addLayout(button_layout)

        buttons = [
            ("Upload Documents", self.upload_documents),
            ("New Chat", self.new_chat),
            ("Settings", self.open_settings),
        ]

        for text, func in buttons:
            button = PrimaryPushButton(text, self)
            button.clicked.connect(func)
            button_layout.addWidget(button)
            button_layout.addSpacing(5)

        sidebar_layout.addStretch()

    def upload_documents(self):
        print("Upload Documents")
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Documents (*.pdf *.docx *.md *.pptx *.xlsx *.csv")
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                tmp = select_files_and_move("data", selected_files)
                self.createWarningInfoBar()

                worker_db = Worker(run_database)
                worker_db.signals.finished.connect(self.database_operation_finished)

                self.threadpool.start(worker_db)

    def database_operation_finished(self, result):
        if result:
            self.createSuccessInfoBar(
                "Uploading Documents Successful",
                "Your files have been moved to the database",
            )
        else:
            self.createErrorInfoBar(
                "Error", "Failed to upload documents to the database"
            )

    def createWarningInfoBar(self, title, content):
        InfoBar.warning(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=20000,
            parent=self,
        )

    def createSuccessInfoBar(self, title, content):
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self,
        )

    def createErrorInfoBar(self, title, content):
        InfoBar.error(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,  # won't disappear automatically
            parent=self,
        )

    def new_chat(self):
        session_id = generate_session_id()
        chat_name = f"Chat_{session_id}"
        item = QListWidgetItem(chat_name)
        self.chat_list.addItem(item)
        self.chat_contents[chat_name] = []

    def open_settings(self):
        dialog = SettingsBox(self)
        dialog.exec_()

    def create_right_main_area(self, parent_layout):
        right_layout = QVBoxLayout()
        parent_layout.addLayout(right_layout)

        self.model_combo_box = ComboBox(self)
        self.model_combo_box.setPlaceholderText("Select Model")

        self.model_items = ["gpt-3.5-turbo-0125", "gpt-4-turbo"]
        self.model_items += list_local_models()

        self.model_combo_box.addItems(self.model_items)
        self.model_combo_box.setCurrentIndex(-1)
        self.model_combo_box.currentTextChanged.connect(self.update_model)
        right_layout.addWidget(self.model_combo_box)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(
            """
            QScrollArea {
                border-radius: 10px; /* Rounded corners */
            }
            """
        )

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #D3D3D3; /* Grey border */
                border-radius: 10px; /* Rounded corners */
                padding: 10px; /* Padding inside the border */
                background-clip: border-box; /* Make the background go under the border */
                background-color: white; /* White background */
                font-size: 16pt; 
                font-family: Open Sans, sans-serif;
            }
            """
        )
        self.chat_display.setPlaceholderText("Start chatting now!")

        self.scroll_area.setWidget(self.chat_display)
        right_layout.addWidget(self.scroll_area)

        input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your message here...")
        input_layout.addWidget(self.chat_input)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.check_and_send)
        input_layout.addWidget(self.send_button)
        
        self.summarize_button = QPushButton("Summarize")
        self.summarize_button.clicked.connect(self.summarize)
        input_layout.addWidget(self.summarize_button)
        right_layout.addLayout(input_layout)
        

    def display_chat_content(self, item):
        chat_name = item.text()
        # print(f"Selected Chat: {chat_name}") # for debug
        content = self.chat_contents.get(chat_name)
        # print(f"Content: {content}\n") # for debug

        formatted_chat = ""
        for message in content:
            role = list(message.keys())[
                0
            ]  # Get the first key (assuming there's only one key)
            data = message[role]

            if role == "human":
                formatted_chat += f"<b>User:</b> {data}<br><br>"
            elif role == "ai":
                ai_content = data.get('content', '')
                sources = data.get('sources', [])
                
                formatted_chat += f"<b>AI:</b> {ai_content}<br>"
                
                if sources:
                    formatted_chat += "<b>Sources:</b><ul>"
                    for source in sources:
                        formatted_chat += f"<li>{source}</li>"
                    formatted_chat += "</ul>"
                
                formatted_chat += "<br>"
        html_formatted_chat = markdown.markdown(formatted_chat)
        self.chat_display.setHtml(html_formatted_chat)

    def check_and_send(self):
        if self.selected_chat is None and self.selected_model is None:
            self.createWarningInfoBar(
                "Warning!", "You have not selected a model or chat yet! Please select a model and chat to continue."
            )
        elif self.selected_model is None:
            self.createWarningInfoBar(
                "Warning!", "You have not selected a model yet! Please select a model to continue."
            )
        elif self.selected_chat is None:
            self.createWarningInfoBar(
                "Warning!", "You have not selected a chat yet! Please select a chat to continue."
            )
        elif self.selected_model in ["gpt-3.5-turbo-0125", "gpt-4-turbo"] and os.getenv("OPENAI_API_KEY") is None:
            self.createWarningInfoBar(
                "Warning!", "You have not set an OpenAI API key! Please set an OpenAI API key in the settings to continue."
            )
        else:
            self.send_message()
    
    def summarize(self):
        session_id = self.selected_chat.split("_")[1]
        model = self.selected_model
        print(f"model is {model}")
        
        self.chat_display.append("<b>AI Summary:</b><br>")
        self.createWarningInfoBar(
                "In Progress", "Please wait while the model is generating a summary..."
        )
        worker_cb = Worker(summarize_docs, model, session_id)
        worker_cb.signals.summary.connect(self.handle_summary)
        
        self.threadpool.start(worker_cb)
        self.chat_input.setEnabled(False)
        
    def handle_summary(self, summary):
        if summary:
            # Set up for typing effect
            self.current_response = summary
            self.current_sources = ""  # No sources for summary
            self.source = []  # No sources for summary
            self.char_index = 0
            self.md_buffer = ""
            
            # Move cursor to end and prepare for typing
            self.chat_display.moveCursor(QTextCursor.End)
            self.cursor = self.chat_display.textCursor()
            
            # Start typing effect
            self.type_next_character()
        else:
            self.chat_input.setEnabled(True)
        
    def send_message(self):
        user_message = self.chat_input.text()
        if user_message:
            self.chat_display.append(f"<b>User:</b> {user_message}<br><br>")
            session_id = self.selected_chat.split("_")[1]
            model = self.selected_model

            worker_cb = Worker(query_rag, model, session_id, user_message)
            worker_cb.signals.result.connect(self.handle_response)
            self.threadpool.start(worker_cb)
            self.chat_input.clear()
            self.chat_input.setEnabled(False)  # Disable chat input while waiting for response

    def finish_response(self):
        self.chat_contents[self.selected_chat].append({
                "ai": {
                    "content": self.current_response,
                    "sources": self.source,
                }
        })
            
        self.cursor.insertHtml("<br><br>")
        self.chat_display.setTextCursor(self.cursor)
        self.chat_input.setEnabled(True)
        self.chat_input.setFocus()

    def type_next_character(self):
        if self.char_index < len(self.current_response):
            char = self.current_response[self.char_index]
        
            # Buffer characters to form the full Markdown input
            self.md_buffer += char

            # Convert Markdown to HTML
            if char == '\n' or self.char_index == len(self.current_response) - 1:
                html_content = markdown.markdown(self.md_buffer)
                # print(f"html_content is: {html_content}\n") # for debug
                
                # Move the cursor to the end and insert HTML
                self.cursor.movePosition(QTextCursor.End)
                self.chat_display.setTextCursor(self.cursor)
                self.chat_display.insertHtml(html_content)
                self.md_buffer = ""  # Reset buffer for next chunk

            self.char_index += 1
            self.chat_display.setTextCursor(self.cursor)
            self.chat_display.ensureCursorVisible()
            QTimer.singleShot(
                20, self.type_next_character
            ) 
        else:
            # Append sources if any
            if self.current_sources:
                self.cursor.insertHtml(self.current_sources)
            self.finish_response()

    def handle_response(self, response):
        self.current_response = response[0]
        self.current_sources = response[1]
        self.source = response[2]
        self.char_index = 0
        self.md_buffer = ""
        self.chat_display.moveCursor(QTextCursor.End)
        self.chat_display.insertHtml("<b>AI:</b> ")
        self.cursor = self.chat_display.textCursor()
        self.type_next_character()

    def update_model(self, text):
        print(f"Selected Model: {text}")
        self.selected_model = text

    def update_chat(self, item):
        self.selected_chat = item.text()
        print(f"Selected Chat: {self.selected_chat}")


if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    create_db()

    app = QApplication(sys.argv)
    window = DocAnalyzerUI()
    window.show()
    sys.exit(app.exec_())
