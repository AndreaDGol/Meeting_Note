#!/usr/bin/env python3
"""
Test scanned PDF upload functionality
"""

import requests
import os
import tempfile
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_scanned_like_pdf():
    """Create a PDF that simulates a scanned handwritten document"""
    # Create an image with handwritten-like content
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a handwriting-like font
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        font = ImageFont.load_default()
    
    # Add handwritten-looking text
    text_lines = [
        "Meeting Notes - Project Beta",
        "",
        "Key Discussion Points:",
        "• Budget review for Q2",
        "• Team performance metrics",
        "• New project proposals",
        "",
        "Decisions Made:",
        "1. Approve additional funding",
        "2. Hire two new developers",
        "3. Schedule client meeting",
        "",
        "Next steps: Follow up by Friday"
    ]
    
    y_position = 50
    for line in text_lines:
        if line.strip():
            # Add some random offset to make it look more handwritten
            import random
            x_offset = random.randint(-5, 5)
            y_offset = random.randint(-2, 2)
            draw.text((50 + x_offset, y_position + y_offset), line, fill='black', font=font)
        y_position += 35
    
    # Save as PDF
    temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    temp_pdf.close()
    
    # Convert image to PDF
    img.save(temp_pdf.name, "PDF", resolution=300.0)
    
    return temp_pdf.name

def test_scanned_pdf_upload():
    """Test scanned PDF upload to the API"""
    try:
        # Create test PDF
        pdf_path = create_scanned_like_pdf()
        print(f"Created scanned-like PDF: {pdf_path}")
        
        # Test upload
        url = "http://localhost:8000/api/upload"
        
        with open(pdf_path, 'rb') as f:
            files = {'file': ('scanned_notes.pdf', f, 'application/pdf')}
            response = requests.post(url, files=files)
        
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Cleanup
        os.unlink(pdf_path)
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error testing scanned PDF upload: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Scanned PDF Upload Functionality")
    print("=" * 50)
    
    success = test_scanned_pdf_upload()
    
    if success:
        print("✅ Scanned PDF upload test passed!")
    else:
        print("❌ Scanned PDF upload test failed!")
