from typing import Dict, Optional
from .prompt_builder import PromptBuilder
from .ai_service import AIService

class ChatHandler:
    def __init__(self, api_key: str):
        """
        Initialize the chat handler with required services.
        
        Args:
            api_key (str): OpenAI API key
        """
        self.prompt_builder = PromptBuilder()
        self.ai_service = AIService(api_key)
        
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
        
        # Get AI response
        response = await self.ai_service.get_response(system_prompt, user_prompt)
        
        # Print conversation for debugging
        print("\n=== Conversation ===")
        print(f"User: {user_input}")
        print(f"AI: {response.get('choices', [{}])[0].get('message', {}).get('content', 'Error')}")
        print("===================\n")
        
        return response 