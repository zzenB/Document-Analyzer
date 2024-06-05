from upload_files import select_files_and_move
from summarize_docs import summarize_docs
from query_data_v2 import query_rag
from populate_database import run_database

def show_menu():
    print("PDF Analyzer")
    print("------------")
    print("1. Upload PDF files")
    print("2. Summarize PDF content")
    print("3. Chat with the bot")
    print("4. Select model")
    print("5. Exit")

def enter_to_continue():
    input("\nPress Enter to continue...\n")

def select_model():
    print("\nSelect the model you want to use:")
    print("1. Llama2")
    print("2. Llama3")
    print("3. Phi3-Mini")
    print("4. GPT-3.5 Turbo (Online)")
    choice = input("Enter your choice (1-4): ")
    
    if choice == '1':
        return "llama2"
    elif choice == '2':
        return "llama3"
    elif choice == '3':
        return "phi3:mini"
    elif choice == '4':
        return "gpt-3.5-turbo-0125"
    else:
        print("Invalid choice. Please try again.\n")

def chat_bot():
    print("Starting chat bot...")
    # Your code for the chat bot goes here

def main():
    model = ""
    while True:
        show_menu()
        choice = input("Enter your choice (1-4): ")

        if choice == '1':
            check = select_files_and_move("data")

            if check:
                print("PDF files uploaded successfully.")
                print("Processing the uploaded files into a database...")
                run_database()
            else:
                print("No files uploaded.")

            enter_to_continue()
        elif choice == '2':
            if model:
                summarize_docs(model)
                enter_to_continue()
            else:
                print("Please select a model first.")
                enter_to_continue()
        elif choice == '3':
            if model:
                # query = input("Enter your question: ")
                query_rag(model)
                enter_to_continue()
            else:
                print("Please select a model first.")
                enter_to_continue()
        elif choice == '4':
            model = select_model()
            print(f"Selected model is {model}\n")
        elif choice == '5':
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please try again.\n")

if __name__ == '__main__':
    main()