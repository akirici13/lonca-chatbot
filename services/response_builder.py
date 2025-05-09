from typing import Dict
import json
from .prompt_builder import PromptBuilder

class ResponseBuilder:
    def __init__(self, ai_service):
        """Initialize the response builder with AI service."""
        self.ai_service = ai_service
        self.prompt_builder = PromptBuilder()
        
    async def generate_response(self, query: str, context: Dict = None) -> str:
        """
        Generate a response for a valid query.
        
        Args:
            query (str): The user's query
            context (Dict, optional): Additional context for response generation
            
        Returns:
            str: Generated response
        """
        system_prompt = self.prompt_builder._load_prompt("response_prompt.txt")
        user_prompt = f"Query: {query}\nContext: {json.dumps(context) if context else 'None'}"
        
        response = await self.ai_service.get_response(system_prompt, user_prompt)
        return response.get('choices', [{}])[0].get('message', {}).get('content', '')
        
    async def get_escalation_response(self, query: str) -> str:
        """
        Generate an escalation response when no relevant FAQs are found.
        
        Args:
            query (str): The user's query
            
        Returns:
            str: Escalation response
        """
        system_prompt = self.prompt_builder._load_prompt("escalation_prompt.txt")
        user_prompt = f"Query: {query}"
        
        response = await self.ai_service.get_response(system_prompt, user_prompt)
        return response.get('choices', [{}])[0].get('message', {}).get('content', '') 