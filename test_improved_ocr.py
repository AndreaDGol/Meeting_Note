#!/usr/bin/env python3
"""
Test improved OCR functionality with scanned PDF
"""

import requests
import os
import tempfile
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_handwritten_style_pdf():
    """Create a PDF that simulates handwritten content"""
    # Create an image with handwritten-like content
    img = Image.new('RGB', (1200, 800), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a handwriting-like font
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
        font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Add handwritten-looking text with better spacing
    text_lines = [
        ("Meeting Notes - Project Planning", font_large, (50, 50)),
        ("", font_medium, (50, 100)),
        ("Key Discussion Points:", font_medium, (50, 120)),
        ("• Budget allocation for Q2", font_small, (80, 160)),
        ("• Team performance review", font_small, (80, 190)),
        ("• New project proposals", font_small, (80, 220)),
        ("", font_medium, (50, 250)),
        ("Decisions Made:", font_medium, (50, 270)),
        ("1. Approve additional funding", font_small, (80, 310)),
        ("2. Hire two new developers", font_small, (80, 340)),
        ("3. Schedule client meeting", font_small, (80, 370)),
        ("", font_medium, (50, 400)),
        ("Action Items:", font_medium, (50, 420)),
        ("- John: prepare budget report", font_small, (80, 460)),
        ("- Sarah: update project timeline", font_small, (80, 490)),
        ("- Mike: contact new vendors", font_small, (80, 520)),
        ("", font_medium, (50, 550)),
        ("Next meeting: Friday 2pm", font_medium, (50, 570)),
        ("Location: Conference Room A", font_small, (50, 600)),
    ]
    
    for text, font, (x, y) in text_lines:
        if text.strip():
            # Add some random offset to make it look more handwritten
            import random
            x_offset = random.randint(-3, 3)
            y_offset = random.randint(-2, 2)
            draw.text((x + x_offset, y + y_offset), text, fill='black', font=font)
    
    # Save as PDF
    temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    temp_pdf.close()
    
    # Convert image to PDF
    img.save(temp_pdf.name, "PDF", resolution=300.0)
    
    return temp_pdf.name

def test_improved_ocr():
    """Test improved OCR with scanned PDF"""
    try:
        # Create test PDF
        pdf_path = create_handwritten_style_pdf()
        print(f"Created handwritten-style PDF: {pdf_path}")
        
        # Test upload
        url = "http://localhost:8000/api/upload"
        
        with open(pdf_path, 'rb') as f:
            files = {'file': ('handwritten_notes.pdf', f, 'application/pdf')}
            response = requests.post(url, files=files)
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload successful!")
            print(f"Title: {result.get('title', 'N/A')}")
            print(f"Confidence: {result.get('confidence', 'N/A')}")
            print(f"Extraction method: {result.get('extraction_method', 'N/A')}")
            print(f"Page count: {result.get('page_count', 'N/A')}")
            
            # Get the full note details
            note_id = result.get('note_id')
            if note_id:
                detail_url = f"http://localhost:8000/api/notes/{note_id}"
                detail_response = requests.get(detail_url)
                if detail_response.status_code == 200:
                    note_detail = detail_response.json()
                    print(f"\n📝 Extracted Text Preview:")
                    print("-" * 50)
                    print(note_detail.get('raw_text', 'No text extracted')[:500] + "...")
                    print("-" * 50)
        else:
            print(f"❌ Upload failed: {response.json()}")
        
        # Cleanup
        os.unlink(pdf_path)
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error testing improved OCR: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Improved OCR Functionality")
    print("=" * 50)
    
    success = test_improved_ocr()
    
    if success:
        print("\n✅ Improved OCR test completed!")
    else:
        print("\n❌ Improved OCR test failed!")
