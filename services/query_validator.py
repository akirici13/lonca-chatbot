from typing import Tuple, Optional
from .prompt_builder import PromptBuilder
from .response_builder import ResponseBuilder
from .conversation_context import ConversationContext
from .product_search_service import ProductSearchService
from helpers.image_utils import process_base64_image
from PIL import Image
import base64
import io

class QueryValidator:
    def __init__(self, ai_service, prompt_builder, response_builder, product_search_service):
        """
        Initialize the query validator with required services.
        
        Args:
            ai_service: The AI service instance
            prompt_builder: The prompt builder instance
            response_builder: The response builder instance
            product_search_service: The product search service instance
        """
        self.ai_service = ai_service
        self.prompt_builder = prompt_builder
        self.response_builder = response_builder
        self.product_search_service = product_search_service
        
    async def validate_query(self, query: str, conversation_context: ConversationContext, image_data: Optional[str] = None) -> Tuple[bool, str, Optional[dict]]:
        """
        Validate if the query is related to Lonca's business and handle product search requests.
        
        Args:
            query (str): The user's query
            conversation_context (ConversationContext): The current conversation context
            image_data (Optional[str]): Base64 encoded image data if present
            
        Returns:
            Tuple[bool, str, Optional[dict]]: (is_valid, response, search_results)
                - is_valid: True if query is related to Lonca's business
                - response: Response message (either standard response or empty string)
                - search_results: Results from product search if applicable
        """
        # Check if this is a product search query
        is_product_query = await self._is_product_query(query)
        
        if is_product_query:
            # Process image if provided
            image = None
            if image_data:
                try:
                    image = process_base64_image(image_data)
                except ValueError as e:
                    return False, str(e), None
            
            # Perform combined search
            exact_match, similar_products = self.product_search_service.search_products(query, image)
            
            return True, "", {
                'exact_match': exact_match,
                'similar_products': similar_products
            }
        
        # Load classification prompt
        context = self.prompt_builder._load_context()
        
        # Get conversation context for validation
        conversation_context_text = conversation_context.get_conversation_context()
        
        system_prompt = self.prompt_builder._load_prompt("classification_prompt.txt").format(
            business_type=context['business_type'],
            company=context['company'],
            valid_topics="\n".join(f"- {topic}" for topic in context['valid_topics']),
            invalid_topics="\n".join(f"- {topic}" for topic in context['invalid_topics']),
            query=query
        )
        
        # Include conversation context in the user prompt
        user_prompt = f"Conversation Context:\n{conversation_context_text}\n\nCurrent Query: {query}"
        
        # Get classification from AI
        response = await self.ai_service.get_response(system_prompt, user_prompt)
        classification = response.get('choices', [{}])[0].get('message', {}).get('content', '').strip().lower()
        
        # Check if query is valid
        is_valid = classification == 'yes'
        
        if not is_valid:
            # Get standard response for non-Lonca queries
            response = await self.response_builder.generate_response(query)
            return False, response, None
            
        return True, "", None
    
    async def _is_product_query(self, query: str) -> bool:
        """
        Determine if the query is related to product search.
        
        Args:
            query (str): The user's query
            
        Returns:
            bool: True if query is related to product search
        """
        system_prompt = self.prompt_builder._load_prompt("product_query_classifier_prompt.txt")
        user_prompt = f"Query: {query}"
        
        response = await self.ai_service.get_response(system_prompt, user_prompt)
        classification = response.get('choices', [{}])[0].get('message', {}).get('content', '').strip().lower()
        
        return classification == 'yes'
 