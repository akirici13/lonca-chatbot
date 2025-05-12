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