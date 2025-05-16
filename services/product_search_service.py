from typing import List, Dict, Optional, Tuple
import json
from pathlib import Path
import numpy as np
from PIL import Image
from .image_search_service import ImageSearchService
import chromadb
from chromadb.utils import embedding_functions
import torch
from transformers import AutoTokenizer, AutoModel
import os
from helpers.chroma_config import get_chroma_client

class ProductSearchService:
    def __init__(self, catalog_path: str = "data/product_catalog_multi_image.json"):
        """Initialize the product search service with both text and image search capabilities."""
        self.catalog_path = catalog_path
        self.image_search_service = ImageSearchService()
        
        # Initialize text search components
        self.tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
        self.text_model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
        
        # Initialize ChromaDB with shared configuration
        self.chroma_client = get_chroma_client()
        
        # Initialize text search components
        try:
            self.text_collection = self.chroma_client.create_collection(
                name="product_text",
                embedding_function=embedding_functions.DefaultEmbeddingFunction()
            )
        except Exception as e:
            if "already exists" in str(e):
                self.text_collection = self.chroma_client.get_collection(
                    name="product_text",
                    embedding_function=embedding_functions.DefaultEmbeddingFunction()
                )
            else:
                raise e
        
        # Load product catalog and initialize text embeddings
        self.product_catalog = self._load_product_catalog()
        self._initialize_text_collection()
    
    def _load_product_catalog(self) -> Dict:
        """Load the product catalog from JSON file."""
        with open(self.catalog_path, 'r') as f:
            return json.load(f)
    
    def _get_text_embedding(self, text: str) -> np.ndarray:
        """Generate text embedding using the transformer model."""
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = self.text_model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).numpy()[0]
    
    def _initialize_text_collection(self):
        """Initialize ChromaDB collection with product text embeddings."""
        if self.text_collection.count() == 0:
            print("Adding text embeddings to ChromaDB...")
            ids = []
            embeddings = []
            documents = []
            metadatas = []
            
            for product in self.product_catalog['products']:
                product_id = product['id']['$oid'] if isinstance(product['id'], dict) else str(product['id'])
                product_text = f"{product['name']} {product.get('description', '')} {product.get('category', '')}"
                ids.append(product_id)
                embeddings.append(self._get_text_embedding(product_text).tolist())
                documents.append(product_text)
                # Use the first image in image_paths if available, else fallback to image_path
                image_paths = product.get('image_paths')
                if image_paths and isinstance(image_paths, list) and len(image_paths) > 0:
                    image_url = image_paths[0]
                else:
                    image_url = product.get('image_path', None)
                metadatas.append({
                    'name': product['name'],
                    'price': product['price'],
                    'image_path': image_url,
                    'total_stock': product.get('total_stock', 0)
                })
            
            self.text_collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
    
    def search_products(self, query: str, image: Optional[Image.Image] = None, 
                       similarity_threshold: float = 0.95) -> Tuple[Optional[Dict], List[Dict]]:
        """
        Search products using both text and image queries.
        
        Args:
            query (str): Text query for product search
            image (Optional[Image.Image]): Optional image for visual search
            similarity_threshold (float): Threshold for considering an exact match
            
        Returns:
            Tuple[Optional[Dict], List[Dict]]: (exact_match, similar_products)
        """
        results = []
        
        # Perform text search
        if query:
            text_results = self.text_collection.query(
                query_texts=[query],
                n_results=5
            )
            
            for i in range(len(text_results['ids'][0])):
                product_id = text_results['ids'][0][i]
                similarity = 1 - text_results['distances'][0][i]
                metadata = text_results['metadatas'][0][i]
                
                results.append({
                    'product_id': product_id,
                    'name': metadata['name'],
                    'price': metadata['price'],
                    'image_path': metadata['image_path'],
                    'total_stock': metadata.get('total_stock', 0),
                    'similarity': similarity,
                    'search_type': 'text'
                })
        
        # Perform image search if image is provided
        if image is not None:
            exact_match, similar_products = self.image_search_service.find_products(
                image, 
                similarity_threshold=similarity_threshold
            )
            
            if exact_match:
                # Get full product details including stock
                product_details = self.get_product_details(exact_match['product_id'])
                if product_details:
                    exact_match['total_stock'] = product_details.get('total_stock', 0)
                results.append({
                    **exact_match,
                    'search_type': 'image_exact'
                })
            
            for product in similar_products:
                # Get full product details including stock
                product_details = self.get_product_details(product['product_id'])
                if product_details:
                    product['total_stock'] = product_details.get('total_stock', 0)
                results.append({
                    **product,
                    'search_type': 'image_similar'
                })
        
        # Sort results by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Find exact match (if any)
        exact_match = None
        if results and results[0]['similarity'] >= similarity_threshold:
            exact_match = results[0]
            # If we have an exact match, don't return similar products
            return exact_match, []
        
        # Return exact match (if any) and top 5 similar products
        return exact_match, results[:5]
    
    def get_product_details(self, product_id: str) -> Optional[Dict]:
        """Get detailed information about a specific product."""
        for product in self.product_catalog['products']:
            if str(product['id'].get('$oid', product['id'])) == product_id:
                return product
        return None 