from typing import Dict, Optional, Tuple
from .ai_service import AIService
from .prompt_builder import PromptBuilder
from .response_builder import ResponseBuilder
from .conversation_context import ConversationContext

class LoncaQueryService:
    def __init__(self, ai_service: AIService, prompt_builder: PromptBuilder, response_builder: ResponseBuilder):
        """
        Initialize the Lonca query service.
        
        Args:
            ai_service: The AI service instance
            prompt_builder: The prompt builder instance
            response_builder: The response builder instance
        """
        self.ai_service = ai_service
        self.prompt_builder = prompt_builder
        self.response_builder = response_builder
        
    async def handle_query(self, query: str, region: Optional[str], conversation_context: ConversationContext) -> Tuple[Dict, ConversationContext]:
        """
        Handle a Lonca-related query.
        
        Args:
            query (str): The user's query
            region (Optional[str]): The user's region
            conversation_context (ConversationContext): The current conversation context
            
        Returns:
            Tuple[Dict, ConversationContext]: The AI's response and updated conversation context
        """
        # Get conversation context
        conversation_context_text = conversation_context.get_conversation_context()
            
        # Build prompt with FAQ processing
        system_prompt, user_prompt = self.prompt_builder.build_prompt(
            query, 
            region=region,
            conversation_context=conversation_context_text
        )
        
        # Get AI response
        response = await self.ai_service.get_response(system_prompt, user_prompt)
        
        # Add assistant's response to conversation context
        conversation_context.add_message('assistant', response['choices'][0]['message']['content'])
        
        # If no relevant FAQs found, escalate to human agent
        if not self.prompt_builder.faq_service.has_relevant_faqs(query, region):
            escalation_response = await self.response_builder.get_escalation_response(query)
            response = {
                "choices": [{
                    "message": {
                        "content": escalation_response
                    }
                }]
            }
            # Add escalation response to conversation context
            conversation_context.add_message('assistant', escalation_response)
        
        return response, conversation_context 