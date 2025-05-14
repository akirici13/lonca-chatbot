from typing import Dict
import json
from .prompt_builder import PromptBuilder
from .conversation_context import ConversationContext
from helpers.loader import load_json

class ResponseBuilder:
    def __init__(self, ai_service, prompt_builder):
        """
        Initialize the response builder with required services.
        
        Args:
            ai_service: The AI service instance
            prompt_builder: The prompt builder instance
        """
        self.ai_service = ai_service
        self.prompt_builder = prompt_builder
        self.responses = load_json(self.prompt_builder.prompts_dir / "responses.json")
        
    async def generate_response(self, query: str, conversation_context: ConversationContext) -> str:
        """
        Generate a response for a valid query.
        
        Args:
            query (str): The user's query
            conversation_context (ConversationContext): The current conversation context
            
        Returns:
            str: Generated response
        """
        template = self.responses["non_lonca_query"]
        system_prompt = template["system_prompt"].format(
            conversation_context=conversation_context.get_conversation_context()
        )
        user_prompt = template["user_prompt"].format(query=query)
        
        response = await self.ai_service.get_response(system_prompt, user_prompt)
        return response.get('choices', [{}])[0].get('message', {}).get('content', '')
        
    async def get_escalation_response(self, query: str, conversation_context: ConversationContext) -> str:
        """
        Generate an escalation response when no relevant FAQs are found.
        
        Args:
            query (str): The user's query
            conversation_context (ConversationContext): The current conversation context
            
        Returns:
            str: Escalation response
        """
        template = self.responses["escalate_to_agent"]
        system_prompt = template["system_prompt"].format(
            conversation_context=conversation_context.get_conversation_context()
        )
        user_prompt = template["user_prompt"].format(query=query)
        
        response = await self.ai_service.get_response(system_prompt, user_prompt)
        return response.get('choices', [{}])[0].get('message', {}).get('content', '') 