import argparse
import time
from langchain_community.vectorstores.chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama
from langchain_openai import ChatOpenAI

from get_embedding_function import get_embedding_function

# Set the OpenAI API key
import os
os.environ["OPENAI_API_KEY"] = "my_key"

CHROMA_PATH = "chroma"

PROMPT_TEMPLATE = """
The following context is from PDFs. Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer:

{context}

---

Answer the question based on the above context: {question}
"""


def question_answer(query_text, model):
    return query_rag(query_text, model)


def query_rag(query_text, model):
    start_time = time.time() 
    # Prepare the DB.
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_score(query_text, k=3)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    print(prompt)

    if model == "gpt-3.5-turbo-0125":
        model = ChatOpenAI(model=model)
    else:
        model = Ollama(model=model)
    
    response_text = model.predict(prompt)

    sources = [doc.metadata.get("id", None) for doc, _score in results]
    # formatted_sources = ", ".join([str(source) for source in sources])
    formatted_response = f"Response: {response_text}\nSources: {sources}"
    print(formatted_response)
    end_time = time.time()
    print(f"Time taken: {(end_time - start_time):.2f} seconds")

    return "Response: " + response_text + "\nSources: " + str(sources)

# if __name__ == "__main__":
#     main()
