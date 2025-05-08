import os
from typing import Dict, Tuple

class PromptBuilder:
    def __init__(self):
        self.instructions_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'instructions.txt')
        self.examples_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'examples.txt')
        self.system_prompt = self._load_instructions()
        self.examples = self._load_examples()
    
    def _load_instructions(self) -> str:
        """Load system instructions from file."""
        try:
            with open(self.instructions_path, 'r') as file:
                return file.read().strip()
        except FileNotFoundError:
            print(f"Warning: Instructions file not found at {self.instructions_path}")
            return "You are a helpful B2B fashion supplier assistant."
    
    def _load_examples(self) -> str:
        """Load example conversations from file."""
        try:
            with open(self.examples_path, 'r') as file:
                return file.read().strip()
        except FileNotFoundError:
            print(f"Warning: Examples file not found at {self.examples_path}")
            return ""
    
    def build_prompts(self, user_input: str, context: dict = None) -> Tuple[str, str]:
        """
        Builds system and user prompts for the AI model.
        
        Args:
            user_input (str): The user's message
            context (dict, optional): Additional context like order history, product info
            
        Returns:
            Tuple[str, str]: A tuple containing (system_prompt, user_prompt)
        """
        # System prompt is loaded from instructions file
        system_prompt = self.system_prompt
        
        # Build user prompt with examples and current input
        user_prompt = ""
        
        # Add examples if available
        if self.examples:
            user_prompt += f"{self.examples}\n\n"
        
        # Add current user input
        user_prompt += f"Current Question: {user_input}"
        
        # Add context if available
        if context:
            user_prompt += f"\n\nContext: {context}"
        
        return system_prompt, user_prompt 