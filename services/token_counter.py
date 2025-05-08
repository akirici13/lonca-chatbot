import tiktoken
from typing import Dict, Tuple

class TokenCounter:
    def __init__(self, model: str = "gpt-4.1-mini"):
        """
        Initialize the token counter with the specified model's encoding.
        
        Args:
            model (str): The model to use for token counting
        """
        self.model = model
        # Use cl100k_base encoding which works for all GPT models
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text."""
        return len(self.encoding.encode(text))
    
    def count_prompt_tokens(self, system_prompt: str, user_prompt: str) -> Dict[str, int]:
        """
        Count tokens for both system and user prompts.
        
        Args:
            system_prompt (str): The system prompt
            user_prompt (str): The user prompt
            
        Returns:
            Dict[str, int]: Dictionary containing token counts
        """
        system_tokens = self.count_tokens(system_prompt)
        user_tokens = self.count_tokens(user_prompt)
        total_tokens = system_tokens + user_tokens
        
        return {
            "system_tokens": system_tokens,
            "user_tokens": user_tokens,
            "total_tokens": total_tokens
        }
    
    def estimate_cost(self, tokens: int) -> float:
        """
        Estimate the cost of tokens based on the current model.
        
        Args:
            tokens (int): Number of tokens
            
        Returns:
            float: Estimated cost in USD
        """
        # Current prices per 1K tokens (as of March 2024)
        prices = {
            "gpt-3.5-turbo": 0.0005,    # $0.0005 per 1K tokens
            "gpt-4": 0.03,              # $0.03 per 1K tokens
            "gpt-4-turbo-preview": 0.01, # $0.01 per 1K tokens
            "gpt-4.1-mini": 0.0015,     # $0.0015 per 1K tokens
            "gpt-4o-mini": 0.001,       # $0.001 per 1K tokens
        }
        
        price_per_1k = prices.get(self.model, 0.0015)  # Default to gpt-4.1-mini
        return (tokens / 1000) * price_per_1k 