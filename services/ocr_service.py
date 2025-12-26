"""
Service for converting PDFs to base64 images for GPT-4o Vision API
"""

import os
import base64
from PIL import Image
from typing import Dict, Any, List
import logging
from pdf2image import convert_from_path
import io

logger = logging.getLogger(__name__)

class OCRService:
    """Service for converting PDF pages to base64 images for GPT-4o Vision API"""
    
    def __init__(self):
        pass
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        try:
            buffer = io.BytesIO()
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image.save(buffer, format='PNG')
            img_bytes = buffer.getvalue()
            return base64.b64encode(img_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Error converting image to base64: {str(e)}")
            raise
    
    def convert_pdf_to_base64_images(self, pdf_path: str) -> List[str]:
        """
        Convert PDF pages to base64 encoded images
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of base64 encoded image strings (one per page)
        """
        try:
            logger.info(f"Converting PDF to images: {pdf_path}")
            # Convert PDF to images with high DPI for better quality
            images = convert_from_path(pdf_path, dpi=300, first_page=None, last_page=None)
            
            base64_images = []
            for image in images:
                base64_str = self._image_to_base64(image)
                base64_images.append(base64_str)
            
            logger.info(f"Converted {len(base64_images)} pages to base64")
            return base64_images
            
        except Exception as e:
            logger.error(f"Error converting PDF to base64: {str(e)}")
            raise
    
    def convert_image_to_base64(self, image_path: str) -> str:
        """
        Convert image file to base64 string
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string
        """
        try:
            logger.info(f"Converting image to base64: {image_path}")
            image = Image.open(image_path)
            return self._image_to_base64(image)
        except Exception as e:
            logger.error(f"Error converting image to base64: {str(e)}")
            raise
    
    def get_pdf_page_count(self, pdf_path: str) -> int:
        """Get the number of pages in a PDF"""
        try:
            # Try to get page count without loading all images
            try:
                from pdf2image import pdfinfo_from_path
                info = pdfinfo_from_path(pdf_path)
                return info['Pages']
            except ImportError:
                # Fallback: load images to count (slower but works)
                images = convert_from_path(pdf_path, dpi=100)
                return len(images)
        except Exception as e:
            logger.warning(f"Could not get PDF page count: {e}, defaulting to 1")
            return 1
