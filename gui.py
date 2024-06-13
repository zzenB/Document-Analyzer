import sys
import sqlite3
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qfluentwidgets import *
from qfluentwidgets.components.widgets.acrylic_label import AcrylicLabel
# from qfluentwidgets import ListWidget, ComboBox, PrimaryPushButton
# from qfluentwidgets import InfoBarIcon, InfoBar, PushButton, setTheme, Theme, FluentIcon, InfoBarPosition, InfoBarManager

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
    result = pyqtSignal(str)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        result = self.fn(*self.args, **self.kwargs)
        if type(result) == bool:
            self.signals.finished.emit(result)
        else:
            self.signals.result.emit(result)


# @InfoBarManager.register('Custom')
# class CustomInfoBarManager(InfoBarManager):
#    """ Custom info bar manager """

#    def _pos(self, infoBar: InfoBar, parentSize=None):
#        p = infoBar.parent()
#        parentSize = parentSize or p.size()

#        # the position of first info bar
#        x = (parentSize.width() - infoBar.width()) // 2
#        y = (parentSize.height() - infoBar.height()) // 2

#        # get the position of current info bar
#        index = self.infoBars[p].index(infoBar)
#        for bar in self.infoBars[p][0:index]:
#            y += (bar.height() + self.spacing)

#        return QPoint(x, y)

#    def _slideStartPos(self, infoBar: InfoBar):
#        pos = self._pos(infoBar)
#        return QPoint(pos.x(), pos.y() - 16)

class DocAnalyzerUI(QMainWindow):
   def __init__(self):
       super().__init__()

       self.init_ui()
       self.load_chats()
       self.load_pdfs()
       if self.chat_list.count() < 1:
           self.new_chat()

       self.threadpool = QThreadPool()
       print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

       self.chat_list.itemClicked.connect(self.display_chat_content)
       self.chat_list.itemClicked.connect(self.update_chat)

   def init_ui(self):
       self.setWindowTitle("Document Analyzer")
       self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
       self.setWindowFlags(Qt.FramelessWindowHint)  # make the window frameless
    #    self.setAttribute(Qt.WA_TranslucentBackground)

       central_widget = QWidget()
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
           self.createSuccessInfoBar("Uploading Documents Successful", "Your files have been moved to the database")
       else:
           self.createErrorInfoBar("Error", "Failed to upload documents to the database")

   def createWarningInfoBar(self):
       InfoBar.warning(
           title='Uploading Documents to the database...',
           content="Please wait for the app to upload your documents before chatting",
           orient=Qt.Horizontal,
           isClosable=False,   # disable close button
           position=InfoBarPosition.TOP_RIGHT,
           duration=20000,
           parent=self
       )

   def createSuccessInfoBar(self, title, content):
       InfoBar.success(
           title=title,
           content=content,
           orient=Qt.Horizontal,
           isClosable=True,
           position=InfoBarPosition.TOP_RIGHT,
           duration=2000,
           parent=self
       )
   def createErrorInfoBar(self, title, content):
        InfoBar.error(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,    # won't disappear automatically
            parent=self
        )

   def new_chat(self):
        session_id = generate_session_id()
        chat_name = f"Chat_{session_id}"
        item = QListWidgetItem(chat_name)
        self.chat_list.addItem(item)
        self.chat_contents[chat_name] = []

   def open_settings(self):
        print("Open Settings")

   def create_right_main_area(self, parent_layout):
        right_layout = QVBoxLayout()
        parent_layout.addLayout(right_layout)

        self.model_combo_box = ComboBox(self)
        self.model_combo_box.setPlaceholderText("Select Model")
        
        model_items = ["gpt-3.5-turbo-0125", "gpt-4-turbo"]
        model_items += list_local_models()

        self.model_combo_box.addItems(model_items)
        self.model_combo_box.setCurrentIndex(-1)
        self.model_combo_box.currentTextChanged.connect(self.update_model)
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
    
   def display_chat_content(self, item):
        chat_name = item.text()
        print(f"Selected Chat: {chat_name}")
        content = self.chat_contents.get(chat_name)
        print(f"Content: {content}\n")

        chat_display = QTextEdit()
        chat_display.setReadOnly(True)

        formatted_chat = ""
        for message in content:
            role = list(message.keys())[0]  # Get the first key (assuming there's only one key)
            content = message[role]

            if role == 'human':
                formatted_chat += f"<b>User:</b> {content}<br><br>"
            elif role == 'ai':
                formatted_chat += f"<b>AI:</b> {content}<br>"

        self.chat_display.setText(formatted_chat)

   def send_message(self):
        user_message = self.chat_input.text()
        if user_message:
            self.chat_display.append(f"<b>User:</b> {user_message}<br><br>")
            session_id = self.selected_chat.split("_")[1]
            model = self.selected_model

            worker_cb = Worker(query_rag, model, session_id, user_message)
            worker_cb.signals.result.connect(self.handle_response)
            self.threadpool.start(worker_cb)
            # self.chat_input.clear()

   def handle_response(self, response):
        self.chat_display.append(response)
        self.chat_contents[self.selected_chat].append({response})
        

   def update_model(self, text):
        print(f"Selected Model: {text}")
        self.selected_model = text
   def update_chat(self, item):
        self.selected_chat = item.text()
        print(f"Selected Chat: {self.selected_chat}")

if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    create_db()

    app = QApplication(sys.argv)
    window = DocAnalyzerUI()
    window.show()
    sys.exit(app.exec_())

    