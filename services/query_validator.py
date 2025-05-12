from typing import Tuple
from .prompt_builder import PromptBuilder
from .response_builder import ResponseBuilder
from .conversation_context import ConversationContext

class QueryValidator:
    def __init__(self, ai_service):
        """Initialize the query validator with AI service."""
        self.ai_service = ai_service
        self.prompt_builder = PromptBuilder()
        self.response_builder = ResponseBuilder(ai_service)
        self.conversation_context = ConversationContext()
        
    async def validate_query(self, query: str) -> Tuple[bool, str]:
        """
        Validate if the query is related to Lonca's business.
        
        Args:
            query (str): The user's query
            
        Returns:
            Tuple[bool, str]: (is_valid, response)
                - is_valid: True if query is related to Lonca's business
                - response: Response message (either standard response or empty string)
        """
        
        # Load classification prompt
        context = self.prompt_builder._load_context()
        system_prompt = self.prompt_builder._load_prompt("classification_prompt.txt").format(
            business_type=context['business_type'],
            company=context['company'],
            valid_topics="\n".join(f"- {topic}" for topic in context['valid_topics']),
            invalid_topics="\n".join(f"- {topic}" for topic in context['invalid_topics']),
            query=query
        )
        user_prompt = f"Query: {query}"
        
        # Get classification from AI
        response = await self.ai_service.get_response(system_prompt, user_prompt)
        classification = response.get('choices', [{}])[0].get('message', {}).get('content', '').strip().lower()
        
        # Check if query is valid
        is_valid = classification == 'yes'
        
        if not is_valid:
            # Get standard response for non-Lonca queries
            response = await self.response_builder.generate_response(query)
            return False, response
            
        return True, ""
 