import asyncio
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import base64
import uuid
from services.chat_handler import ChatHandler
from services.message_service import MultiMessageBuffer
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify ["http://localhost:3000"] for more security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store: session_id -> {buffer, messages, region, base64_image}
sessions: Dict[str, dict] = {}
DEBOUNCE_SECONDS = 10

class MessageIn(BaseModel):
    message: str
    image: Optional[str] = None  # base64
    region: Optional[str] = None
    session_id: Optional[str] = None

@app.post("/message")
async def post_message(msg: MessageIn):
    # Session management
    session_id = msg.session_id or str(uuid.uuid4())
    if session_id not in sessions:
        chat_handler = ChatHandler()
        buffer = MultiMessageBuffer(debounce_seconds=DEBOUNCE_SECONDS, process_callback=None)
        sessions[session_id] = {
            'buffer': buffer,
            'messages': [],
            'region': msg.region or 'Europe',
            'chat_handler': chat_handler,
            'base64_image': None,
            'pending': False,
        }
    session = sessions[session_id]
    # Only add to buffer if message or image is present
    if msg.message or msg.image:
        user_msg = {'role': 'user', 'content': msg.message}
        if msg.image:
            user_msg['image'] = msg.image
            session['base64_image'] = msg.image
        session['messages'].append(user_msg)
        # Add to buffer
        async def process_combined_message(combined_message, context):
            session['pending'] = True
            try:
                response = await session['chat_handler'].process_message(combined_message, context)
                assistant_msg = {
                    'role': 'assistant',
                    'content': response.get('choices', [{}])[0].get('message', {}).get('content', 'Error')
                }
                session['messages'].append(assistant_msg)
            except Exception as e:
                session['messages'].append({'role': 'assistant', 'content': f'Error: {e}'})
            session['pending'] = False
        session['buffer'].process_callback = process_combined_message
        await session['buffer'].add_message(msg.message, region=session['region'], base64_image=session['base64_image'])
    # Check if debounce timer is running
    pending = session['pending'] or (session['buffer'].debounce_task and not session['buffer'].debounce_task.done())
    return JSONResponse({
        'messages': session['messages'],
        'pending': pending,
        'session_id': session_id
    }) 