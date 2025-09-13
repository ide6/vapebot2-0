"""
Simple imghdr replacement for Python 3.13 compatibility
"""
import os

def what(filepath):
    """
    Determine the type of an image file
    """
    if not os.path.isfile(filepath):
        return None
    
    ext = os.path.splitext(filepath)[1].lower()
    
    image_extensions = {
        '.jpg': 'jpeg',
        '.jpeg': 'jpeg',
        '.png': 'png',
        '.gif': 'gif',
        '.bmp': 'bmp',
        '.tiff': 'tiff',
        '.webp': 'webp'
    }
    
    return image_extensions.get(ext)