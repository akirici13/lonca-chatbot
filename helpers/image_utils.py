from PIL import Image
import io
import base64

def convert_image_to_base64(image: Image.Image) -> str:
    """
    Convert PIL Image to base64 string.
    
    Args:
        image (PIL.Image): The image to convert
        
    Returns:
        str: Base64 encoded string of the image
    """
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def decode_base64_to_image(base64_string: str) -> Image.Image:
    """
    Convert base64 string back to PIL Image.
    
    Args:
        base64_string (str): Base64 encoded image string
        
    Returns:
        PIL.Image: Decoded image
    """
    image_data = base64.b64decode(base64_string)
    return Image.open(io.BytesIO(image_data))

def process_base64_image(image_data: str) -> Image.Image:
    """
    Process base64 encoded image data and return a PIL Image object.
    
    Args:
        image_data (str): Base64 encoded image data
        
    Returns:
        Image.Image: PIL Image object
        
    Raises:
        ValueError: If image data is invalid or cannot be processed
    """
    try:
        image_bytes = base64.b64decode(image_data)
        return Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise ValueError(f"Error processing image: {str(e)}") 