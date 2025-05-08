import asyncio
from services.chat_handler import ChatHandler

async def interactive_chat():
    """
    Run an interactive chat session with the AI.
    Users can type messages and get responses in real-time.
    Type 'exit', 'quit', or press Ctrl+C to end the conversation.
    """
    chat_handler = ChatHandler()
    
    print("\nWelcome to the B2B Fashion Supplier Chatbot!")
    print("Type 'exit' or 'quit' to end the conversation.")
    print("----------------------------------------\n")
    
    try:
        while True:
            # Get user input
            user_message = input("\nYou: ").strip()
            
            # Check for exit commands
            if user_message.lower() in ['exit', 'quit']:
                print("\nThank you for using our chatbot. Goodbye!")
                break
            
            # Skip empty messages
            if not user_message:
                continue
            
            # Get AI response
            print("\nAI: ", end='', flush=True)
            response = await chat_handler.process_message(user_message)
            
            # Add a blank line for better readability
            print("\n")
            
    except KeyboardInterrupt:
        print("\n\nChat session ended by user. Goodbye!")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Chat session ended.")

if __name__ == "__main__":
    try:
        asyncio.run(interactive_chat())
    except KeyboardInterrupt:
        print("\nChat session ended by user. Goodbye!") 