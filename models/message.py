from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict

@dataclass
class Message:
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    image: Optional[str] = None
    search_results: Optional[Dict] = None
    image_description: Optional[str] = None