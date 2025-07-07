#!/usr/bin/env python3

"""
Debug test for OCR issues
"""

import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import shutil
import hashlib

def create_simple_test_image():
    """Create a simple test image with clear text"""
    
    # Create image
    img = Image.new('RGB', (400, 200), 'white')
    draw = ImageDraw.Draw(img)
    
    # Use default font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # Draw clear text
    draw.text((20, 50), "Hello World", fill='black', font=font)
    draw.text((20, 100), "This is a test", fill='black', font=font)
    
    # Save
    test_file = "debug_test.png"
    img.save(test_file)
    print(f"Created test image: {test_file}")
    return test_file

def test_file_copy(source_file):
    """Test file copying"""
    print("\n=== Testing File Copy ===")
    
    # Create output directory
    output_dir = Path("debug_output")
    output_dir.mkdir(exist_ok=True)
    
    # Test copy
    dest_file = output_dir / "copied_original.png"
    
    try:
        # Method 1: shutil.copy2
        shutil.copy2(source_file, dest_file)
        print(f" File copied successfully to: {dest_file}")
        
        # Verify file integrity
        original_size = os.path.getsize(source_file)
        copied_size = os.path.getsize(dest_file)
        
        print(f"Original size: {original_size} bytes")
        print(f"Copied size: {copied_size} bytes")
        
        if original_size == copied_size:
            print(" File sizes match")
        else:
            print(" File sizes don't match!")
            
        # Test opening copied file
        try:
            with Image.open(dest_file) as img:
                print(f" Copied image opens successfully: {img.size}")
        except Exception as e:
            print(f" Copied image corrupted: {e}")
            
    except Exception as e:
        print(f" File copy failed: {e}")

def test_hash_calculation(file_path):
    """Test hash calculation"""
    print("\n=== Testing Hash Calculation ===")
    
    try:
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        
        file_hash = hash_sha256.hexdigest()
        print(f" Hash calculated: {file_hash[:16]}...")
        return file_hash
        
    except Exception as e:
        print(f" Hash calculation failed: {e}")
        return "unknown"

def test_basic_ocr(image_file):
    """Test basic OCR without overlay system"""
    print("\n=== Testing Basic OCR ===")
    
    try:
        import pytesseract
        from PIL import Image
        
        # Open image
        with Image.open(image_file) as img:
            print(f" Image opened: {img.size}, mode: {img.mode}")
            
            # Basic text extraction
            text = pytesseract.image_to_string(img)
            print(f" Extracted text: '{text.strip()}'")
            
            # Detailed data extraction
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            
            print(f" OCR data extracted, found {len(data['text'])} elements")
            
            # Filter valid text
            valid_text = []
            for i in range(len(data['text'])):
                text_item = data['text'][i].strip()
                confidence = int(data['conf'][i])
                
                if text_item and confidence > 30:
                    valid_text.append({
                        'text': text_item,
                        'confidence': confidence,
                        'x': data['left'][i],
                        'y': data['top'][i]
                    })
            
            print(f" Valid text blocks: {len(valid_text)}")
            for item in valid_text:
                print(f"  - '{item['text']}' (confidence: {item['confidence']}%)")
                
            return valid_text
            
    except Exception as e:
        print(f" OCR test failed: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """Run debug tests"""
    print(" OCR Debug Test Suite")
    print("=" * 50)
    
    # Create test image
    test_file = create_simple_test_image()
    
    # Test file operations
    test_file_copy(test_file)
    test_hash_calculation(test_file)
    
    # Test OCR
    test_basic_ocr(test_file)
    
    print("\n" + "=" * 50)
    print("Debug tests completed")
    print("Check debug_output/ directory for results")

if __name__ == "__main__":
    main()