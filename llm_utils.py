import ollama
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()
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

def list_local_models():
    # Listing local models from Ollama
    models = ollama.list()
    model_names = [model['name'] for model in models['models']]
    model_names.remove("nomic-embed-text:latest")
    
    print(f"Local models: {model_names}")
    return model_names

# DEBUG
# if __name__ == "__main__":
#     list_local_models()