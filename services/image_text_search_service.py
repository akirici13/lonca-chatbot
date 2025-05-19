import json
import os
from typing import Optional, Dict
from difflib import SequenceMatcher
from services.ai_service import AIService
from services.prompt_builder import PromptBuilder
from services.image_description_service import ImageDescriptionService
from helpers.image_utils import convert_image_to_base64

class ImageTextSearchService:
    def __init__(self, descriptions_path: str = "data/product_image_descriptions.json"):
        self.descriptions_path = descriptions_path
        if not os.path.exists(descriptions_path):
            raise FileNotFoundError(f"Descriptions file not found: {descriptions_path}")
        with open(descriptions_path, 'r') as f:
            self.product_descriptions = json.load(f)
        self.ai_service = AIService()
        self.prompt_builder = PromptBuilder()
        self.image_desc_service = ImageDescriptionService(self.ai_service, self.prompt_builder)

    async def search_by_image(self, image) -> Optional[Dict]:
        # Accepts PIL.Image or base64 string
        if not isinstance(image, str):
            base64_img = convert_image_to_base64(image)
        else:
            base64_img = image
        # Get description for the input image
        desc = await self.image_desc_service.get_image_description(base64_img)
        if not desc:
            return None
        # Find the most similar product description
        best_score = 0
        best_product = None
        for product_id, info in self.product_descriptions.items():
            product_desc = info.get('description', '')
            score = SequenceMatcher(None, desc, product_desc).ratio()
            if score > best_score:
                best_score = score
                best_product = {
                    'product_id': product_id,
                    'score': score,
                    'description': product_desc,
                    'name': info.get('name', ''),
                    'image_url': info.get('image_url', '')
                }
        return best_product if best_product and best_score > 0.5 else None 