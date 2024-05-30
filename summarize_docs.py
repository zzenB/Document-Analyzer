import time
from langchain_community.llms.ollama import Ollama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.prompts import PromptTemplate
from langchain.schema.document import Document
from langchain.chains.summarize import load_summarize_chain
from langchain_openai import ChatOpenAI

# Set the OpenAI API key
import os
os.environ["OPENAI_API_KEY"] = "my_key"

# Code for loading a pdf document and then summarize it using langchain map reduce
def load_documents(file_path):
    document_loader = PyPDFDirectoryLoader(file_path)
    return document_loader.load()

def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)

def summarize_docs(model):
    start_time = time.time() 
    documents = load_documents("data")
    split_docs = split_documents(documents)

    print(f"Summarizing documents using {model}, Please wait...")
    
    if model == "gpt-3.5-turbo-0125":
        model = ChatOpenAI(model=model)
    else:
        model = Ollama(model=model)

    # Summarize the documents using load_summarize_chain
    map_prompt = """
    Write a concise summary of the following:
    "{text}"
    CONCISE SUMMARY:
    """
    map_prompt_template = PromptTemplate(template=map_prompt, input_variables=["text"])

    summary_chain = load_summarize_chain(llm=model, chain_type="map_reduce", map_prompt=map_prompt_template)
    summaries = summary_chain.run(split_docs)
    print(summaries)

    end_time = time.time()
    print(f"Time taken: {(end_time - start_time):.2f} seconds")

    return summaries

