import sys
from pathlib import Path
import asyncio
import aiohttp
from tqdm import tqdm
import os
import json
import chromadb
from chromadb.utils import embedding_functions
import torch
from transformers import AutoTokenizer, AutoModel
from PIL import Image
from io import BytesIO
import numpy as np

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from services.image_search_service import ImageSearchService
from services.product_search_service import ProductSearchService

class EmbeddingUpdater:
    def __init__(self):
        """Initialize the embedding updater with both text and image search services."""
        self.image_search_service = ImageSearchService()
        self.product_search_service = ProductSearchService()
        
        # Initialize text search components
        self.tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
        self.text_model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.Client()
        
    def _get_text_embedding(self, text: str) -> np.ndarray:
        """Generate text embedding using the transformer model."""
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = self.text_model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).numpy()[0]
    
    async def _process_product_batch(self, session: aiohttp.ClientSession, products: list) -> tuple:
        """Process a batch of products to generate both text and image embeddings."""
        text_embeddings = []
        image_embeddings = []
        product_data = []
        
        for product in products:
            product_id = product['id']['$oid'] if isinstance(product['id'], dict) else str(product['id'])
            
            # Generate text embedding
            product_text = f"{product['name']} {product.get('description', '')} {product.get('category', '')}"
            text_embedding = self._get_text_embedding(product_text)
            
            # Load and process image
            try:
                async with session.get(product['image_path']) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        image = Image.open(BytesIO(image_data))
                        image = self.image_search_service._preprocess_image(image)
                        image_embedding = self.image_search_service.extract_features(image)
                        
                        text_embeddings.append(text_embedding)
                        image_embeddings.append(image_embedding)
                        product_data.append({
                            'id': product_id,
                            'name': product['name'],
                            'price': product['price'],
                            'image_path': product['image_path'],
                            'text': product_text
                        })
            except Exception as e:
                print(f"Error processing product {product_id}: {str(e)}")
        
        return text_embeddings, image_embeddings, product_data
    
    async def update_embeddings(self):
        """Update both text and image embeddings for all products."""
        print("Starting embeddings update...")
        
        # Load product catalog
        catalog_path = project_root / "data" / "product_catalog.json"
        with open(catalog_path, 'r') as f:
            catalog_data = json.load(f)
        
        # Process products in batches
        batch_size = 10
        products = catalog_data['products']
        all_text_embeddings = []
        all_image_embeddings = []
        all_product_data = []
        
        async with aiohttp.ClientSession() as session:
            for i in tqdm(range(0, len(products), batch_size), desc="Processing products"):
                batch = products[i:i + batch_size]
                text_embeddings, image_embeddings, product_data = await self._process_product_batch(session, batch)
                
                all_text_embeddings.extend(text_embeddings)
                all_image_embeddings.extend(image_embeddings)
                all_product_data.extend(product_data)
        
        # Update ChromaDB collections
        print("\nUpdating ChromaDB collections...")
        
        # Update text collection
        try:
            text_collection = self.chroma_client.create_collection(
                name="product_text",
                embedding_function=embedding_functions.DefaultEmbeddingFunction()
            )
        except Exception as e:
            if "already exists" in str(e):
                self.chroma_client.delete_collection("product_text")
                text_collection = self.chroma_client.create_collection(
                    name="product_text",
                    embedding_function=embedding_functions.DefaultEmbeddingFunction()
                )
            else:
                raise e
        
        # Update image collection
        try:
            image_collection = self.chroma_client.create_collection(
                name="product_images",
                embedding_function=embedding_functions.DefaultEmbeddingFunction()
            )
        except Exception as e:
            if "already exists" in str(e):
                self.chroma_client.delete_collection("product_images")
                image_collection = self.chroma_client.create_collection(
                    name="product_images",
                    embedding_function=embedding_functions.DefaultEmbeddingFunction()
                )
            else:
                raise e
        
        # Add embeddings to collections
        print("Adding embeddings to ChromaDB...")
        
        # Add text embeddings
        text_collection.add(
            ids=[p['id'] for p in all_product_data],
            embeddings=[e.tolist() for e in all_text_embeddings],
            documents=[p['text'] for p in all_product_data],
            metadatas=[{
                'name': p['name'],
                'price': p['price'],
                'image_path': p['image_path']
            } for p in all_product_data]
        )
        
        # Add image embeddings
        image_collection.add(
            ids=[p['id'] for p in all_product_data],
            embeddings=[e.numpy().tolist() for e in all_image_embeddings],
            documents=[p['name'] for p in all_product_data],
            metadatas=[{
                'name': p['name'],
                'price': p['price'],
                'image_path': p['image_path']
            } for p in all_product_data]
        )
        
        print("Embeddings update completed successfully!")

def main():
    """Main function to run the embedding update process."""
    updater = EmbeddingUpdater()
    asyncio.run(updater.update_embeddings())

if __name__ == "__main__":
    main() 