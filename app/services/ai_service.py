from typing import Dict, Optional, Tuple
import openai

class AIService:
    def __init__(self, api_key: str, model: str = "gpt-4.1-mini"):
        """
        Initialize the AI service with OpenAI API key.
        
        Args:
            api_key (str): OpenAI API key
            model (str): The model to use (default: gpt-4.1-mini)
        """
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key
        
    async def get_response(self, system_prompt: str, user_prompt: str) -> Dict:
        """
        Get response from OpenAI's model.
        
        Args:
            system_prompt (str): The system prompt defining the assistant's behavior
            user_prompt (str): The user's message and context
            
        Returns:
            Dict: The model's response
        """
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            return response
        except Exception as e:
            print(f"Error getting AI response: {e}")
            return {"error": str(e)} 