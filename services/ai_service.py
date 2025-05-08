from typing import Dict, Optional, Tuple
from openai import AsyncOpenAI
from helpers.api_key import get_openai_api_key

class AIService:
    def __init__(self, model: str = "gpt-4.1-mini"):
        """
        Initialize the AI service.
        
        Args:
            model (str): The model to use (default: gpt-4.1-mini)
        """
        self.model = model
        self.client = AsyncOpenAI(api_key=get_openai_api_key())
        
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
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            return {"choices": [{"message": {"content": response.choices[0].message.content}}]}
        except Exception as e:
            print(f"Error getting AI response: {e}")
            return {"error": str(e)} 