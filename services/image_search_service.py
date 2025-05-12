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
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.Client()
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
    
    def _load_or_create_embeddings(self) -> Tuple[Dict[str, Dict], Dict[str, np.ndarray]]:
        """
        Load existing embeddings or create new ones if they don't exist.
        
        Returns:
            Tuple[Dict[str, Dict], Dict[str, np.ndarray]]: (product_catalog, embeddings)
        """
        if os.path.exists(self.embeddings_path):
            print("Loading existing embeddings...")
            with open(self.embeddings_path, 'rb') as f:
                return pickle.load(f)
        
        print("Creating new embeddings...")
        # Load product catalog
        with open(self.catalog_path, 'r') as f:
            catalog_data = json.load(f)
        
        products = {}
        embeddings = {}
        
        for product in catalog_data['products']:
            image_path = product['image_path']
            if os.path.exists(image_path):
                # Load and process the image
                image = Image.open(image_path).convert('RGB')
                features = self.extract_features(image)
                
                product_id = product['id']
                products[product_id] = {
                    'name': product['name'],
                    'price': product['price'],
                    'image_path': image_path
                }
                embeddings[product_id] = features.numpy()
            else:
                print(f"Warning: Image not found for product {product['id']}: {image_path}")
        
        # Save embeddings
        with open(self.embeddings_path, 'wb') as f:
            pickle.dump((products, embeddings), f)
        
        return products, embeddings
    
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
                    'image_path': product['image_path']
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
        # Extract features from uploaded image
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
    
    def get_product_details(self, product_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific product.
        
        Args:
            product_id (str): Product identifier
            
        Returns:
            Optional[Dict]: Product details if found, None otherwise
        """
        return self.product_catalog.get(product_id) 