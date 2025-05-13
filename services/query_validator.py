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
        # First check if this is a follow-up about an existing product
        existing_product_result = await self._handle_existing_product(query, conversation_context)
        if existing_product_result:
            return existing_product_result

        # Then check if this is a new product search
        product_search_result = await self._handle_product_search(query, image_data)
        if product_search_result:
            return product_search_result

        # Finally, check if the query is valid for Lonca's business
        return await self._validate_business_query(query, conversation_context)
    
    async def _handle_existing_product(self, query: str, conversation_context: ConversationContext) -> Optional[Tuple[bool, str, Optional[dict]]]:
        """
        Handle queries about existing products in the conversation context.
        
        Args:
            query (str): The user's query
            conversation_context (ConversationContext): The current conversation context
            
        Returns:
            Optional[Tuple[bool, str, Optional[dict]]]: Result tuple if this is a follow-up query, None otherwise
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

    async def _handle_product_search(self, query: str, image_data: Optional[str]) -> Optional[Tuple[bool, str, Optional[dict]]]:
        """
        Handle new product search queries.
        
        Args:
            query (str): The user's query
            image_data (Optional[str]): Base64 encoded image data if present
            
        Returns:
            Optional[Tuple[bool, str, Optional[dict]]]: Result tuple if this is a product search, None otherwise
        """
        is_product_query = await self._is_product_query(query)
        if not is_product_query:
            return None

        # Process image if provided
        image = None
        if image_data:
            try:
                image = process_base64_image(image_data)
            except ValueError as e:
                return False, str(e), None
        
        # Perform search and return only exact matches
        exact_match, _ = self.product_search_service.search_products(query, image)
        return True, "", {
            'exact_match': exact_match,
            'similar_products': []  # Empty list since we're not using similar products
        }

    async def _validate_business_query(self, query: str, conversation_context: ConversationContext) -> Tuple[bool, str, Optional[dict]]:
        """
        Validate if the query is related to Lonca's business.
        
        Args:
            query (str): The user's query
            conversation_context (ConversationContext): The current conversation context
            
        Returns:
            Tuple[bool, str, Optional[dict]]: Result tuple indicating if query is valid
        """
        context = self.prompt_builder._load_context()
        conversation_context_text = conversation_context.get_conversation_context()
        
        system_prompt = self.prompt_builder._load_prompt("classification_prompt.txt").format(
            business_type=context['business_type'],
            company=context['company'],
            valid_topics="\n".join(f"- {topic}" for topic in context['valid_topics']),
            invalid_topics="\n".join(f"- {topic}" for topic in context['invalid_topics']),
            query=query
        )
        
        user_prompt = f"Conversation Context:\n{conversation_context_text}\n\nCurrent Query: {query}"
        
        response = await self.ai_service.get_response(system_prompt, user_prompt)
        classification = response.get('choices', [{}])[0].get('message', {}).get('content', '').strip().lower()
        
        is_valid = classification == 'yes'
        
        if not is_valid:
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
 