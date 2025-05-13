import asyncio
import sys
from pathlib import Path
from PIL import Image
import base64
from io import BytesIO

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from services.chat_handler import ChatHandler
from helpers.image_utils import convert_image_to_base64

def encode_image_to_base64(image_path: str) -> str:
    """Convert an image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

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
    
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()
        
        # Check for exit command
        if user_input.lower() == 'exit':
            print("\nThank you for chatting with us. Goodbye!")
            break
        
        # Skip empty messages
        if not user_input:
            continue
        
        try:
            # Check if this is an image upload command
            if user_input.lower().startswith('image '):
                image_path = user_input[6:].strip()  # Remove 'image ' prefix
                try:
                    # Load and convert image to base64
                    image = Image.open(image_path)
                    base64_image = convert_image_to_base64(image)
                    
                    # Process message with image
                    context = {
                        "region": region,
                        "image_data": base64_image
                    }
                    response = await chat_handler.process_message(
                        "I'm searching for a product similar to this image.",
                        context=context
                    )
                except Exception as e:
                    print(f"\nError processing image: {e}")
                    continue
            else:
                # Process regular text message
                context = {"region": region}
                response = await chat_handler.process_message(user_input, context)
            
            # Print the response
            print("\nAssistant:", response.get('choices', [{}])[0].get('message', {}).get('content', 'Error'))
            
        except Exception as e:
            print(f"\nError: {e}")
        
        print("\n" + "-"*40)

if __name__ == "__main__":
    try:
        asyncio.run(interactive_chat_with_images())
    except KeyboardInterrupt:
        print("\n\nChat session ended by user. Goodbye!") 