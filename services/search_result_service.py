from typing import Dict, Tuple
from .ai_service import AIService
from .prompt_builder import PromptBuilder
from .conversation_context import ConversationContext

class SearchResultService:
    def __init__(self, ai_service: AIService, prompt_builder: PromptBuilder):
        """
        Initialize the search result service.
        
        Args:
            ai_service: The AI service instance
            prompt_builder: The prompt builder instance
        """
        self.ai_service = ai_service
        self.prompt_builder = prompt_builder
        
    async def handle_search_results(self, query: str, search_results: dict, conversation_context: ConversationContext, region: str) -> Tuple[Dict, ConversationContext]:
        """
        Handle search results and generate appropriate response.
        
        Args:
            query (str): The original user query
            search_results (dict): The search results
            conversation_context (ConversationContext): The current conversation context
            
        Returns:
            Tuple[Dict, ConversationContext]: The AI's response and updated conversation context
        """
        print("\n[SearchResultService] Processing search results")
        # Update conversation context with search results
        conversation_context.add_search_results(
            search_results['exact_match'],
            search_results['similar_products']
        )
        
        # Load and format the image search response prompt
        prompt_template = self.prompt_builder._load_prompt("image_search_response_prompt.txt")

        relevant_faqs = self.prompt_builder.faq_service.get_relevant_faqs(query, region=region)

        # Format FAQs
        faq_text = ""
        if relevant_faqs:
            faq_text = self.prompt_builder.faq_service.format_faqs_for_prompt(relevant_faqs)
        
        # Format the similar products list
        similar_products_text = chr(10).join([
            f"- {p['name']} (Price: ${p['price']}, Stock: {p.get('total_stock', 0)} packs)" 
            for p in search_results['similar_products']
        ])
        
        # Format the exact match text
        exact_match_text = (
            f"{search_results['exact_match']['name']} (Price: ${search_results['exact_match']['price']}, Stock: {search_results['exact_match'].get('total_stock', 0)} packs)" 
            if search_results['exact_match'] 
            else 'None'
        )
        
        # Format the prompt
        system_prompt = prompt_template.format(
            conversation_context=conversation_context.get_conversation_context(),
            query=query,
            faq=faq_text,
            exact_match=exact_match_text,
            similar_products=similar_products_text
        )
        
        response = await self.ai_service.get_response(system_prompt, "")
        
        # Add assistant's response to conversation context
        conversation_context.add_message(
            'assistant',
            response['choices'][0]['message']['content']
        )
        
        return response, conversation_context 