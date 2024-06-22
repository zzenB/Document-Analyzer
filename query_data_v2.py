import dotenv
from dotenv import load_dotenv
load_dotenv()

from langchain_community.vectorstores.chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama
from langchain_openai import ChatOpenAI

# For chains
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

# For chat history
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import MessagesPlaceholder

# from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from vector_store import load_vector_store
from db_utils import update_message_with_sources

chat_history = {}

CHROMA_PATH = "chroma"

def create_chain(model: str):
    if model == "gpt-3.5-turbo-0125" or model == "gpt-4-turbo":
        model = ChatOpenAI(model=model)
    else:
        model = Ollama(model=model)
    
    # Prepare the DB.
    db = load_vector_store()
    retriever = db.as_retriever(search_kwargs={"k": 3})

    # Initialize the chains
    # prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are a virtual assistant chatbot responsible for answering user's questions about documents. The following context is from a single or set of documents. Use ONLY the following pieces of context to answer the user's question. If you don't know the answer, just say that you don't know, don't try to make up an answer: {context}"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ])

    document_chain = create_stuff_documents_chain(
        llm=model, 
        prompt=prompt_template
    )

    retriever_prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        ("human", "Given the above conversation, generate a search query to look up in order to get information relevant to the conversation")
    ])

    history_aware_retriever = create_history_aware_retriever(
        llm=model,
        retriever=retriever,
        prompt=retriever_prompt
    )

    retrieval_chain = create_retrieval_chain(
        history_aware_retriever, 
        document_chain
    )
    return retrieval_chain

def process_chat(chain, query_text, session_id):

    history_chain = RunnableWithMessageHistory(
        chain,
        # get_session_history,
        lambda session_id: SQLChatMessageHistory(
            session_id=session_id, connection_string="sqlite:///sqlite.db", table_name="history"
        ),
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

    response = history_chain.invoke(
        {"input": query_text},
        config={
            "configurable": {"session_id": session_id},
        }
    )
    sources = [doc.metadata.get("id", None) for doc in response["context"]]
    return response, sources


def query_rag(model: str, session_id: str, query_text: str):
    chain = create_chain(model)
    response, sources = process_chat(chain, query_text, session_id)

    f_answer = f"{response["answer"]}<br>"
    f_sources = f"<b>Sources:</b><ul>"
    for source in sources:
        f_sources += f"<li>{source}</li>"
    f_sources += "</ul>"
    
    print(f"f_answer: {f_answer}")
    print(f"f_sources: {f_sources}")
    formatted_response = [f_answer, f_sources, sources]
    update_message_with_sources(session_id, sources)
    
    return formatted_response
if __name__ == "__main__":
    print(query_rag("gpt-3.5-turbo-0125", "4", "What is fuzzy set then?"))
