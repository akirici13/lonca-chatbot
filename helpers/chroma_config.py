import os
import chromadb
from chromadb.config import Settings
from pathlib import Path

def get_chroma_client():
    """Get a shared ChromaDB client instance with consistent settings."""
    # Create a persistent directory for ChromaDB
    persist_directory = os.path.join(Path(__file__).parent.parent, "data", "chroma")
    os.makedirs(persist_directory, exist_ok=True)
    
    # Initialize ChromaDB with persistent storage
    return chromadb.Client(Settings(
        persist_directory=persist_directory,
        anonymized_telemetry=False
    )) 