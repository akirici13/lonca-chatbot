from typing import Optional, Tuple, Dict
from .conversation_context import ConversationContext
from .ai_service import AIService
from .prompt_builder import PromptBuilder

class FollowUpService:
    def __init__(self, ai_service: AIService, prompt_builder: PromptBuilder):
        """
        Initialize the follow-up service.
        
        Args:
            ai_service: The AI service instance
            prompt_builder: The prompt builder instance
        """
        self.ai_service = ai_service
        self.prompt_builder = prompt_builder
        
    async def check_follow_up(self, query: str, conversation_context: ConversationContext) -> Optional[Tuple[bool, str, Optional[dict]]]:
        """
        Check if the query is a follow-up question about an existing product.
        
        Args:
            query (str): The user's query
            conversation_context (ConversationContext): The current conversation context
            
        Returns:
            Optional[Tuple[bool, str, Optional[dict]]]: Result tuple if this is a follow-up query, None otherwise
                - bool: True if query is valid
                - str: Response message (empty string for valid queries)
                - dict: Search results if applicable
        """
        if not conversation_context.last_search_results or not conversation_context.last_search_results['exact_match']:
            return None

        is_follow_up = await self._is_follow_up_about_product(
            query, 
            conversation_context.last_search_results['exact_match']
        )
        
        if is_follow_up:
            return True, "", conversation_context.last_search_results
            
        return None

    async def _is_follow_up_about_product(self, query: str, product: dict) -> bool:
        """
        Determine if the query is a follow-up question about an existing product.
        
        Args:
            query (str): The user's query
            product (dict): The product information
            
        Returns:
            bool: True if query is about the existing product
        """
        system_prompt = self.prompt_builder._load_prompt("follow_up_classifier_prompt.txt").format(
            product_name=product['name'],
            product_id=product['product_id']
        )
        user_prompt = f"Query: {query}"
        
        response = await self.ai_service.get_response(system_prompt, user_prompt)
        classification = response.get('choices', [{}])[0].get('message', {}).get('content', '').strip().lower()
        
        return classification == 'yes' 