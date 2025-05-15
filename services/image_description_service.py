from .ai_service import AIService
from .prompt_builder import PromptBuilder
from helpers.image_utils import process_base64_image
from typing import Optional, Tuple

class ImageDescriptionService:
    def __init__(self, ai_service: AIService, prompt_builder: PromptBuilder):
        self.ai_service = ai_service
        self.prompt_builder = prompt_builder

    async def get_image_description(self, image_data: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Process the base64 image and return a detailed description using the AI service.
        Args:
            image_data (str): Base64 encoded image data
        Returns:
            Optional[str]: Description of the image, or None if processing fails
        """
        try:
            image = process_base64_image(image_data)
        except ValueError:
            return None, None

        # Use a detailed prompt for image description
        system_prompt = self.prompt_builder._load_prompt("image_description_prompt.txt")
        user_prompt = f"Query: {image}"
        response = await self.ai_service.get_response(system_prompt, user_prompt)
        image_description = response.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
        return image, image_description 