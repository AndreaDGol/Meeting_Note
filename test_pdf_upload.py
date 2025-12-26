#!/usr/bin/env python3
"""
Test PDF upload functionality
"""

import requests
import os
import tempfile
from PIL import Image, ImageDraw, ImageFont
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_test_pdf():
    """Create a test PDF with handwritten-like content"""
    # Create a simple PDF using reportlab
    temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    temp_pdf.close()
    
    # Create PDF content
    c = canvas.Canvas(temp_pdf.name, pagesize=letter)
    c.drawString(100, 750, "Meeting Notes - Project Alpha")
    c.drawString(100, 720, "Key Points:")
    c.drawString(120, 690, "• Discuss budget allocation")
    c.drawString(120, 660, "• Review timeline for Q1")
    c.drawString(120, 630, "• Assign tasks to team members")
    c.drawString(100, 600, "Action Items:")
    c.drawString(120, 570, "1. John - prepare budget report")
    c.drawString(120, 540, "2. Sarah - update project timeline")
    c.drawString(100, 510, "Next meeting: Friday 2pm")
    c.save()
    
    return temp_pdf.name

def test_pdf_upload():
    """Test PDF upload to the API"""
    try:
        # Create test PDF
        pdf_path = create_test_pdf()
        print(f"Created test PDF: {pdf_path}")
        
        # Test upload
        url = "http://localhost:8000/api/upload"
        
        with open(pdf_path, 'rb') as f:
            files = {'file': ('test_notes.pdf', f, 'application/pdf')}
            response = requests.post(url, files=files)
        
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Cleanup
        os.unlink(pdf_path)
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error testing PDF upload: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing PDF Upload Functionality")
    print("=" * 40)
    
    # Install reportlab if not available
    try:
        import reportlab
    except ImportError:
        print("Installing reportlab...")
        import subprocess
        subprocess.run(["pip", "install", "reportlab"], check=True)
    
    success = test_pdf_upload()
    
    if success:
        print("✅ PDF upload test passed!")
    else:
        print("❌ PDF upload test failed!")
