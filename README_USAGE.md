# OCR Extract - PDF Text Extraction with Coordinates

Extract text and coordinates from PDF documents for feature vector generation and machine learning applications.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Extract text with coordinates from a PDF:

```bash
python main.py document.pdf
```

This creates a JSON file with all text elements and their coordinates.

### Command Line Options

```bash
python main.py <pdf_file> [options]
```

#### Export Formats
- `--json` - Export as JSON with full coordinate data (default)
- `--csv` - Export as CSV for spreadsheet analysis
- `--features` - Export feature vectors for machine learning
- `--text` - Export text only (no coordinates)
- `--all` - Export in all formats

#### Processing Options
- `--ocr` - Use OCR for scanned PDFs
- `--normalize` - Normalize coordinates to [0,1] range
- `--group {line,block,page}` - Text grouping for text export

#### Output Options
- `--output-dir <dir>` - Output directory (default: output_data)
- `--output-name <name>` - Base name for output files

### Examples

1. **Basic extraction with JSON output:**
   ```bash
   python main.py invoice.pdf
   ```

2. **Extract with feature vectors for ML:**
   ```bash
   python main.py document.pdf --features --normalize
   ```

3. **Process scanned PDF with OCR:**
   ```bash
   python main.py scanned.pdf --ocr --all
   ```

4. **Export to multiple formats:**
   ```bash
   python main.py report.pdf --json --csv --features
   ```

5. **Extract text grouped by blocks:**
   ```bash
   python main.py article.pdf --text --group block
   ```

## Output Directory Structure

Each processed document is saved under a unique directory:
```
output_data/
 filename_sha256hash/
     filename_timestamp.json
     filename_timestamp.csv
     filename_coordinates_timestamp.txt  # Required: Text with vector coordinates
     filename_viz_timestamp.json
     ...
```

Example: `output_data/test_document_39f4cde2/`

## Output Files

### JSON Format (`*_[timestamp].json`)
Contains all text elements with:
- Text content
- Bounding box coordinates (x0, y0, x1, y1)
- Width and height
- Center coordinates
- Page number
- Font information (if available)

### CSV Format (`*_[timestamp].csv`)
Tabular format with all text elements and properties.

### Feature Vectors (`*_[timestamp]_*.npy`)
- `*_matrix.npy` - Raw feature matrix for each text element
- `*_spatial_grid.npy` - Spatial grid features (text density)
- `*_aggregate.json` - Document-level features
- `*_clustering.npz` - Normalized features for clustering

### Text Output (`*_[timestamp].txt`)
Plain text extracted from PDF, grouped by line/block/page.

### Text with Coordinates (`*_coordinates_[timestamp].txt`) - **Required**
Human-readable format showing each extracted text with its vector coordinates:
```
[ID] "text" -> (x0, y0, x1, y1) [center: (cx, cy)] [size: widthheight] [font: size]
```

### Visualization Data (`*_[timestamp].json`)
Structured data for creating visualizations of text layout.

## Feature Vectors for ML

The extracted features are designed for machine learning applications:

### Element-Level Features
Each text element provides:
1. Spatial coordinates (x0, y0, x1, y1)
2. Center position (center_x, center_y)
3. Dimensions (width, height, area)
4. Font size (when available)
5. Page number

### Document-Level Features
- Total text area
- Average font size
- Text density
- Spatial spread
- Coverage ratio

### Spatial Grid Features
- 10x10 grid showing text density
- Useful for layout classification

### Pattern Features
- Email/phone/URL detection
- Date patterns
- Numeric content
- Word statistics

## Use Cases

1. **Document Classification**
   - Use spatial features to classify document types
   - Identify forms, invoices, reports, etc.

2. **Information Extraction**
   - Extract specific fields based on position
   - Build training data for NER models

3. **Layout Analysis**
   - Understand document structure
   - Detect headers, footers, columns

4. **OCR Post-Processing**
   - Improve OCR results using spatial context
   - Group related text elements

## Tips

- Use `--ocr` flag for scanned PDFs or when text extraction fails
- Normalize coordinates with `--normalize` for consistent ML features
- Export multiple formats with `--all` to explore the data
- Check visualization data to understand text layout

## Troubleshooting

1. **No text found**
   - Try using `--ocr` flag
   - Check if PDF is password protected
   - Verify PDF is not corrupted

2. **Memory issues with large PDFs**
   - Process page by page (modify code)
   - Reduce grid size for spatial features

3. **OCR not working**
   - Install Tesseract: `sudo apt-get install tesseract-ocr`
   - Verify with: `tesseract --version`
