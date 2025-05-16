import asyncio
from models.message import Message
from typing import Optional, Dict, List, Callable
from helpers.image_utils import process_base64_image
import time

class MultiMessageBuffer:
    def __init__(self, debounce_seconds: int = 5, process_callback: Optional[Callable] = None):
        self.message_buffer: List[str] = []
        self.base64_image: Optional[str] = None
        self.debounce_seconds = debounce_seconds
        self.last_input_time = None
        self.debounce_task = None
        self.buffer_lock = None
        self.process_callback = process_callback  # Called with (combined_message, context)
        self.region = None

    async def ensure_lock(self):
        if self.buffer_lock is None:
            self.buffer_lock = asyncio.Lock()

    async def add_message(self, user_input: str, region: Optional[str] = None, base64_image: Optional[str] = None):
        await self.ensure_lock()
        async with self.buffer_lock:
            self.message_buffer.append(user_input)
            self.last_input_time = time.time()
            if region:
                self.region = region
            if base64_image:
                self.base64_image = base64_image
        if self.debounce_task is None or self.debounce_task.done():
            self.debounce_task = asyncio.create_task(self.debounce_loop())

    async def debounce_loop(self):
        await self.ensure_lock()
        while True:
            await asyncio.sleep(0.1)
            if self.last_input_time and (time.time() - self.last_input_time > self.debounce_seconds):
                await self.process_buffer()
                self.last_input_time = None
                self.debounce_task = None
                break

    async def process_buffer(self):
        await self.ensure_lock()
        async with self.buffer_lock:
            if self.message_buffer:
                combined_message = "\n".join(self.message_buffer)
                context = {"region": self.region}
                if self.base64_image:
                    context["image_data"] = self.base64_image
                if self.process_callback:
                    await self.process_callback(combined_message, context)
                self.message_buffer.clear()
                self.base64_image = None

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