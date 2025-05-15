from typing import Dict
import aiohttp
from helpers.api_key import get_openai_api_key

class AIService:
    def __init__(self, model: str = "gpt-4.1-mini"):
        """
        Initialize the AI service.
        
        Args:
            model (str): The model to use (default: gpt-4.1-mini)
        """
        self.model = model
        self.api_key = get_openai_api_key()
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
    async def get_classification(self, prompt: str) -> str:
        """
        Get a simple yes/no classification from the model.
        
        Args:
            prompt (str): The classification prompt
            
        Returns:
            str: The model's classification ('yes' or 'no')
        """
        try:
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            # Prepare payload
            payload = {
                "model": self.model,
                "temperature": 0.1,  # Lower temperature for more consistent responses
                "max_tokens": 10,    # We only need a short response
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a query classifier. Respond with ONLY 'yes' or 'no'."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result["choices"][0]["message"]["content"].strip().lower()
            
        except Exception as e:
            print(f"Error getting classification: {e}")
            return "no"  # Default to 'no' in case of error
        
    async def get_response(self, system_prompt: str, user_prompt: str, image_data: str = None) -> Dict:
        """
        Get response from OpenAI's model, supporting optional image input.
        
        Args:
            system_prompt (str): The system prompt defining the assistant's behavior
            user_prompt (str): The user's message and context
            image_data (str, optional): Base64-encoded image data
            
        Returns:
            Dict: The model's response
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            if image_data:
                image_url = f"data:image/jpeg;base64,{image_data}"
                payload = {
                    "model": self.model,
                    "temperature": 0.7,
                    "max_tokens": 250,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_prompt},
                                {"type": "image_url", "image_url": {'url': image_url}}
                            ]
                        }
                    ]
                }
            else:
                payload = {
                    "model": self.model,
                    "temperature": 0.7,
                    "max_tokens": 250,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ]
                }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return {
                        "choices": [{
                            "message": {
                                "content": result["choices"][0]["message"]["content"]
                            }
                        }]
                    }
        except Exception as e:
            print(f"Error getting AI response: {e}")
            return {"error": str(e)} 