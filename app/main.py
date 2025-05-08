import asyncio
import os
from dotenv import load_dotenv
from services.chat_handler import ChatHandler

async def main():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    # Initialize chat handler
    chat_handler = ChatHandler(api_key)
    
    # Example conversation
    test_messages = [
        "What are your delivery times?",
        "Do you have any summer collection items in stock?",
        "What's your return policy?"
    ]
    
    for message in test_messages:
        response = await chat_handler.process_message(message)
        await asyncio.sleep(1)  # Small delay between messages

if __name__ == "__main__":
    asyncio.run(main()) 