from PIL import Image
import torch
from torchvision import transforms
from torchvision.models import resnet50, ResNet50_Weights
import numpy as np
from typing import List, Dict, Optional, Tuple
import os
import json
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
import pickle
import requests
from io import BytesIO
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from helpers.chroma_config import get_chroma_client

class ImageSearchService:
    def __init__(self, catalog_path: str = "data/product_catalog.json", embeddings_path: str = "data/product_embeddings.pkl"):
        """Initialize the image search service with a pre-trained model."""
        # Load pre-trained ResNet model
        self.model = resnet50(weights=ResNet50_Weights.DEFAULT)
        self.model.eval()  # Set to evaluation mode
        
        # Define image transformations
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        # Initialize paths
        self.catalog_path = catalog_path
        self.embeddings_path = embeddings_path
        
        # Load or create embeddings
        self.product_catalog, self.embeddings = self._load_or_create_embeddings()
        
        # Initialize ChromaDB with shared configuration
        self.chroma_client = get_chroma_client()
        try:
            self.collection = self.chroma_client.create_collection(
                name="product_images",
                embedding_function=embedding_functions.DefaultEmbeddingFunction()
            )
        except Exception as e:
            if "already exists" in str(e):
                # If collection exists, get it
                self.collection = self.chroma_client.get_collection(
                    name="product_images",
                    embedding_function=embedding_functions.DefaultEmbeddingFunction()
                )
            else:
                raise e
        
        # Add embeddings to ChromaDB if not already added
        self._initialize_chroma_collection()
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to ensure it's in the correct format.
        
        Args:
            image (PIL.Image): Input image
            
        Returns:
            PIL.Image: Preprocessed image
        """
        # Convert to RGB if not already
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Remove alpha channel if present
        if image.mode == 'RGBA':
            # Create a white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            # Paste the image on the background
            background.paste(image, mask=image.split()[3])  # 3 is the alpha channel
            image = background
        
        return image

    async def _load_image_from_url_async(self, session: aiohttp.ClientSession, image_url: str) -> Optional[Image.Image]:
        """Load an image from URL asynchronously."""
        try:
            async with session.get(image_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    image = Image.open(BytesIO(image_data))
                    return self._preprocess_image(image)
                else:
                    print(f"Failed to load image from {image_url}: HTTP {response.status}")
                    return None
        except Exception as e:
            print(f"Error loading image from URL {image_url}: {str(e)}")
            return None

    async def _process_product_batch(self, session: aiohttp.ClientSession, products: List[Dict]) -> Tuple[Dict, Dict]:
        """Process a batch of products asynchronously."""
        products_dict = {}
        embeddings_dict = {}
        
        # Create tasks for all products in the batch
        tasks = []
        for product in products:
            product_id = product['id']['$oid'] if isinstance(product['id'], dict) else str(product['id'])
            tasks.append(self._load_image_from_url_async(session, product['image_path']))
        
        # Wait for all images to load
        images = await asyncio.gather(*tasks)
        
        # Process loaded images
        for product, image in zip(products, images):
            if image is not None:
                product_id = product['id']['$oid'] if isinstance(product['id'], dict) else str(product['id'])
                features = self.extract_features(image)
                
                products_dict[product_id] = {
                    'name': product['name'],
                    'price': product['price'],
                    'image_path': product['image_path']
                }
                embeddings_dict[product_id] = features.numpy()
        
        return products_dict, embeddings_dict

    def _load_or_create_embeddings(self) -> Tuple[Dict[str, Dict], Dict[str, np.ndarray]]:
        """Load existing embeddings or create new ones if they don't exist."""
        if os.path.exists(self.embeddings_path):
            print("Loading existing embeddings...")
            with open(self.embeddings_path, 'rb') as f:
                return pickle.load(f)
        
        print("Creating new embeddings...")
        # Load product catalog
        with open(self.catalog_path, 'r') as f:
            catalog_data = json.load(f)
        
        # Process products in batches
        batch_size = 10  # Process 10 products at a time
        products = catalog_data['products']
        all_products = {}
        all_embeddings = {}
        
        async def process_all_products():
            async with aiohttp.ClientSession() as session:
                for i in tqdm(range(0, len(products), batch_size), desc="Processing products"):
                    batch = products[i:i + batch_size]
                    products_dict, embeddings_dict = await self._process_product_batch(session, batch)
                    all_products.update(products_dict)
                    all_embeddings.update(embeddings_dict)
        
        # Run the async processing
        asyncio.run(process_all_products())
        
        # Save embeddings
        with open(self.embeddings_path, 'wb') as f:
            pickle.dump((all_products, all_embeddings), f)
        
        return all_products, all_embeddings
    
    def _initialize_chroma_collection(self):
        """Initialize ChromaDB collection with product embeddings."""
        # Check if collection is empty
        if self.collection.count() == 0:
            print("Adding embeddings to ChromaDB...")
            # Prepare data for ChromaDB
            ids = []
            embeddings = []
            documents = []
            metadatas = []
            
            for product_id, product in self.product_catalog.items():
                ids.append(product_id)
                embeddings.append(self.embeddings[product_id].tolist())
                documents.append(product['name'])
                metadatas.append({
                    'price': product['price'],
                    'image_path': product['image_path']  # Store the URL in metadata
                })
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
    
    def extract_features(self, image: Image.Image) -> torch.Tensor:
        """
        Extract features from an image using the pre-trained model.
        
        Args:
            image (PIL.Image): Input image
            
        Returns:
            torch.Tensor: Feature vector
        """
        # Preprocess image
        image = self._preprocess_image(image)
        image_tensor = self.transform(image).unsqueeze(0)
        
        # Extract features
        with torch.no_grad():
            features = self.model(image_tensor)
            
        return features.squeeze()
    
    def find_products(self, image: Image.Image, similarity_threshold: float = 0.95) -> Tuple[Optional[Dict], List[Dict]]:
        """
        Find exact match and similar products to the uploaded image using vector search.
        
        Args:
            image (PIL.Image): Uploaded image
            similarity_threshold (float): Threshold for considering an exact match
            
        Returns:
            Tuple[Optional[Dict], List[Dict]]: (exact_match, similar_products)
                - exact_match: Product details if exact match found, None otherwise
                - similar_products: List of similar products (up to 3)
        """
        try:
            # Preprocess and extract features from uploaded image
            image = self._preprocess_image(image)
            query_features = self.extract_features(image)
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_features.numpy().tolist()],
                n_results=4  # Get top 4 results (1 for exact match, 3 for similar)
            )
            
            # Process results
            similarities = []
            for i in range(len(results['ids'][0])):
                product_id = results['ids'][0][i]
                similarity = results['distances'][0][i]  # ChromaDB returns distances, convert to similarity
                metadata = results['metadatas'][0][i]
                
                similarities.append({
                    'product_id': product_id,
                    'name': results['documents'][0][i],
                    'price': metadata['price'],
                    'image_path': metadata['image_path'],  # Include the image URL in results
                    'similarity': 1 - similarity  # Convert distance to similarity
                })
            
            # Check for exact match
            exact_match = None
            if similarities and similarities[0]['similarity'] >= similarity_threshold:
                exact_match = similarities[0]
                # Remove exact match from similar products
                similarities = similarities[1:]
            
            # Return exact match (if any) and top 3 similar products
            return exact_match, similarities[:3]
            
        except Exception as e:
            print(f"Error in find_products: {str(e)}")
            return None, []
    
    def get_product_details(self, product_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific product.
        
        Args:
            product_id (str): Product identifier
            
        Returns:
            Optional[Dict]: Product details if found, None otherwise
        """
        return self.product_catalog.get(product_id) 