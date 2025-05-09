import json
import os
from typing import Dict, Any, Tuple
from services.ai_service import AIService

class QueryValidator:
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
        self.context = self._load_context()
        self.classification_prompt = self._load_classification_prompt()
        self.response_templates = self._load_response_templates()
    
    def _load_context(self) -> Dict[str, Any]:
        """Load business context from JSON file."""
        context_path = os.path.join('prompts', 'context.json')
        with open(context_path, 'r') as f:
            return json.load(f)
    
    def _load_classification_prompt(self) -> str:
        """Load classification prompt template."""
        prompt_path = os.path.join('prompts', 'classification_prompt.txt')
        with open(prompt_path, 'r') as f:
            return f.read()
    
    def _load_response_templates(self) -> Dict[str, Dict[str, str]]:
        """Load response templates from JSON file."""
        templates_path = os.path.join('prompts', 'responses.json')
        with open(templates_path, 'r') as f:
            return json.load(f)
    
    async def validate_query(self, query: str) -> Tuple[bool, str]:
        """
        Validate if a query is related to Lonca's business.
        
        Args:
            query: The user's query to validate
            
        Returns:
            Tuple of (is_valid, response)
            - is_valid: Boolean indicating if query is related to Lonca
            - response: Response message if query is not related
        """
        # Build system prompt from template
        system_prompt = self.classification_prompt.format(
            business_type=self.context['business_type'],
            company=self.context['company'],
            valid_topics="\n".join(f"- {topic}" for topic in self.context['valid_topics']),
            invalid_topics="\n".join(f"- {topic}" for topic in self.context['invalid_topics']),
            query=query
        )
        
        # Get classification from AI
        user_prompt = f"Query to classify: {query}"
        response = await self.ai_service.get_response(system_prompt, user_prompt)
        is_valid = response["choices"][0]["message"]["content"].strip().lower() == 'yes'
        
        if not is_valid:
            # Generate dynamic response for non-Lonca queries
            response = await self._generate_response('non_lonca_query', query)
            return False, response["choices"][0]["message"]["content"]
        
        return True, ""
    
    async def _generate_response(self, template_key: str, query: str) -> Dict:
        """
        Generate a response using the specified template.
        
        Args:
            template_key: Key for the response template to use
            query: The user's query
            
        Returns:
            Dict: The model's response
        """
        template = self.response_templates[template_key]
        user_prompt = template['user_prompt'].format(query=query)
        
        return await self.ai_service.get_response(
            template['system_prompt'],
            user_prompt
        )
    
    async def get_escalation_response(self, query: str) -> str:
        """
        Generate a response for escalating to a human agent.
        
        Args:
            query: The user's query
            
        Returns:
            Response message for escalation
        """
        response = await self._generate_response('escalate_to_agent', query)
        return response["choices"][0]["message"]["content"] 