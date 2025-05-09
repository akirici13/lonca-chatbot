from typing import Dict, Optional
from .prompt_builder import PromptBuilder
from .ai_service import AIService
from .query_validator import QueryValidator
from helpers.token_counter import TokenCounter

class ChatHandler:
    def __init__(self, model: str = "gpt-4.1-mini"):
        """
        Initialize the chat handler with required services.
        
        Args:
            model (str): The model to use (default: gpt-4.1-mini)
        """
        self.ai_service = AIService(model)
        self.prompt_builder = PromptBuilder()
        self.token_counter = TokenCounter(model)
        self.query_validator = QueryValidator(self.ai_service)
        
    async def process_message(self, user_input: str, context: Optional[Dict] = None) -> Dict:
        """
        Process a user message and return the AI response.
        
        Args:
            user_input (str): The user's message
            context (Dict, optional): Additional context for the conversation
            
        Returns:
            Dict: The AI's response
        """
        # First, validate if the query is Lonca-related
        is_valid, response = await self.query_validator.validate_query(user_input)
        
        if not is_valid:
            return {
                "choices": [{
                    "message": {
                        "content": response
                    }
                }]
            }
            
        # If valid, proceed with FAQ processing
        system_prompt, user_prompt = self.prompt_builder.build_prompt(user_input, context.get("region") if context else None)
        
        # Count tokens and estimate cost
        token_counts = self.token_counter.count_prompt_tokens(system_prompt, user_prompt)
        estimated_cost = self.token_counter.estimate_cost(token_counts["total_tokens"])
        
        # Get AI response
        response = await self.ai_service.get_response(system_prompt, user_prompt)
        
        # If no relevant FAQs found, escalate to human agent
        if not self.prompt_builder.faq_service.has_relevant_faqs(user_input):
            return {
                "choices": [{
                    "message": {
                        "content": "I apologize, but I need to connect you with a human agent to better assist you with this specific query about Lonca."
                    }
                }]
            }
        
        # Print conversation and token information
        print("\n=== Conversation ===")
        print(f"User: {user_input}")
        print(f"AI: {response.get('choices', [{}])[0].get('message', {}).get('content', 'Error')}")
        print("\n=== Token Information ===")
        print(f"Model: {self.ai_service.model}")
        print(f"System Prompt Tokens: {token_counts['system_tokens']}")
        print(f"User Prompt Tokens: {token_counts['user_tokens']}")
        print(f"Total Tokens: {token_counts['total_tokens']}")
        print(f"Estimated Cost: ${estimated_cost:.6f}")
        print("===================\n")
        
        return response 