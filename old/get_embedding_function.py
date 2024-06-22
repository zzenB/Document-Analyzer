from langchain_community.embeddings.ollama import OllamaEmbeddings

def get_embedding_function():
    """
    Returns the embedding function used for the vector store.
    For now only OllamaEmbeddings is supported

    Returns:
        embeddings: The embedding function.
    """
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    return embeddings
