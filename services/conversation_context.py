from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    image_search_results: Optional[Dict] = None

class ConversationContext:
    def __init__(self):
        self.messages: List[Message] = []
        self.current_topic: Optional[str] = None
        self.last_image_search_results: Optional[Dict] = None
        
    def add_message(self, role: str, content: str, image_search_results: Optional[Dict] = None):
        """Add a new message to the conversation history."""
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            image_search_results=image_search_results
        )
        self.messages.append(message)
        
    def add_image_search_results(self, exact_match: Optional[Dict], similar_products: List[Dict]):
        """Store the latest image search results."""
        self.last_image_search_results = {
            'exact_match': exact_match,
            'similar_products': similar_products
        }
        
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
            
            # Add image search results if present
            if msg.image_search_results:
                context += "\nImage Search Results:\n"
                if msg.image_search_results['exact_match']:
                    exact = msg.image_search_results['exact_match']
                    context += f"Exact Match: {exact['name']} (Price: {exact['price']})\n"
                
                if msg.image_search_results['similar_products']:
                    context += "Similar Products:\n"
                    for product in msg.image_search_results['similar_products']:
                        context += f"- {product['name']} (Price: {product['price']})\n"
                context += "\n"
            
        return context 