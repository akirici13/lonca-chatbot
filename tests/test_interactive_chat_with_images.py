import asyncio
import sys
from pathlib import Path
from PIL import Image
import base64
from io import BytesIO
import time
import aioconsole

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
    
    message_buffer = []
    base64_image = None
    debounce_seconds = 3
    last_input_time = None
    debounce_task = None
    buffer_lock = asyncio.Lock()

    async def process_buffer():
        nonlocal message_buffer, base64_image
        async with buffer_lock:
            if message_buffer:
                print(f"\n[DEBUG] Processing buffer with {len(message_buffer)} message(s)...")
                combined_message = "\n".join(message_buffer)
                context = {"region": region}
                if base64_image:
                    context["image_data"] = base64_image
                try:
                    response = await chat_handler.process_message(combined_message, context)
                    print("\nAssistant:", response.get('choices', [{}])[0].get('message', {}).get('content', 'Error'))
                except Exception as e:
                    print(f"\nError: {e}")
                message_buffer.clear()
                base64_image = None
                print("\n" + "-"*40)

    async def debounce_loop():
        nonlocal last_input_time, debounce_task
        print(f"[DEBUG] Debounce timer started. Waiting for {debounce_seconds} seconds of inactivity...")
        while True:
            await asyncio.sleep(0.1)
            if last_input_time and (time.time() - last_input_time > debounce_seconds):
                print(f"[DEBUG] Debounce timer expired. No new messages for {debounce_seconds} seconds.")
                await process_buffer()
                last_input_time = None
                debounce_task = None
                break

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

        async with buffer_lock:
            print(f"[DEBUG] Buffering message: '{user_input}'")
            message_buffer.append(user_input)
            last_input_time = time.time()
        if debounce_task is None or debounce_task.done():
            print(f"[DEBUG] Starting debounce timer...")
            debounce_task = asyncio.create_task(debounce_loop())

if __name__ == "__main__":
    try:
        asyncio.run(interactive_chat_with_images())
    except KeyboardInterrupt:
        print("\n\nChat session ended by user. Goodbye!") 