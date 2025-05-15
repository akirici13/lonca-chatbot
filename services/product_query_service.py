from typing import Optional, Tuple, Dict
from PIL import Image
from .ai_service import AIService
from .prompt_builder import PromptBuilder
from .product_search_service import ProductSearchService
from helpers.image_utils import process_base64_image

class ProductQueryService:
    def __init__(self, ai_service: AIService, prompt_builder: PromptBuilder, product_search_service: ProductSearchService):
        """
        Initialize the product query service.
        
        Args:
            ai_service: The AI service instance
            prompt_builder: The prompt builder instance
            product_search_service: The product search service instance
        """
        self.ai_service = ai_service
        self.prompt_builder = prompt_builder
        self.product_search_service = product_search_service
        
    async def check_product_query(self, query: str, image: Optional[str] = None, image_description: Optional[str] = None) -> Optional[Tuple[bool, str, Optional[dict]]]:
        """
        Check if the query is related to product search and handle it if it is.
        
        Args:
            query (str): The user's query
            image (Optional[str]): Base64 encoded image data if present
            image_description (Optional[str]): Description of the image, if available
            
        Returns:
            Optional[Tuple[bool, str, Optional[dict]]]: Result tuple if this is a product query, None otherwise
                - bool: True if query is valid
                - str: Response message (empty string for valid queries)
                - dict: Search results if applicable
        """
        is_product_query = await self._is_product_query(query, image_description)
        if not is_product_query:
            return None
        
        print("\n[ProductQueryService] Handling new product search query")
        # Perform search and return only exact matches
        exact_match, _ = self.product_search_service.search_products(query, image)
        return True, "", {
            'exact_match': exact_match,
            'similar_products': []  # Empty list since we're not using similar products
        }

    async def _is_product_query(self, query: str, image_description: Optional[str] = None) -> bool:
        """
        Determine if the query is related to product search.
        
        Args:
            query (str): The user's query
            image (Optional[Image.Image]): Image if provided
            
        Returns:
            bool: True if query is related to product search
        """
        # If image description is provided, add its description to the query
        if image_description:
            query = f"{query}\nImage Description: {image_description}"

        # Check if the combined query is product-related
        system_prompt = self.prompt_builder._load_prompt("product_query_classifier_prompt.txt")
        user_prompt = f"Query: {query}"
        
        response = await self.ai_service.get_response(system_prompt, user_prompt)
        classification = response.get('choices', [{}])[0].get('message', {}).get('content', '').strip().lower()
        
        return classification == 'yes' 