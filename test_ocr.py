#!/usr/bin/env python3

"""
Test script for OCR Overlay System
Creates sample images and tests the OCR functionality
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from ocr_overlay import OCROverlay
import json


def create_test_image(text_content, filename, width=800, height=600):
    """Create a test image with text content"""
    
    # Create image with white background
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Try to load a font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    # Draw text content
    lines = text_content.split('\n')
    y_offset = 50
    
    for line in lines:
        if line.strip():
            draw.text((50, y_offset), line, fill='black', font=font)
            y_offset += 40
    
    # Save image
    image.save(filename)
    print(f"Created test image: {filename}")


def run_tests():
    """Run comprehensive tests"""
    
    print(" OCR Overlay System Test Suite")
    print("=" * 50)
    
    # Create test directory
    test_dir = Path("test_images")
    test_dir.mkdir(exist_ok=True)
    
    # Test cases
    test_cases = [
        {
            "name": "Simple Text",
            "content": "Hello World\nThis is a test\nSimple OCR example",
            "filename": test_dir / "simple_text.png"
        },
        {
            "name": "Mixed Content",
            "content": "Invoice #12345\nDate: 2024-01-15\nAmount: $299.99\nStatus: PAID",
            "filename": test_dir / "invoice.png"
        },
        {
            "name": "Technical Text",
            "content": "class OCROverlay:\n    def __init__(self):\n        self.font_size = 12\n    def process(self):",
            "filename": test_dir / "code.png"
        }
    ]
    
    # Create test images
    print("\n Creating test images...")
    for test_case in test_cases:
        create_test_image(
            test_case["content"], 
            test_case["filename"]
        )
    
    # Initialize OCR processor
    print("\n Initializing OCR processor...")
    try:
        ocr = OCROverlay()
        print(" OCR processor initialized")
    except Exception as e:
        print(f" Failed to initialize OCR: {e}")
        return False
    
    # Test each image
    print("\n Testing OCR processing...")
    
    all_passed = True
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 30)
        
        input_path = str(test_case["filename"])
        output_path = str(test_case["filename"]).replace('.png', '_overlay.png')
        
        # Test each overlay style
        for style in ["highlight", "border", "shadow"]:
            print(f"  Testing {style} style...")
            
            try:
                result = ocr.process_image(
                    input_path, 
                    style
                )
                
                if result["success"]:
                    print(f"     Success: {result['text_blocks_count']} text blocks")
                    print(f"     Text: {result['extracted_text'][:50]}...")
                    print(f"     Output: {result['output_directory']}")
                    
                    results.append({
                        "test": test_case['name'],
                        "style": style,
                        "success": True,
                        "text_blocks": result['text_blocks_count'],
                        "extracted_text": result['extracted_text'],
                        "output_directory": result['output_directory']
                    })
                else:
                    print(f"     Failed: {result.get('error', 'Unknown error')}")
                    all_passed = False
                    
                    results.append({
                        "test": test_case['name'],
                        "style": style,
                        "success": False,
                        "error": result.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                print(f"     Exception: {e}")
                all_passed = False
                
                results.append({
                    "test": test_case['name'],
                    "style": style,
                    "success": False,
                    "error": str(e)
                })
    
    # Save test results
    with open(test_dir / "test_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Performance test
    print("\n Performance test...")
    try:
        import time
        start_time = time.time()
        
        result = ocr.process_image(
            str(test_cases[0]["filename"]),
            "highlight"
        )
        
        processing_time = time.time() - start_time
        print(f"  Processing time: {processing_time:.2f} seconds")
        
        if result["success"]:
            print(f"   Performance test passed")
        else:
            print(f"   Performance test failed")
            
    except Exception as e:
        print(f"   Performance test error: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print(" TEST SUMMARY")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["success"])
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if all_passed:
        print("\n All tests passed!")
    else:
        print("\n Some tests failed - check results above")
    
    print(f"\nTest images and results saved in: {test_dir}")
    print("You can inspect the overlay images to validate quality")
    
    return all_passed


def main():
    """Main test function"""
    
    # Check if tesseract is available
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print(" Tesseract OCR is available")
    except Exception as e:
        print(f" Tesseract OCR not available: {e}")
        print("Please install tesseract or run setup.py")
        return False
    
    # Run tests
    success = run_tests()
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)