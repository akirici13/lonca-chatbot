from typing import Tuple, Optional
from .prompt_builder import PromptBuilder
from .response_builder import ResponseBuilder
from .conversation_context import ConversationContext
from .product_search_service import ProductSearchService
from PIL import Image
import base64
import io

class QueryValidator:
    def __init__(self, ai_service, conversation_context: ConversationContext):
        """Initialize the query validator with AI service."""
        self.ai_service = ai_service
        self.prompt_builder = PromptBuilder()
        self.response_builder = ResponseBuilder(ai_service)
        self.conversation_context = conversation_context
        self.product_search_service = ProductSearchService()
        
    async def validate_query(self, query: str, image_data: Optional[str] = None) -> Tuple[bool, str, Optional[dict]]:
        """
        Validate if the query is related to Lonca's business and handle product search requests.
        
        Args:
            query (str): The user's query
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
                    image_bytes = base64.b64decode(image_data)
                    image = Image.open(io.BytesIO(image_bytes))
                except Exception as e:
                    return False, f"Error processing image: {str(e)}", None
            
            # Perform combined search
            exact_match, similar_products = self.product_search_service.search_products(query, image)
            
            # Store results in conversation context
            self.conversation_context.add_search_results(exact_match, similar_products)
            
            return True, "", {
                'exact_match': exact_match,
                'similar_products': similar_products
            }
        
        # Load classification prompt
        context = self.prompt_builder._load_context()
        
        # Get conversation context for validation
        conversation_context = self.conversation_context.get_conversation_context()
        
        system_prompt = self.prompt_builder._load_prompt("classification_prompt.txt").format(
            business_type=context['business_type'],
            company=context['company'],
            valid_topics="\n".join(f"- {topic}" for topic in context['valid_topics']),
            invalid_topics="\n".join(f"- {topic}" for topic in context['invalid_topics']),
            query=query
        )
        
        # Include conversation context in the user prompt
        user_prompt = f"Conversation Context:\n{conversation_context}\n\nCurrent Query: {query}"
        
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
 