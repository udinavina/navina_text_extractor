#!/usr/bin/env python3

"""
Fixed OCR Text Overlay System
Addresses corruption issues in file handling and overlay generation
"""

import os
import sys
import hashlib
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import argparse
import json
from typing import List, Dict, Tuple, Optional

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Warning: reportlab not available, PDF generation disabled")


class OCROverlayFixed:
    """Fixed OCR text overlay processor"""
    
    def __init__(self, 
                 tesseract_cmd: Optional[str] = None,
                 font_path: Optional[str] = None,
                 font_size: int = 12,
                 output_base_dir: str = "output_data"):
        """
        Initialize OCR overlay processor
        
        Args:
            tesseract_cmd: Path to tesseract executable
            font_path: Path to font file for text rendering
            font_size: Font size for overlay text
            output_base_dir: Base directory for structured output
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        self.font_size = font_size
        self.font_path = font_path
        self.output_base_dir = Path(output_base_dir)
        
        # Try to load a font
        try:
            if font_path and os.path.exists(font_path):
                self.font = ImageFont.truetype(font_path, font_size)
            else:
                # Try common system fonts
                for font_name in [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/TTF/DejaVuSans.ttf",
                    "/System/Library/Fonts/Arial.ttf",
                    "C:\\Windows\\Fonts\\arial.ttf"
                ]:
                    if os.path.exists(font_name):
                        self.font = ImageFont.truetype(font_name, font_size)
                        break
                else:
                    # Fall back to default font
                    self.font = ImageFont.load_default()
        except Exception:
            self.font = ImageFont.load_default()
    
    def extract_text_with_positions(self, image_path: str) -> List[Dict]:
        """
        Extract text from image with bounding box positions
        """
        try:
            print(f"Extracting text from: {image_path}")
            
            # Verify image exists and is readable
            if not os.path.exists(image_path):
                print(f"Error: Image file not found: {image_path}")
                return []
            
            # Open and verify image
            try:
                with Image.open(image_path) as image:
                    print(f"Image loaded: {image.size}, mode: {image.mode}")
                    
                    # Convert to RGB if needed
                    if image.mode not in ('RGB', 'L'):
                        image = image.convert('RGB')
                        print(f"Converted image to RGB mode")
                    
                    # Get detailed OCR data with positions
                    print("Running OCR extraction...")
                    ocr_data = pytesseract.image_to_data(
                        image, 
                        output_type=pytesseract.Output.DICT,
                        config='--psm 6 -c preserve_interword_spaces=1'
                    )
                    
            except Exception as e:
                print(f"Error opening image: {e}")
                return []
            
            text_blocks = []
            
            # Process OCR results with better filtering
            print(f"Processing {len(ocr_data['text'])} OCR elements...")
            
            for i in range(len(ocr_data['text'])):
                text = ocr_data['text'][i].strip()
                confidence = int(ocr_data['conf'][i]) if ocr_data['conf'][i] != '-1' else 0
                
                # More lenient filtering - accept lower confidence for debugging
                if text and confidence > 0:  # Reduced from 30 to 0 for debugging
                    text_blocks.append({
                        'text': text,
                        'x': ocr_data['left'][i],
                        'y': ocr_data['top'][i],
                        'width': ocr_data['width'][i],
                        'height': ocr_data['height'][i],
                        'confidence': confidence
                    })
            
            print(f"Found {len(text_blocks)} valid text blocks")
            for i, block in enumerate(text_blocks[:5]):  # Show first 5 for debugging
                print(f"  Block {i+1}: '{block['text']}' (conf: {block['confidence']}%)")
            
            return text_blocks
            
        except Exception as e:
            print(f"Error extracting text: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            print(f"Error calculating hash: {e}")
            return "unknown"
    
    def create_output_directory(self, input_path: str) -> Path:
        """Create structured output directory based on filename and SHA256"""
        input_file = Path(input_path)
        filename = input_file.stem
        file_hash = self.calculate_file_hash(input_path)
        
        # Create directory name: filename_sha256 (truncated)
        dir_name = f"{filename}_{file_hash[:16]}"  # Use first 16 chars of hash
        output_dir = self.output_base_dir / dir_name
        
        # Create directories
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created output directory: {output_dir}")
        
        return output_dir
    
    def safe_copy_file(self, source_path: str, dest_path: str) -> bool:
        """Safely copy a file with integrity verification"""
        try:
            # Use shutil.copy2 to preserve metadata
            shutil.copy2(source_path, dest_path)
            
            # Verify file integrity
            original_size = os.path.getsize(source_path)
            copied_size = os.path.getsize(dest_path)
            
            if original_size != copied_size:
                print(f"Warning: File size mismatch after copy")
                return False
            
            # Verify copied file is readable
            if dest_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                try:
                    with Image.open(dest_path) as img:
                        pass  # Just verify it opens
                except Exception as e:
                    print(f"Warning: Copied image file appears corrupted: {e}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error copying file: {e}")
            return False
    
    def create_overlay_image_fixed(self, 
                                  image_path: str, 
                                  text_blocks: List[Dict],
                                  output_path: str,
                                  overlay_style: str = "highlight") -> bool:
        """
        Create new image with text overlaid - fixed version
        """
        try:
            print(f"Creating overlay image: {overlay_style} style")
            
            # Open original image
            with Image.open(image_path) as original:
                # Ensure RGB mode for consistent processing
                if original.mode != 'RGB':
                    original = original.convert('RGB')
                
                # Create a copy for overlay
                overlay_img = original.copy()
                
                # Color schemes (without alpha channel issues)
                colors = {
                    "highlight": {
                        "bg": (255, 255, 0),      # Yellow background
                        "text": (0, 0, 0),        # Black text
                        "border": (255, 165, 0)   # Orange border
                    },
                    "border": {
                        "bg": (255, 255, 255),    # White background
                        "text": (0, 0, 0),        # Black text
                        "border": (255, 0, 0)     # Red border
                    },
                    "shadow": {
                        "bg": (128, 128, 128),    # Gray background
                        "text": (255, 255, 255),  # White text
                        "border": (64, 64, 64)    # Dark gray border
                    }
                }
                
                style = colors.get(overlay_style, colors["highlight"])
                
                # Create draw object
                draw = ImageDraw.Draw(overlay_img)
                
                # Create overlay for each text block
                overlays_created = 0
                for block in text_blocks:
                    x, y = block['x'], block['y']
                    width, height = block['width'], block['height']
                    text = block['text']
                    
                    # Skip if coordinates are invalid
                    if width <= 0 or height <= 0:
                        continue
                    
                    # Calculate text size for centering
                    try:
                        text_bbox = draw.textbbox((0, 0), text, font=self.font)
                        text_width = text_bbox[2] - text_bbox[0]
                        text_height = text_bbox[3] - text_bbox[1]
                    except:
                        # Fallback if textbbox not available
                        text_width = len(text) * self.font_size * 0.6
                        text_height = self.font_size
                    
                    # Position text in center of detected area
                    text_x = x + max(0, (width - text_width) // 2)
                    text_y = y + max(0, (height - text_height) // 2)
                    
                    # Ensure text stays within image bounds
                    text_x = max(0, min(text_x, original.width - text_width))
                    text_y = max(0, min(text_y, original.height - text_height))
                    
                    # Draw background rectangle
                    bg_rect = [
                        max(0, text_x - 4),
                        max(0, text_y - 2),
                        min(original.width, text_x + text_width + 4),
                        min(original.height, text_y + text_height + 2)
                    ]
                    
                    # Draw background
                    draw.rectangle(bg_rect, fill=style["bg"], outline=style["border"], width=1)
                    
                    # Draw text
                    draw.text((text_x, text_y), text, font=self.font, fill=style["text"])
                    
                    overlays_created += 1
                
                print(f"Created {overlays_created} text overlays")
                
                # Save result with high quality
                overlay_img.save(output_path, format='PNG', optimize=False)
                
                # Verify saved file
                if os.path.exists(output_path):
                    try:
                        with Image.open(output_path) as test_img:
                            print(f"Overlay image saved successfully: {test_img.size}")
                            return True
                    except Exception as e:
                        print(f"Saved overlay image appears corrupted: {e}")
                        return False
                else:
                    print("Overlay image file was not created")
                    return False
            
        except Exception as e:
            print(f"Error creating overlay: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_text_file(self, text_blocks: List[Dict], output_path: str) -> bool:
        """Save extracted text to TXT file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("OCR Extracted Text\n")
                f.write("=" * 50 + "\n\n")
                
                for i, block in enumerate(text_blocks, 1):
                    f.write(f"Text Block {i}:\n")
                    f.write(f"Text: {block['text']}\n")
                    f.write(f"Position: ({block['x']}, {block['y']})\n")
                    f.write(f"Size: {block['width']} x {block['height']}\n")
                    f.write(f"Confidence: {block['confidence']}%\n")
                    f.write("-" * 30 + "\n")
                
                # Also save plain text
                f.write("\n\nPlain Text:\n")
                f.write("=" * 20 + "\n")
                all_text = "\n".join([block['text'] for block in text_blocks])
                f.write(all_text)
            
            print(f"Text file saved: {output_path}")
            return True
        except Exception as e:
            print(f"Error saving text file: {e}")
            return False
    
    def save_pdf_file(self, text_blocks: List[Dict], output_path: str, original_image_path: str) -> bool:
        """Save extracted text and image to PDF file"""
        if not PDF_AVAILABLE:
            print("PDF generation skipped - reportlab not available")
            return False
            
        try:
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            # Add title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "OCR Extracted Text Report")
            
            # Add extracted text
            c.setFont("Helvetica", 10)
            y_position = height - 100
            
            for i, block in enumerate(text_blocks, 1):
                if y_position < 100:  # Start new page if needed
                    c.showPage()
                    y_position = height - 50
                
                c.drawString(50, y_position, f"Block {i}: {block['text']}")
                y_position -= 15
                c.drawString(70, y_position, f"Position: ({block['x']}, {block['y']}) - Confidence: {block['confidence']}%")
                y_position -= 25
            
            c.save()
            print(f"PDF file saved: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error saving PDF file: {e}")
            return False
    
    def process_image(self, input_path: str, overlay_style: str = "highlight") -> Dict:
        """
        Complete OCR processing pipeline with fixed file handling
        """
        print(f"\n Processing image: {input_path}")
        print("=" * 60)
        
        # Validate input file
        if not os.path.exists(input_path):
            return {
                "success": False,
                "error": f"Input file not found: {input_path}",
                "text_blocks": []
            }
        
        # Create structured output directory
        try:
            output_dir = self.create_output_directory(input_path)
            input_file = Path(input_path)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create output directory: {e}",
                "text_blocks": []
            }
        
        # Define output file paths
        original_copy_path = output_dir / f"original{input_file.suffix}"
        overlay_image_path = output_dir / f"overlay_image.png"  # Always PNG for overlay
        text_file_path = output_dir / "extracted_text.txt"
        pdf_file_path = output_dir / "document.pdf"
        json_file_path = output_dir / "ocr_data.json"
        
        # Extract text with positions
        text_blocks = self.extract_text_with_positions(input_path)
        
        if not text_blocks:
            return {
                "success": False,
                "error": "No text found in image",
                "text_blocks": [],
                "output_directory": str(output_dir)
            }
        
        # Track success of each operation
        operations_success = {
            "copy_original": False,
            "create_overlay": False,
            "save_text": False,
            "save_pdf": False,
            "save_json": False
        }
        
        # 1. Copy original file safely
        print(f"\n Copying original file...")
        operations_success["copy_original"] = self.safe_copy_file(input_path, str(original_copy_path))
        if operations_success["copy_original"]:
            print(f" Original file copied to: {original_copy_path}")
        else:
            print(f" Failed to copy original file")
        
        # 2. Create overlay image
        print(f"\n Creating overlay image...")
        operations_success["create_overlay"] = self.create_overlay_image_fixed(
            input_path, text_blocks, str(overlay_image_path), overlay_style
        )
        if operations_success["create_overlay"]:
            print(f" Overlay image saved to: {overlay_image_path}")
        else:
            print(f" Failed to create overlay image")
        
        # 3. Save text file
        print(f"\n Saving text file...")
        operations_success["save_text"] = self.save_text_file(text_blocks, str(text_file_path))
        
        # 4. Save PDF file
        print(f"\n Saving PDF file...")
        operations_success["save_pdf"] = self.save_pdf_file(text_blocks, str(pdf_file_path), input_path)
        
        # 5. Save JSON data
        print(f"\n Saving JSON data...")
        try:
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "input_file": str(input_file),
                    "processing_info": {
                        "overlay_style": overlay_style,
                        "total_text_blocks": len(text_blocks),
                        "file_hash": self.calculate_file_hash(input_path)
                    },
                    "text_blocks": text_blocks
                }, f, indent=2)
            operations_success["save_json"] = True
            print(f" JSON data saved to: {json_file_path}")
        except Exception as e:
            print(f" Failed to save JSON file: {e}")
        
        # Extract all text for summary
        all_text = "\n".join([block['text'] for block in text_blocks])
        
        # Determine overall success
        critical_operations = ["copy_original", "create_overlay"]
        overall_success = all(operations_success[op] for op in critical_operations)
        
        result = {
            "success": overall_success,
            "input_path": input_path,
            "output_directory": str(output_dir),
            "output_files": {
                "original": str(original_copy_path) if operations_success["copy_original"] else None,
                "overlay_image": str(overlay_image_path) if operations_success["create_overlay"] else None,
                "text_file": str(text_file_path) if operations_success["save_text"] else None,
                "pdf_file": str(pdf_file_path) if operations_success["save_pdf"] else None,
                "json_file": str(json_file_path) if operations_success["save_json"] else None
            },
            "operations_success": operations_success,
            "text_blocks_count": len(text_blocks),
            "text_blocks": text_blocks,
            "extracted_text": all_text
        }
        
        return result


def main():
    """Command line interface for fixed OCR system"""
    parser = argparse.ArgumentParser(description="Fixed OCR Text Overlay System")
    parser.add_argument("input_image", help="Path to input image")
    parser.add_argument("-s", "--style", choices=["highlight", "border", "shadow"], 
                       default="highlight", help="Overlay style")
    parser.add_argument("--font-size", type=int, default=12, 
                       help="Font size for overlay text")
    parser.add_argument("--tesseract-cmd", help="Path to tesseract executable")
    parser.add_argument("--output-dir", default="output_data_fixed", 
                       help="Base output directory")
    
    args = parser.parse_args()
    
    # Validate input
    if not os.path.exists(args.input_image):
        print(f"Error: Input image '{args.input_image}' not found")
        sys.exit(1)
    
    # Create OCR processor
    ocr_processor = OCROverlayFixed(
        tesseract_cmd=args.tesseract_cmd,
        font_size=args.font_size,
        output_base_dir=args.output_dir
    )
    
    # Process image
    result = ocr_processor.process_image(args.input_image, args.style)
    
    # Print results
    print("\n" + "=" * 60)
    print(" PROCESSING RESULTS")
    print("=" * 60)
    
    if result["success"]:
        print(f" Processing completed successfully!")
        print(f" Input: {result['input_path']}")
        print(f" Output directory: {result['output_directory']}")
        print(f" Text blocks found: {result['text_blocks_count']}")
        
        print(f"\n Generated files:")
        for file_type, file_path in result['output_files'].items():
            if file_path:
                print(f"   {file_type.replace('_', ' ').title()}: {file_path}")
            else:
                print(f"   {file_type.replace('_', ' ').title()}: Failed to create")
        
        if result['extracted_text'].strip():
            print(f"\n Extracted text:")
            print("-" * 50)
            print(result['extracted_text'])
        else:
            print(f"\n No text extracted from image")
        
        print(f"\n All files saved to: {result['output_directory']}")
    else:
        print(f" Processing failed: {result.get('error', 'Unknown error')}")
        if 'output_directory' in result:
            print(f" Output directory: {result['output_directory']}")
        sys.exit(1)


if __name__ == "__main__":
    main()