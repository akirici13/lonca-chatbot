import os
from typing import Dict, Optional, Tuple
from pathlib import Path
from .faq_service import FAQService

class PromptBuilder:
    def __init__(self):
        """Initialize the prompt builder with paths to different prompt files."""
        self.prompts_dir = Path("prompts")
        
        # Load system prompt
        self.system_prompt = self._load_prompt("system/guidelines.txt")
        
        # Initialize FAQ service
        self.faq_service = FAQService()
        
    def _load_prompt(self, relative_path: str) -> str:
        """Load a prompt from a file."""
        try:
            with open(self.prompts_dir / relative_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"Warning: Prompt file not found: {relative_path}")
            return ""
            
    def build_prompt(self, user_message: str, region: str = None) -> Tuple[str, str]:
        """
        Build the complete prompt based on the user's message.
        
        Args:
            user_message (str): The user's message
            region (str, optional): The region to filter FAQs by
            
        Returns:
            Tuple[str, str]: (system_prompt, user_prompt)
        """
        # Start with the base system prompt
        system_prompt = self.system_prompt
        
        # Get relevant FAQs
        relevant_faqs = self.faq_service.get_relevant_faqs(user_message, region)
        
        # Add relevant FAQs to the system prompt
        if relevant_faqs:
            system_prompt += self.faq_service.format_faqs_for_prompt(relevant_faqs)
            
        # Build the user prompt
        user_prompt = f"User message: {user_message}"
        
        return system_prompt, user_prompt 