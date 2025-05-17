import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from helpers.chroma_config import get_chroma_client

client = get_chroma_client()
try:
    client.delete_collection("lonca_faqs")
    print("FAQ collection deleted.")
except Exception as e:
    print(f"Error deleting collection: {e}")