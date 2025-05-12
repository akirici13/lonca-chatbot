import asyncio
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from services.chat_handler import ChatHandler

async def interactive_chat():
    # Initialize chat handler
    print("Initializing chat handler...")
    chat_handler = ChatHandler()
    
    # Get user's region
    print("\nAvailable regions: Europe, Turkey, Other, Own")
    while True:
        region = input("\nPlease select your region: ").strip()
        if region in ["Europe", "Turkey", "Other", "Own"]:
            break
        print("Invalid region. Please choose from: Europe, Turkey, Other, Own")
    
    print(f"\nWelcome to the Lonca Chatbot! (Region: {region})")
    print("Type 'exit' to end the conversation.")
    print("="*80)
    
    while True:
        # Get user input
        user_message = input("\nYou: ").strip()
        
        # Check for exit command
        if user_message.lower() == 'exit':
            print("\nThank you for chatting with us. Goodbye!")
            break
        
        # Skip empty messages
        if not user_message:
            continue
        
        try:
            # Process message with context
            context = {"region": region}
            response = await chat_handler.process_message(user_message, context)
            
            # Print the response
            print("\nAssistant:", response.get('choices', [{}])[0].get('message', {}).get('content', 'Error'))
            
        except Exception as e:
            print(f"\nError: {e}")
        
        print("\n" + "-"*40)

if __name__ == "__main__":
    try:
        asyncio.run(interactive_chat())
    except KeyboardInterrupt:
        print("\n\nChat session ended by user. Goodbye!") 