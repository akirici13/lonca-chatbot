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
from torchvision import transforms
from torchvision.models import resnet50, ResNet50_Weights

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from services.image_search_service import ImageSearchService
from services.product_search_service import ProductSearchService

class EmbeddingUpdater:
    def __init__(self):
        """Initialize the embedding updater with both text and image search services."""
        self.catalog_path = project_root / "data" / "product_catalog_elisa.json"
        self.embeddings_path = project_root / "data" / "product_embeddings_elisa.pkl"
        # Image model and transform (copied from ImageSearchService)
        self.model = resnet50(weights=ResNet50_Weights.DEFAULT)
        self.model.eval()
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        # Text model
        self.tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
        self.text_model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
        self.chroma_client = chromadb.Client()
        
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        return image
    
    def _extract_features(self, image: Image.Image) -> torch.Tensor:
        image = self._preprocess_image(image)
        image_tensor = self.transform(image).unsqueeze(0)
        with torch.no_grad():
            features = self.model(image_tensor)
        return features.squeeze()
    
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
            
            # Process all images in image_paths
            image_paths = product.get('image_paths', [product.get('image_path')])
            for idx, image_url in enumerate(image_paths):
                try:
                    async with session.get(image_url) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            image = Image.open(BytesIO(image_data))
                            image_embedding = self._extract_features(image)
                            
                            text_embeddings.append(text_embedding)
                            image_embeddings.append(image_embedding)
                            product_data.append({
                                'id': f"{product_id}_{idx}",
                                'name': product['name'],
                                'price': product['price'],
                                'image_path': image_url,
                                'text': product_text
                            })
                except Exception as e:
                    print(f"Error processing product {product_id} image {image_url}: {str(e)}")
        
        return text_embeddings, image_embeddings, product_data
    
    async def update_embeddings(self):
        """Update both text and image embeddings for all products."""
        print("Starting embeddings update...")
        
        # Load product catalog
        with open(self.catalog_path, 'r') as f:
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
        
        # Save embeddings as a pickle file for ImageSearchService compatibility
        with open(self.embeddings_path, 'wb') as f:
            import pickle
            # Save as (products_dict, embeddings_dict)
            products_dict = {p['id']: {'product_id': p['id'].split('_')[0], 'name': p['name'], 'price': p['price'], 'image_url': p['image_path']} for p in all_product_data}
            embeddings_dict = {p['id']: e.numpy() for p, e in zip(all_product_data, all_image_embeddings)}
            pickle.dump((products_dict, embeddings_dict), f)
        
        print("Embeddings update completed successfully!")

def main():
    """Main function to run the embedding update process."""
    updater = EmbeddingUpdater()
    asyncio.run(updater.update_embeddings())

if __name__ == "__main__":
    main() 