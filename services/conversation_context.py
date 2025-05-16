from typing import List, Dict, Optional
from datetime import datetime
from models.message import Message

class ConversationContext:
    def __init__(self):
        self.messages: List[Message] = []
        self.current_topic: Optional[str] = None
        self.last_search_results: Optional[Dict] = None
        
    def add_message(self, role: str, content: str, timestamp: Optional[datetime] = datetime.now(), search_results: Optional[Dict] = None, image_description: Optional[str] = None):
        """Add a new message to the conversation history."""
        message = Message(
            role=role,
            content=content,
            timestamp=timestamp,
            search_results=search_results,
            image_description=image_description
        )
        self.messages.append(message)
        
    def add_search_results(self, exact_match: Optional[Dict], similar_products: List[Dict]):
        """Store the latest search results."""
        self.last_search_results = {
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
            
            # Add image description if present
            if msg.image_description:
                context += f"[Image provided. Description (summary): {msg.image_description}]\n"
            
            # Add search results if present
            if msg.search_results:
                context += "\nSearch Results:\n"
                if msg.search_results['exact_match']:
                    exact = msg.search_results['exact_match']
                    context += f"Exact Match: {exact['name']} (Price: ${exact['price']}, Stock: {exact.get('total_stock', 0)} packs)\n"
                    if 'search_type' in exact:
                        context += f"Found via: {exact['search_type']}\n"
                
                if msg.search_results['similar_products']:
                    context += "Similar Products:\n"
                    for product in msg.search_results['similar_products']:
                        context += f"- {product['name']} (Price: ${product['price']}, Stock: {product.get('total_stock', 0)} packs)"
                        if 'search_type' in product:
                            context += f" (Found via: {product['search_type']})"
                        context += "\n"
                context += "\n"
            
        return context 