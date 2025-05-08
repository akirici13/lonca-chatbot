import asyncio
from services.chat_handler import ChatHandler

async def main():
    # Initialize chat handler
    chat_handler = ChatHandler()
    
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