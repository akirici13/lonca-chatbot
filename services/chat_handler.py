from typing import Dict, Optional
from .prompt_builder import PromptBuilder
from .ai_service import AIService
from .query_validator import QueryValidator
from .response_builder import ResponseBuilder
from .conversation_context import ConversationContext
from .product_search_service import ProductSearchService
from .follow_up_service import FollowUpService
from .product_query_service import ProductQueryService
from .search_result_service import SearchResultService
from .lonca_query_service import LoncaQueryService

class ChatHandler:
    def __init__(self, model: str = "gpt-4.1-mini"):
        """
        Initialize the chat handler with required services.
        
        Args:
            model (str): The model to use (default: gpt-4.1-mini)
        """
        # Initialize core services
        self.ai_service = AIService(model)
        self.prompt_builder = PromptBuilder()
        self.conversation_context = ConversationContext()
        self.product_search_service = ProductSearchService()
        
        # Initialize dependent services with shared instances
        self.response_builder = ResponseBuilder(self.ai_service, self.prompt_builder)
        self.query_validator = QueryValidator(
            self.ai_service,
            self.prompt_builder,
            self.response_builder
        )
        self.follow_up_service = FollowUpService(self.ai_service, self.prompt_builder)
        self.product_query_service = ProductQueryService(
            self.ai_service,
            self.prompt_builder,
            self.product_search_service
        )
        self.search_result_service = SearchResultService(self.ai_service, self.prompt_builder)
        self.lonca_query_service = LoncaQueryService(
            self.ai_service,
            self.prompt_builder,
            self.response_builder
        )

    def _create_response(self, content: str) -> Dict:
        """
        Create a standardized response format.
        
        Args:
            content (str): The response content
            
        Returns:
            Dict: Standardized response format
        """
        return {
            "choices": [{
                "message": {
                    "content": content
                }
            }]
        }
        
    async def process_message(self, user_input: str, context: Optional[Dict] = None) -> Dict:
        """
        Process a user message and return the AI response.
        
        Args:
            user_input (str): The user's message
            context (Dict, optional): Additional context for the conversation
                - image_data: Base64 encoded image data if present
                - region: The user's region
            
        Returns:
            Dict: The AI's response
        """
        # Add user message to conversation context
        self.conversation_context.add_message('user', user_input)
        
        # Get region and image data from context
        region = context.get("region") if context else None
        image_data = context.get("image_data") if context else None
        
        # First, check if this is a follow-up about an existing product
        follow_up_result = await self.follow_up_service.check_follow_up(
            user_input,
            self.conversation_context
        )
        if follow_up_result:
            is_valid, response, search_results = follow_up_result
            if not is_valid:
                return self._create_response(response)
            return await self.search_result_service.handle_search_results(
                user_input,
                search_results,
                self.conversation_context
            )
        
        # Then, check if this is a new product search
        product_query_result = await self.product_query_service.check_product_query(
            user_input,
            image_data
        )
        if product_query_result:
            is_valid, response, search_results = product_query_result
            if not is_valid:
                return self._create_response(response)
            return await self.search_result_service.handle_search_results(
                user_input,
                search_results,
                self.conversation_context
            )
        
        # Finally, validate if the query is Lonca-related
        is_valid, response, _ = await self.query_validator.validate_query(
            user_input,
            self.conversation_context
        )
        
        if not is_valid:
            return self._create_response(response)
            
        # Handle Lonca-related query
        return await self.lonca_query_service.handle_query(
            user_input,
            region,
            self.conversation_context
        ) 