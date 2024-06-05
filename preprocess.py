from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import PyPDFDirectoryLoader, Docx2txtLoader, UnstructuredMarkdownLoader, UnstructuredExcelLoader, UnstructuredPowerPointLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document

types = {
    ".pdf": PyPDFDirectoryLoader,
    ".docx": Docx2txtLoader,
    ".md": UnstructuredMarkdownLoader,
    ".pptx": UnstructuredPowerPointLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".csv": CSVLoader,
}

def documents_directory_loader(file_type, DATA_PATH):
    document_loader = DirectoryLoader(
        path=DATA_PATH, 
        glob=f"**/*{file_type}", 
        loader_cls=types[file_type]
    )
    return document_loader.load()

# def load_documents(DATA_PATH):
#     document_loader = PyPDFDirectoryLoader(DATA_PATH, extract_images=True)
#     return document_loader.load()

def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1024,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)