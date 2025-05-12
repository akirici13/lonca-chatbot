from PIL import Image
import torch
from torchvision import transforms
from torchvision.models import resnet50, ResNet50_Weights
import numpy as np
from typing import List, Dict, Optional, Tuple
import os
import json
from pathlib import Path

class ImageSearchService:
    def __init__(self, catalog_path: str = "data/product_catalog.json"):
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
        
        # Load product catalog
        self.catalog_path = catalog_path
        self.product_catalog = self._load_product_catalog()
        
    def _load_product_catalog(self) -> Dict[str, Dict]:
        """
        Load product catalog with image features from JSON file.
        
        Returns:
            Dict[str, Dict]: Dictionary of products with their features
        """
        try:
            with open(self.catalog_path, 'r') as f:
                catalog_data = json.load(f)
            
            products = {}
            for product in catalog_data['products']:
                image_path = product['image_path']
                if os.path.exists(image_path):
                    # Load and process the image
                    image = Image.open(image_path).convert('RGB')
                    features = self.extract_features(image)
                    
                    products[product['id']] = {
                        'name': product['name'],
                        'price': product['price'],
                        'features': features,
                        'image_path': image_path
                    }
                else:
                    print(f"Warning: Image not found for product {product['id']}: {image_path}")
            
            return products
        except Exception as e:
            print(f"Error loading product catalog: {e}")
            return {}
    
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
        Find exact match and similar products to the uploaded image.
        
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
        
        # Calculate similarity scores
        similarities = []
        for product_id, product in self.product_catalog.items():
            similarity = torch.cosine_similarity(
                query_features.unsqueeze(0),
                product['features'].unsqueeze(0)
            ).item()
            
            similarities.append({
                'product_id': product_id,
                'name': product['name'],
                'price': product['price'],
                'similarity': similarity
            })
        
        # Sort by similarity score
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
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