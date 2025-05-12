import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from services.image_search_service import ImageSearchService
import os

def update_embeddings():
    """Update embeddings with the new product catalog."""
    print("Starting embeddings update...")
    
    # Remove existing embeddings file if it exists
    embeddings_path = project_root / "data" / "product_embeddings.pkl"
    if embeddings_path.exists():
        print("Removing existing embeddings...")
        os.remove(embeddings_path)
    
    # Initialize image search service (this will create new embeddings)
    print("Creating new embeddings...")
    service = ImageSearchService()
    
    print("Embeddings update completed!")

if __name__ == "__main__":
    update_embeddings() 