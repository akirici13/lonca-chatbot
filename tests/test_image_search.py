import unittest
from PIL import Image
import torch
from services.image_search_service import ImageSearchService
import os
from pathlib import Path
import numpy as np

class TestImageSearchService(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.service = ImageSearchService()
        
        # Create test images with different patterns
        self.red_image = Image.new('RGB', (224, 224), color='red')
        self.blue_image = Image.new('RGB', (224, 224), color='blue')
        self.gradient_image = self._create_gradient_image()
        
        # Create a products directory if it doesn't exist
        self.products_dir = Path("products")
        self.products_dir.mkdir(exist_ok=True)
        
        # Save test images
        self.red_image.save(self.products_dir / "red_product.jpg")
        self.blue_image.save(self.products_dir / "blue_product.jpg")
        self.gradient_image.save(self.products_dir / "gradient_product.jpg")
        
        # Update product catalog with real images
        self.service.product_catalog = {
            "red_product": {
                "name": "Red Product",
                "price": "€29.99",
                "features": self.service.extract_features(self.red_image),
                "image_path": str(self.products_dir / "red_product.jpg")
            },
            "blue_product": {
                "name": "Blue Product",
                "price": "€39.99",
                "features": self.service.extract_features(self.blue_image),
                "image_path": str(self.products_dir / "blue_product.jpg")
            },
            "gradient_product": {
                "name": "Gradient Product",
                "price": "€49.99",
                "features": self.service.extract_features(self.gradient_image),
                "image_path": str(self.products_dir / "gradient_product.jpg")
            }
        }
    
    def _create_gradient_image(self) -> Image.Image:
        """Create a gradient image for testing."""
        width, height = 224, 224
        image = Image.new('RGB', (width, height))
        pixels = image.load()
        
        for x in range(width):
            for y in range(height):
                r = int(255 * x / width)
                g = int(255 * y / height)
                b = int(255 * (x + y) / (width + height))
                pixels[x, y] = (r, g, b)
        
        return image
    
    def test_exact_match(self):
        """Test finding an exact match product."""
        # Search with the same red image
        exact_match, similar_products = self.service.find_products(self.red_image, similarity_threshold=0.999)
        
        # Should find exact match
        self.assertIsNotNone(exact_match)
        self.assertEqual(exact_match['name'], "Red Product")
        self.assertGreaterEqual(exact_match['similarity'], 0.999)
        
        # Similar products should not include the exact match
        self.assertNotIn(exact_match['product_id'], [p['product_id'] for p in similar_products])
    
    def test_similar_products(self):
        """Test finding similar products when no exact match exists."""
        # Create a modified red image with a different pattern
        modified_red = Image.new('RGB', (224, 224), color='red')
        pixels = modified_red.load()
        # Add a small white dot in the corner
        pixels[0, 0] = (255, 255, 255)
        
        exact_match, similar_products = self.service.find_products(modified_red, similarity_threshold=0.999)
        
        # Should not find exact match
        self.assertIsNone(exact_match)
        
        # Should find similar products
        self.assertGreater(len(similar_products), 0)
        self.assertLessEqual(len(similar_products), 3)
        
        # Red product should be most similar
        self.assertEqual(similar_products[0]['name'], "Red Product")
        self.assertGreater(similar_products[0]['similarity'], 0.8)  # Still should be quite similar
    
    def test_different_colors(self):
        """Test searching with completely different colors."""
        exact_match, similar_products = self.service.find_products(self.blue_image, similarity_threshold=0.999)
        
        # Should not find exact match
        self.assertIsNone(exact_match)
        
        # Should find similar products
        self.assertGreater(len(similar_products), 0)
        self.assertLessEqual(len(similar_products), 3)
        
        # Blue product should be most similar
        self.assertEqual(similar_products[0]['name'], "Blue Product")
        self.assertGreater(similar_products[0]['similarity'], 0.8)  # Still should be quite similar
    
    def test_feature_extraction_consistency(self):
        """Test that feature extraction is consistent for the same image."""
        features1 = self.service.extract_features(self.red_image)
        features2 = self.service.extract_features(self.red_image)
        
        # Features should be identical for the same image
        self.assertTrue(torch.allclose(features1, features2))
        
        # Features should be different for different images
        features3 = self.service.extract_features(self.blue_image)
        self.assertFalse(torch.allclose(features1, features3))
    
    def tearDown(self):
        """Clean up test files."""
        # Remove test images
        for image_file in self.products_dir.glob("*.jpg"):
            image_file.unlink()
        
        # Remove products directory if empty
        if not any(self.products_dir.iterdir()):
            self.products_dir.rmdir()

if __name__ == '__main__':
    unittest.main() 