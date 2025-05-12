from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime

class ConversationContext:
    def __init__(self):
        self.messages: List[Message] = []
        self.current_topic: Optional[str] = None
        
    def add_message(self, role: str, content: str):
        """Add a new message to the conversation history."""
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now()
        )
        self.messages.append(message)
        
    def get_recent_messages(self, limit: Optional[int] = None) -> List[Message]:
        """
        Get messages from the conversation.
        
        Args:
            limit (Optional[int]): Number of most recent messages to return. If None, returns all messages.
            
        Returns:
            List[Message]: List of messages
        """
        if limit is None:
            return self.messages
        return self.messages[-limit:]
        
    def get_conversation_context(self) -> str:
        """Get the conversation context."""
        recent_messages = self.get_recent_messages()
        if not recent_messages:
            return ""
            
        context = "Recent conversation:\n"
        for msg in recent_messages:
            context += f"{msg.role.capitalize()}: {msg.content}\n"
            
        return context 