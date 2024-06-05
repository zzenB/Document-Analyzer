import argparse
import time

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
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from get_embedding_function import get_embedding_function

chat_history = {}

CHROMA_PATH = "chroma"

PROMPT_TEMPLATE = """
The following context is from PDFs. Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer:
---

{context}

---

Answer the question based on the above context: {input}
"""

def create_chain(model):
    if model == "gpt-3.5-turbo-0125":
        model = ChatOpenAI(model=model)
    else:
        model = Ollama(model=model)

    # Prepare the DB.
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    retriever = db.as_retriever(search_kwargs={"k": 3})

    # Initialize the chains
    # prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "The following context is from a single or set of documents. Use the following pieces of context to answer the user's question. \
         If you don't know the answer, just say that you don't know, don't try to make up an answer: {context}"),
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

def get_session_history(session_id: str) -> BaseChatMessageHistory:

    if session_id not in chat_history:
        chat_history[session_id] = ChatMessageHistory()
    return chat_history[session_id]

def process_chat(chain, query_text, chat_history):
    history_chain = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

    response = history_chain.invoke(
        {"input": query_text},
        config={
            "configurable": {"session_id": "abc123"}
        }
    )

    return response

def query_rag(model):
    start_time = time.time() 

    chain = create_chain(model)
    
    while True:
        query_text = input("(Type \"q\" to quit)\n > ")
        if query_text.lower() == "q":
            print("Exiting program!")
            break
        
        response = process_chat(chain, query_text, chat_history)
        # response = process_chat(chain, query_text, chat_history)
        # chat_history.append(HumanMessage(content=user_input))
        # chat_history.append(AIMessage(content=response))

        sources = [doc.metadata.get("id", None) for doc in response["context"]]

        # For debugging:
        print(f"Response is:\n-------{response}-------\n")
        # for target_id in sources:
        #     for doc in response["context"]:
        #         if doc.metadata["id"] == target_id:
        #             print("---")
        #             print(f"For ID: {target_id}\n")
        #             print(doc.page_content)
        #             print("---\n")

        content = response["answer"]
        formatted_response = f"Response: {content}\n\nSources: {sources}"
        print(formatted_response)

    end_time = time.time()
    print(f"Time taken: {(end_time - start_time):.2f} seconds")

    # return formatted_response

if __name__ == "__main__":
    query_rag()
