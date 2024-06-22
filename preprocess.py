from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredMarkdownLoader, UnstructuredExcelLoader, UnstructuredPowerPointLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document

types = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".md": UnstructuredMarkdownLoader,
    ".pptx": UnstructuredPowerPointLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".csv": CSVLoader,
}

def documents_directory_loader(file_type, DATA_PATH):
    """
    Load documents from a directory based on the specified file type.

    Args:
        file_type (str): The file type to filter the documents (e.g., '.txt', '.pdf').
        DATA_PATH (str): The path to the directory containing the documents.

    Returns:
        list: A list of loaded documents.

    """
    document_loader = DirectoryLoader(
        path=DATA_PATH, 
        glob=f"**/*{file_type}", 
        loader_cls=types[file_type],
        use_multithreading=True
    )
    print(f"loader_cls: {types[file_type]}")
    return document_loader.load()

def split_documents(documents: list[Document]):
    """
    Splits a list of documents into smaller chunks using a text splitter.

    Args:
        documents (list[Document]): The list of documents to be split.

    Returns:
        list[Document]: The list of split documents.

    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1024,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)