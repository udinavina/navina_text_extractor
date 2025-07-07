# OCR Text Overlay System

A Python-based Text extractor (currently from PDF) nd  OCR (Optical Character Recognition) system that extracts text from images and creates new images with the recognized text visually overlaid on the original image.

This is perliminary stage.

NOTE: I'm developing on Fedora Linux and perform testing on Fedora, Redhat and Ubuntu distros, some functions might not work as expected on macOS.

## Features

-  **Text Extraction**: Uses Tesseract OCR for accurate text recognition, we can test both EasyOCR and PaddleOCR as an alternatives
-  **Visual Overlay**: Creates new images with text overlaid on original positions, this is very perliminary
-  **Multiple Styles**: Choose from highlight, border, or shadow overlay styles:
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

**Windows:**
Download from [UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH.

## Usage

### Command Line Interface

Basic usage:
```bash
python3 main.py test_samples/Medical-Record-Requirements-for-Pre-Service.pdf --all
```

## Examples
```
python3 main.py -h
PyMuPDF loaded successfully.
usage: main.py [-h] [--json] [--csv] [--features] [--text] [--all] [--ocr] [--normalize] [--group {line,block,page}]
               [--output-dir OUTPUT_DIR] [--output-name OUTPUT_NAME]
               pdf_file

Extract text with coordinates from PDF for feature vectors

positional arguments:
  pdf_file              Path to PDF file

options:
  -h, --help            show this help message and exit
  --json                Export as JSON with full coordinate data
  --csv                 Export as CSV for analysis
  --features            Export feature vectors for ML
  --text                Export text only (no coordinates)
  --all                 Export in all formats
  --ocr                 Use OCR for scanned PDFs
  --normalize           Normalize coordinates to [0,1] range
  --group {line,block,page}
                        Text grouping for text export (default: line)
  --output-dir OUTPUT_DIR
                        Output directory (default: output_data)
  --output-name OUTPUT_NAME
                        Base name for output files (default: PDF filename)

Examples:
  # Basic extraction
  python main.py document.pdf

  # Export as feature vectors
  python main.py document.pdf --features

  # Export multiple formats
  python main.py document.pdf --json --csv --features

  # Use OCR for scanned PDFs
  python main.py scanned.pdf --ocr

  # Normalize coordinates for ML
  python main.py document.pdf --features --normalize
```
### Batch Processing with JSON Export

TBD

### Using with all plugins to extract data

```bash
python3 main.py test_samples/certmedrecdoc_factsheet_icn909160.pdf --all
```

## Programming Interface
TBD

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

## Development

### Project Structure

```
navina_text_extractor/
 main.py      # Main OCR processing module
 modules      # Processing modules
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
