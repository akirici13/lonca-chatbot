from typing import Tuple, Optional
from .prompt_builder import PromptBuilder
from .response_builder import ResponseBuilder
from .conversation_context import ConversationContext

class QueryValidator:
    def __init__(self, ai_service, prompt_builder, response_builder):
        """
        Initialize the query validator with required services.
        
        Args:
            ai_service: The AI service instance
            prompt_builder: The prompt builder instance
            response_builder: The response builder instance
        """
        self.ai_service = ai_service
        self.prompt_builder = prompt_builder
        self.response_builder = response_builder
        
    async def validate_query(self, query: str, conversation_context: ConversationContext) -> Tuple[bool, str]:
        """
        Validate if the query is related to Lonca's business.
        
        Args:
            query (str): The user's query
            conversation_context (ConversationContext): The current conversation context
            
        Returns:
            Tuple[bool, str, Optional[dict]]: (is_valid, response, search_results)
                - is_valid: True if query is related to Lonca's business
                - response: Response message (either standard response or empty string)
                - search_results: None for business validation
        """
        context = self.prompt_builder._load_context()
        conversation_context_text = conversation_context.get_conversation_context()
        
        system_prompt = self.prompt_builder._load_prompt("classification_prompt.txt").format(
            business_type=context['business_type'],
            company=context['company'],
            valid_topics="\n".join(f"- {topic}" for topic in context['valid_topics']),
            invalid_topics="\n".join(f"- {topic}" for topic in context['invalid_topics']),
            query=query
        )
        
        user_prompt = f"Conversation Context:\n{conversation_context_text}\n\nCurrent Query: {query}"
        
        response = await self.ai_service.get_response(system_prompt, user_prompt)
        classification = response.get('choices', [{}])[0].get('message', {}).get('content', '').strip().lower()
        
        is_valid = classification == 'yes'
        
        if not is_valid:
            print("\n[QueryValidator] Query is not related to Lonca's business")
            response = await self.response_builder.generate_response(query)
            return False, response
            
        print("\n[QueryValidator] Query is related to Lonca's business")
        return True, ""
 