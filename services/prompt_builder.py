from pathlib import Path
from typing import Dict, List, Optional, Tuple
from .faq_service import FAQService
from helpers.loader import load_text, load_json

class PromptBuilder:
    def __init__(self, prompts_dir: str = "prompts", faq_service=None):
        """Initialize the prompt builder with the prompts directory."""
        self.prompts_dir = Path(prompts_dir)
        self.faq_service = faq_service or FAQService()
        self.system_prompt = self._load_prompt("instructions.txt")
        
    def _load_prompt(self, filename: str) -> str:
        """
        Load a prompt from a file.
        
        Args:
            filename (str): Name of the prompt file
            
        Returns:
            str: Content of the prompt file
        """
        return load_text(self.prompts_dir / filename)
        
    def _load_context(self) -> Dict:
        """
        Load business context from JSON file.
        
        Returns:
            Dict: Business context data
        """
        return load_json(self.prompts_dir / "context.json")
        
    def build_prompt(self, user_message: str, region: Optional[str] = None, conversation_context: str = None) -> Tuple[str, str]:
        """
        Build the complete prompt with system instructions and relevant FAQs.
        
        Args:
            user_message (str): The user's message
            region (Optional[str]): Region to filter FAQs by
            conversation_context (Optional[str]): Recent conversation history
            
        Returns:
            Tuple[str, str]: (system_prompt, user_prompt)
                - system_prompt: System instructions with relevant FAQs and conversation context
                - user_prompt: The user's message
        """
        # Get relevant FAQs
        print(f"[PromptBuilder] Calling get_relevant_faqs with region: {region}")
        relevant_faqs = self.faq_service.get_relevant_faqs(user_message, region=region)
        print(f"[PromptBuilder] Relevant FAQs for query '{user_message}' and region '{region}': {relevant_faqs}")
        
        # Format FAQs
        faq_text = ""
        if relevant_faqs:
            faq_text = self.faq_service.format_faqs_for_prompt(relevant_faqs)
            self.system_prompt += faq_text
        
        # Add conversation context if available
        if conversation_context:
            self.system_prompt += f"\n\n{conversation_context}"
        
        # Build user prompt
        user_prompt = f"User message: {user_message}"
        
        return self.system_prompt, user_prompt 