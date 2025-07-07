# OCR Text Overlay System

A Python-based OCR (Optical Character Recognition) system that extracts text from images and creates new images with the recognized text visually overlaid on the original image.

This is perliminary stage.

NOTE: I'm developing on Fedora Linux and perform testing on Fedora, Redhat and Ubuntu distros, some functions might not work as expected on macOS.

## Features

-  **Text Extraction**: Uses Tesseract OCR for accurate text recognition, we can test both EasyOCR and PaddleOCR as an alternatives
-  **Visual Overlay**: Creates new images with text overlaid on original positions, this is very perliminary
-  **Multiple Styles**: Choose from highlight, border, or shadow overlay styles,
  . Highlight: OpenCV / PIL
  . Border: OpenCV
  . Shadow: PIL
-  **CLI Support**: Command-line interface for batch processing
-  **JSON Export**: Optional export of OCR data with coordinates and confidence scores
-  **Customizable**: Adjustable font sizes and overlay styles

## Installation

Note: if you are using macOS i would recommend installing [homebrew](https://brew.sh/) package manager + newer version of python.
You will need to run in virtual enviorment, python especially on macOS, make it hard to install python packages across the main file system and require "isolation".

on macOS i have succefully tested with `python 3.13.5` 

# Step 1: Create a venv
`python3 -m venv .venv`

# Step 2: Activate it
`source .venv/bin/activate`

### Prerequisites

- Python 3.7 or higher
- Tesseract OCR engine

### Quick Setup

1. Clone or download the project files
2. Run the automated setup:

```bash
python setup.py
```

This will install all dependencies and check for Tesseract OCR.

### Manual Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Tesseract OCR:

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download from [UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH.

## Usage

### Command Line Interface

Basic usage:
```bash
python ocr_overlay.py input_image.jpg
```

With options:
```bash
python ocr_overlay.py input_image.jpg -o output_overlay.png -s highlight --font-size 14 -j
```

#### CLI Options

- `-o, --output`: Output image path (auto-generated if not specified)
- `-s, --style`: Overlay style (`highlight`, `border`, `shadow`)
- `-j, --json`: Save OCR data as JSON file
- `--font-size`: Font size for overlay text (default: 12)
- `--tesseract-cmd`: Path to tesseract executable

### Overlay Styles

1. **Highlight** (default): Yellow background with black text
2. **Border**: White background with red border
3. **Shadow**: Black background with white text

## Examples

### Processing Screenshots

```bash
python ocr_overlay.py screenshot.png -s border --font-size 16
```

### Batch Processing with JSON Export

```bash
python ocr_overlay.py document.jpg -o processed_document.png -j
```

### Using Custom Tesseract Path

```bash
python ocr_overlay.py image.png --tesseract-cmd /usr/local/bin/tesseract
```

## Programming Interface

You can also use the OCR system in your own Python code:

```python
from ocr_overlay import OCROverlay

# Create OCR processor
ocr = OCROverlay(font_size=14)

# Process an image
result = ocr.process_image("input.jpg", "output.png", "highlight", save_json=True)

if result["success"]:
    print(f"Found {result['text_blocks_count']} text blocks")
    print(f"Extracted text: {result['extracted_text']}")
else:
    print(f"Error: {result['error']}")
```

## Output Format

The system creates:

1. **Overlay Image**: New image with text overlaid on the original
2. **JSON Data** (optional): Detailed OCR results with:
   - Extracted text for each block
   - Bounding box coordinates (x, y, width, height)
   - Confidence scores
   - Position information

### JSON Structure

```json
[
  {
    "text": "Sample Text",
    "x": 100,
    "y": 50,
    "width": 120,
    "height": 25,
    "confidence": 95
  }
]
```

## Supported Image Formats

- PNG
- JPEG/JPG
- GIF
- BMP
- TIFF

## Performance Tips

1. **Image Quality**: Higher resolution images generally produce better OCR results
2. **Contrast**: Images with good contrast between text and background work best
3. **Font Size**: Larger text is recognized more accurately
4. **Preprocessing**: Consider image preprocessing for poor quality images

## Troubleshooting

### Common Issues

**"tesseract not found"**
- Ensure Tesseract is installed and in PATH
- Use `--tesseract-cmd` to specify custom path

**"No text found in image"**
- Check image quality and contrast
- Verify text is clearly visible
- Try different OCR configurations
- I had a bug where i was overriding the original file, as result the file got corrupted and the extraction failed.

**Low accuracy results**
- Improve image resolution
- Enhance contrast
- Remove noise/artifacts

### Debug Mode

Add debug output by modifying the tesseract config:

```python
ocr_data = pytesseract.image_to_data(
    image, 
    output_type=pytesseract.Output.DICT,
    config='--psm 6 -c debug_file=/tmp/tesseract.log'
)
```

## Development

### Project Structure

```
ocrextract/
 ocr_overlay.py      # Main OCR processing module
 setup.py            # Installation script
 requirements.txt    # Python dependencies
 README.md          # This file
```
## References

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for text recognition
- [Pillow](https://pillow.readthedocs.io/) for image processing
- [pytesseract](https://github.com/madmaze/pytesseract) for Python integration

email: udi.shamir@navina.ai  / slack me if you have any questions
Cheers!
