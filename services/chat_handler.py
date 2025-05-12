from typing import Dict, Optional
from .prompt_builder import PromptBuilder
from .ai_service import AIService
from .query_validator import QueryValidator
from .response_builder import ResponseBuilder
from .conversation_context import ConversationContext
from .product_search_service import ProductSearchService

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
            self.response_builder,
            self.product_search_service
        )
        
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
        print("\n" + "="*80)
        print("CHAT HANDLER: STARTING MESSAGE PROCESSING")
        print("="*80)
        print(f"\nCONVERSATION CONTEXT STATE:")
        print(f"Context ID: {id(self.conversation_context)}")
        print(f"Number of messages: {len(self.conversation_context.messages)}")
        if self.conversation_context.last_search_results:
            print("Has search results: Yes")
            print(f"Exact match: {self.conversation_context.last_search_results['exact_match']}")
            print(f"Similar products: {len(self.conversation_context.last_search_results['similar_products'])}")
        else:
            print("Has search results: No")
        
        # Add user message to conversation context
        self.conversation_context.add_message('user', user_input)
        print("\nAFTER ADDING USER MESSAGE:")
        print(f"Number of messages: {len(self.conversation_context.messages)}")
        print(f"Last message role: {self.conversation_context.messages[-1].role}")
        print(f"Last message content: {self.conversation_context.messages[-1].content}")
        
        # Get region and image data from context
        region = context.get("region") if context else None
        image_data = context.get("image_data") if context else None
        
        # First, validate if the query is Lonca-related and handle image search if needed
        is_valid, response, image_search_results = await self.query_validator.validate_query(
            user_input,
            self.conversation_context,
            image_data=image_data
        )
        
        if not is_valid:
            print("\nQUERY VALIDATION: Invalid query")
            return {
                "choices": [{
                    "message": {
                        "content": response
                    }
                }]
            }
        
        # If we have image search results, update context and generate response
        if image_search_results:
            print("\nPROCESSING IMAGE SEARCH RESULTS:")
            print(f"Exact match: {image_search_results['exact_match']}")
            print(f"Similar products: {len(image_search_results['similar_products'])}")
            
            # Update conversation context with search results
            self.conversation_context.add_search_results(
                image_search_results['exact_match'],
                image_search_results['similar_products']
            )
            
            print("\nAFTER ADDING SEARCH RESULTS:")
            print(f"Last search results: {self.conversation_context.last_search_results}")
            
            # Load and format the image search response prompt
            prompt_template = self.prompt_builder._load_prompt("image_search_response_prompt.txt")
            
            # Format the similar products list
            similar_products_text = chr(10).join([
                f"- {p['name']} (Price: ${p['price']}, Stock: {p.get('total_stock', 0)} packs)" 
                for p in image_search_results['similar_products']
            ])
            
            # Format the exact match text
            exact_match_text = (
                f"{image_search_results['exact_match']['name']} (Price: ${image_search_results['exact_match']['price']}, Stock: {image_search_results['exact_match'].get('total_stock', 0)} packs)" 
                if image_search_results['exact_match'] 
                else 'None'
            )
            
            # Format the prompt
            system_prompt = prompt_template.format(
                query=user_input,
                exact_match=exact_match_text,
                similar_products=similar_products_text
            )
            
            response = await self.ai_service.get_response(system_prompt, "")
            
            # Add assistant's response to conversation context
            self.conversation_context.add_message(
                'assistant',
                response['choices'][0]['message']['content']
            )
            
            print("\nAFTER ADDING ASSISTANT RESPONSE:")
            print(f"Number of messages: {len(self.conversation_context.messages)}")
            print(f"Last message role: {self.conversation_context.messages[-1].role}")
            print(f"Last message content: {self.conversation_context.messages[-1].content[:100]}...")
            
            return response
            
        # Get conversation context
        conversation_context_text = self.conversation_context.get_conversation_context()
        print("\nCONVERSATION CONTEXT TEXT:")
        print(conversation_context_text)
            
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
        
        print("\nFINAL CONVERSATION CONTEXT STATE:")
        print(f"Number of messages: {len(self.conversation_context.messages)}")
        print(f"Last message role: {self.conversation_context.messages[-1].role}")
        print(f"Last message content: {self.conversation_context.messages[-1].content[:100]}...")
        if self.conversation_context.last_search_results:
            print("Has search results: Yes")
            print(f"Exact match: {self.conversation_context.last_search_results['exact_match']}")
            print(f"Similar products: {len(self.conversation_context.last_search_results['similar_products'])}")
        else:
            print("Has search results: No")
        
        print("\n" + "="*80)
        
        # If no relevant FAQs found, escalate to human agent
        if not self.prompt_builder.faq_service.has_relevant_faqs(user_input, region):
            escalation_response = await self.response_builder.get_escalation_response(user_input)
            return {
                "choices": [{
                    "message": {
                        "content": escalation_response
                    }
                }]
            }
        
        return response 