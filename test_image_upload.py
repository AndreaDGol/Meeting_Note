#!/usr/bin/env python3
"""
Test image upload functionality
"""

import requests
import os
import tempfile
from PIL import Image, ImageDraw, ImageFont

def create_test_image():
    """Create a test handwritten note image"""
    # Create a white background
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a handwriting-like font
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        font = ImageFont.load_default()
    
    # Add handwritten-looking text
    text_lines = [
        "Personal Journal Entry",
        "",
        "Today's thoughts:",
        "• Had a great meeting with the team",
        "• Need to finish the project proposal",
        "• Remember to call mom this weekend",
        "",
        "Goals for tomorrow:",
        "1. Complete the budget analysis",
        "2. Review the contract details",
        "3. Schedule team meeting",
        "",
        "Feeling optimistic about the future!"
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
    
    return img

def test_image_upload():
    """Test image upload to the API"""
    try:
        # Create test image
        test_img = create_test_image()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            test_img.save(tmp_file.name)
            temp_path = tmp_file.name
        
        # Test upload
        url = "http://localhost:8000/api/upload"
        
        with open(temp_path, 'rb') as f:
            files = {'file': ('test_notes.png', f, 'image/png')}
            response = requests.post(url, files=files)
        
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Cleanup
        os.unlink(temp_path)
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error testing image upload: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Image Upload Functionality")
    print("=" * 40)
    
    success = test_image_upload()
    
    if success:
        print("✅ Image upload test passed!")
    else:
        print("❌ Image upload test failed!")
