from dotenv import load_dotenv
load_dotenv()

from langchain_community.llms.ollama import Ollama
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains.llm import LLMChain
from langchain.chains import MapReduceDocumentsChain, ReduceDocumentsChain
from langchain.chains.combine_documents.stuff import StuffDocumentsChain

from langchain_community.chat_message_histories import SQLChatMessageHistory

from preprocess import documents_directory_loader, split_documents
from db_utils import create_db

# Code for loading a pdf document and then summarize it using langchain map reduce

DATA_PATH = "data"

types = [
    ".pdf",
    ".docx",
    ".md",
    ".pptx",
    ".xlsx",
    ".csv"
]

def create_summary_chain(model):
    if model == "gpt-3.5-turbo-0125" or model == "gpt-4-turbo":
        model = ChatOpenAI(model=model)
    else:
        model = Ollama(model=model)

    # Map chain
    map_prompt = """
    The following is a set of documents:
    "{docs}"
    Based on the list of docs, please identify the main themes. If the docs are empty, just say so and do not summarize anything.
    Helpful Answer:
    """
    map_prompt_template = PromptTemplate(template=map_prompt, input_variables=["text"])
    map_chain = LLMChain(llm=model, prompt=map_prompt_template)

    # Reduce chain
    reduce_template = """
    The following is set of summaries:
    {docs}
    Take these and distill it into a final, consolidated summary of the main themes.
    Helpful Answer:
    """
    reduce_prompt = PromptTemplate.from_template(reduce_template)
    reduce_chain = LLMChain(llm=model, prompt=reduce_prompt)

    combine_documents_chain = StuffDocumentsChain(
        llm_chain=reduce_chain, document_variable_name="docs"
    )

    reduce_documents_chain = ReduceDocumentsChain(
        # This is final chain that is called.
        combine_documents_chain=combine_documents_chain,
        # If documents exceed context for `StuffDocumentsChain`
        collapse_documents_chain=combine_documents_chain,
        # The maximum number of tokens to group documents into.
        token_max=4096,
    )

    map_reduce_chain = MapReduceDocumentsChain(
        # Map chain
        llm_chain=map_chain,
        # Reduce chain
        reduce_documents_chain=reduce_documents_chain,
        # The variable name in the llm_chain to put the documents in
        document_variable_name="docs",
        # Return the results of the map steps in the output
        return_intermediate_steps=False,
    )

    return map_reduce_chain

def summarize_docs(model, session_id):
    split_docs = []
    for file_type in types:
        documents = documents_directory_loader(file_type, DATA_PATH)
        print(documents)
        splits = split_documents(documents)
        split_docs.extend(splits)

    print(f"Summarizing documents using {model}, Please wait...")

    create_db()
    chain = create_summary_chain(model)
    
    response = chain.invoke(split_docs)
    summaries = response["output_text"]

    # Add summaries to chat history
    chat_message_history = SQLChatMessageHistory(
        session_id=session_id, connection_string="sqlite:///sqlite.db", table_name="history"
    )
    chat_message_history.add_ai_message(summaries)

    print(f"Summaries:\n{summaries}")
    
    return summaries