
from models.message import Message
from datetime import datetime
from typing import Optional, Dict, List
from helpers.image_utils import process_base64_image

async def receive_message(user_input: str, context: Optional[Dict] = None):

    region = context.get("region") if context else None
    image_data = context.get("image_data") if context else None

    # Process image and image description from context
    image=None
    if image_data:
        try:
            image = process_base64_image(image_data)
        except ValueError:
            image=None

    message = Message(
        role='user',
        content=user_input,
        image=image
    )

    """Store incoming messages."""
    return message

def generate_response(messages: List[Message]):
    """Combine messages and generate a response."""
    combined_message = "\n".join(messages)  # Combine messages with newlines
    # Process the combined message (e.g., send to AI model)
    response = process_combined_message(combined_message)
    return response

def process_combined_message(combined_message: str):
    """Process the combined message and generate a response."""
    # Here you would implement your logic to generate a response
    # For example, you could call your AI service with the combined message
    return f"Processed message: {combined_message}"