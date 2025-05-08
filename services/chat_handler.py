from typing import Dict, Optional
from .prompt_builder import PromptBuilder
from .ai_service import AIService
from helpers.token_counter import TokenCounter

class ChatHandler:
    def __init__(self, model: str = "gpt-4.1-mini"):
        """
        Initialize the chat handler with required services.
        
        Args:
            model (str): The model to use (default: gpt-4.1-mini)
        """
        self.prompt_builder = PromptBuilder()
        self.ai_service = AIService(model)
        self.token_counter = TokenCounter(model)
        
    async def process_message(self, user_input: str, context: Optional[Dict] = None) -> Dict:
        """
        Process a user message and return the AI response.
        
        Args:
            user_input (str): The user's message
            context (Dict, optional): Additional context for the conversation
            
        Returns:
            Dict: The AI's response
        """
        # Build the prompts
        system_prompt, user_prompt = self.prompt_builder.build_prompts(user_input, context)
        
        # Count tokens and estimate cost
        token_counts = self.token_counter.count_prompt_tokens(system_prompt, user_prompt)
        estimated_cost = self.token_counter.estimate_cost(token_counts["total_tokens"])
        
        # Get AI response
        response = await self.ai_service.get_response(system_prompt, user_prompt)
        
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