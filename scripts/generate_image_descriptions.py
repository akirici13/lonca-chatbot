import json
import requests
import os
import sys
from io import BytesIO
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services.ai_service import AIService
from services.prompt_builder import PromptBuilder
from services.image_description_service import ImageDescriptionService
from helpers.image_utils import convert_image_to_base64
import asyncio

CATALOG_PATH = "data/product_catalog_multi_image.json"
OUTPUT_PATH = "data/product_image_descriptions.json"

async def main():
    # Load product catalog
    with open(CATALOG_PATH, 'r') as f:
        catalog = json.load(f)
    products = catalog['products']

    # Set up services
    ai_service = AIService()
    prompt_builder = PromptBuilder()
    image_desc_service = ImageDescriptionService(ai_service, prompt_builder)

    results = {}
    for product in products:
        product_id = product['id']['$oid'] if isinstance(product['id'], dict) else str(product['id'])
        image_urls = product.get('image_paths') or []
        if not image_urls:
            print(f"No image for product {product_id}")
            continue
        image_url = image_urls[0]
        try:
            resp = requests.get(image_url)
            resp.raise_for_status()
            image = Image.open(BytesIO(resp.content)).convert('RGB')
            base64_img = convert_image_to_base64(image)
            desc = await image_desc_service.get_image_description(base64_img)
            print(f"{product_id}: {desc}")
            results[product_id] = {
                'description': desc,
                'image_url': image_url,
                'name': product.get('name', '')
            }
        except Exception as e:
            print(f"Error for {product_id}: {e}")

    with open(OUTPUT_PATH, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Saved descriptions to {OUTPUT_PATH}")

if __name__ == "__main__":
    asyncio.run(main()) 