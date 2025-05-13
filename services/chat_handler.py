from typing import Dict, Optional
from .prompt_builder import PromptBuilder
from .ai_service import AIService
from .query_validator import QueryValidator
from .response_builder import ResponseBuilder
from .conversation_context import ConversationContext
from .product_search_service import ProductSearchService
from .follow_up_service import FollowUpService
from .product_query_service import ProductQueryService

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
            return await self._handle_search_results(user_input, search_results)
        
        # Then, check if this is a new product search
        product_query_result = await self.product_query_service.check_product_query(
            user_input,
            image_data
        )
        if product_query_result:
            is_valid, response, search_results = product_query_result
            if not is_valid:
                return self._create_response(response)
            return await self._handle_search_results(user_input, search_results)
        
        # Finally, validate if the query is Lonca-related
        is_valid, response, _ = await self.query_validator.validate_query(
            user_input,
            self.conversation_context
        )
        
        if not is_valid:
            return self._create_response(response)
            
        # Get conversation context
        conversation_context_text = self.conversation_context.get_conversation_context()
            
        # If valid, proceed with FAQ processing
        system_prompt, user_prompt = self.prompt_builder.build_prompt(
            user_input, 
            region=region,
            conversation_context=conversation_context_text
        )
        
        # Get AI response
        response = await self.ai_service.get_response(system_prompt, user_prompt)
        
        # Add assistant's response to conversation context
        self.conversation_context.add_message('assistant', response['choices'][0]['message']['content'])
        
        # If no relevant FAQs found, escalate to human agent
        if not self.prompt_builder.faq_service.has_relevant_faqs(user_input, region):
            escalation_response = await self.response_builder.get_escalation_response(user_input)
            return self._create_response(escalation_response)
        
        return response

    async def _handle_search_results(self, query: str, search_results: dict) -> Dict:
        """
        Handle search results and generate appropriate response.
        
        Args:
            query (str): The original user query
            search_results (dict): The search results
            
        Returns:
            Dict: The AI's response
        """
        # Update conversation context with search results
        self.conversation_context.add_search_results(
            search_results['exact_match'],
            search_results['similar_products']
        )
        
        # Load and format the image search response prompt
        prompt_template = self.prompt_builder._load_prompt("image_search_response_prompt.txt")
        
        # Format the similar products list
        similar_products_text = chr(10).join([
            f"- {p['name']} (Price: ${p['price']}, Stock: {p.get('total_stock', 0)} packs)" 
            for p in search_results['similar_products']
        ])
        
        # Format the exact match text
        exact_match_text = (
            f"{search_results['exact_match']['name']} (Price: ${search_results['exact_match']['price']}, Stock: {search_results['exact_match'].get('total_stock', 0)} packs)" 
            if search_results['exact_match'] 
            else 'None'
        )
        
        # Format the prompt
        system_prompt = prompt_template.format(
            query=query,
            exact_match=exact_match_text,
            similar_products=similar_products_text
        )
        
        response = await self.ai_service.get_response(system_prompt, "")
        
        # Add assistant's response to conversation context
        self.conversation_context.add_message(
            'assistant',
            response['choices'][0]['message']['content']
        )
        
        return response 