import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from services.image_search_service import ImageSearchService
from PIL import Image
import os

def test_with_real_images():
    # Initialize the service
    service = ImageSearchService()
    
    # Create test images directory if it doesn't exist
    test_images_dir = project_root / "test_images"
    test_images_dir.mkdir(exist_ok=True)
    
    print("\nImage Search Test Results:")
    print("=" * 50)
    
    # Test each image in the test_images directory
    image_files = list(test_images_dir.glob("*.jpg")) + list(test_images_dir.glob("*.jpeg"))
    
    if not image_files:
        print("No test images found in the test_images directory!")
        print("Please add some .jpg or .jpeg files to test.")
        return
    
    for image_file in image_files:
        print(f"\nTesting with image: {image_file.name}")
        print("-" * 30)
        
        try:
            # Load and process the image
            image = Image.open(image_file).convert('RGB')
            
            # Find matches
            exact_match, similar_products = service.find_products(image)
            
            # Print results
            if exact_match:
                print("Found exact match:")
                print(f"Product: {exact_match['name']}")
                print(f"Price: {exact_match['price']}")
                print(f"Similarity: {exact_match['similarity']:.4f}")
            else:
                print("No exact match found.")
            
            if similar_products:
                print("\nSimilar products:")
                for product in similar_products:
                    print(f"\nProduct: {product['name']}")
                    print(f"Price: {product['price']}")
                    print(f"Similarity: {product['similarity']:.4f}")
            else:
                print("No similar products found.")
                
        except Exception as e:
            print(f"Error processing image {image_file.name}: {str(e)}")

if __name__ == "__main__":
    test_with_real_images() 