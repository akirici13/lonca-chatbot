from typing import Dict
import json
from .prompt_builder import PromptBuilder
from helpers.loader import load_json
from .conversation_context import ConversationContext

class ResponseBuilder:
    def __init__(self, ai_service):
        """Initialize the response builder with AI service."""
        self.ai_service = ai_service
        self.prompt_builder = PromptBuilder()
        self.responses = load_json(self.prompt_builder.prompts_dir / "responses.json")
        self.conversation_context = ConversationContext()
        
    async def generate_response(self, query: str, context: Dict = None) -> str:
        """
        Generate a response for a valid query.
        
        Args:
            query (str): The user's query
            context (Dict, optional): Additional context for response generation
            
        Returns:
            str: Generated response
        """
        template = self.responses["non_lonca_query"]
        system_prompt = template["system_prompt"]
        user_prompt = template["user_prompt"].format(query=query)
        
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
        template = self.responses["escalate_to_agent"]
        system_prompt = template["system_prompt"]
        user_prompt = template["user_prompt"].format(query=query)
        
        response = await self.ai_service.get_response(system_prompt, user_prompt)
        return response.get('choices', [{}])[0].get('message', {}).get('content', '') 