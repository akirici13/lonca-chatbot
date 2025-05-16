import asyncio
import sys
from pathlib import Path
from PIL import Image
import aioconsole

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from services.chat_handler import ChatHandler
from services.message_service import MultiMessageBuffer
from helpers.image_utils import convert_image_to_base64

async def interactive_chat_with_images():
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
    print("Commands:")
    print("- Type 'exit' to end the conversation")
    print("- Type 'image <path>' to upload an image (e.g., 'image products/red_product.jpg')")
    print("="*80)
    
    base64_image = None

    async def process_combined_message(combined_message, context):
        try:
            response = await chat_handler.process_message(combined_message, context)
            print("\nAssistant:", response.get('choices', [{}])[0].get('message', {}).get('content', 'Error'))
        except Exception as e:
            print(f"\nError: {e}")
        print("\n" + "-"*40)

    buffer = MultiMessageBuffer(debounce_seconds=10, process_callback=process_combined_message)

    while True:
        # Get user input asynchronously
        user_input = (await aioconsole.ainput("\nYou: ")).strip()
        
        # Check for exit command
        if user_input.lower() == 'exit':
            print("\nThank you for chatting with us. Goodbye!")
            break

        if user_input.lower().startswith('image '):
            image_path = user_input[6:].strip()  # Remove 'image ' prefix
            try:
                # Load and convert image to base64
                image = Image.open(image_path)
                base64_image = convert_image_to_base64(image)
            except Exception as e:
                print(f"\nError processing image: {e}")
                continue
        
        # Skip empty messages
        if not user_input:
            continue

        print(f"[DEBUG] Buffering message: '{user_input}'")
        await buffer.add_message(user_input, region=region, base64_image=base64_image)

if __name__ == "__main__":
    try:
        asyncio.run(interactive_chat_with_images())
    except KeyboardInterrupt:
        print("\n\nChat session ended by user. Goodbye!") 