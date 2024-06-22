import argparse
import os
import shutil

from langchain.schema.document import Document
from llm_utils import get_embedding_function
from langchain_community.vectorstores.chroma import Chroma
from preprocess import documents_directory_loader, split_documents

CHROMA_PATH = "chroma"
DATA_PATH = "data"

types = [
    ".pdf",
    ".docx",
    ".md",
    ".pptx",
    ".xlsx",
    ".csv"
]

def load_vector_store():
    # Load the vector store db
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    return db

def run_database():
    """
    Runs the database process.

    This function checks if the database should be cleared using the --reset flag.
    If the flag is provided, the function clears the database and then proceeds to process the files.
    The function processes different file types, loads the documents from the 'data/' directory,
    splits the documents into chunks, and adds the chunks to the chroma.

    Returns:
        bool: True if the database process is completed successfully.
    """
    # Check if the database should be cleared (using the --reset flag).
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    args = parser.parse_args()
    if args.reset:
        print("✨ Clearing Database")
        clear_database()
    
    docs_used = []

    for file_type in types:
        print(f"Processing {file_type} files...")
        documents = documents_directory_loader(file_type, 'data/')
        if documents:
            docs_used.append(documents)
        chunks = split_documents(documents)
        # print(f"Chunks: {chunks}")
        add_to_chroma(file_type, chunks)

    return True

def clear_database():
    # Clear database function
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
    else:
        print("No database to clear.")

def docs_used_in_chroma():
    """
    Retrieves the list of documents used in the chroma analysis.

    Returns:
        list: A list of document IDs used in the chroma analysis.
    """
    db = load_vector_store()
    all_ids = db.get(include=[])["ids"]

    docs_used = list(set([doc_id.split(":")[0] for doc_id in all_ids]))
    print(f"Number of documents in DB: {len(docs_used)}")
    print(f"docs_used: \n{docs_used}")
    return docs_used


def add_to_chroma(file_type: str, chunks: list[Document]):
    """
    Adds new documents to the Chroma database.

    Args:
        file_type (str): The type of file being added.
        chunks (list[Document]): A list of Document objects representing the new documents.

    Returns:
        None
    """
    # Load the existing database.
    db = Chroma(
        persist_directory=CHROMA_PATH, embedding_function=get_embedding_function()
    )

    # Calculate Page IDs.
    chunks_with_ids = calculate_chunk_ids(chunks)

    # Add or Update the documents.
    existing_items = db.get(include=[])  # IDs are always included by default
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    # Only add documents that don't exist in the DB.
    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)

    if len(new_chunks):
        print(f"👉 Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        db.add_documents(new_chunks, ids=new_chunk_ids)
        # db.persist()
    else:
        print(f"✅ No new documents {file_type} to add\n")


def calculate_chunk_ids(chunks):
    # This will create IDs like "data/monopoly.pdf:6:2"
    # Page Source : Page Number : Chunk Index

    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        # If the page ID is the same as the last one, increment the index.
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        # Calculate the chunk ID.
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        # Add it to the page meta-data.
        chunk.metadata["id"] = chunk_id

    return chunks

# DEBUG
# if __name__ == "__main__":
#     run_database()
