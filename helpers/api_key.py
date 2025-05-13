import os
from dotenv import load_dotenv

def get_openai_api_key() -> str:
    """
    Get the OpenAI API key from environment variables.
    
    Returns:
        str: The OpenAI API key
        
    Raises:
        ValueError: If the API key is not found
    """
    # Load environment variables from .env file
    load_dotenv(override=True)
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Please create a .env file in your project root with:\n"
            "OPENAI_API_KEY=your-api-key-here"
        )
    
    return api_key 