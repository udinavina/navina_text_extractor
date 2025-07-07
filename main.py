#!/usr/bin/env python3
"""
OCR Extract PDF text extraction with coordinates for feature vectors
Simple command-line interface for extracting text and coordinates from PDFs
"""

import argparse
import sys
import os
from modules.pdf_parser import PDFParser
from modules.text_processor import TextProcessor
from modules.data_exporter import DataExporter


def main():
    parser = argparse.ArgumentParser(
        description="Extract text with coordinates from PDF for feature vectors",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
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
        """
    )
    
    # Required argument
    parser.add_argument('pdf_file', help='Path to PDF file')
    
    # Export format options
    parser.add_argument('--json', action='store_true',
                       help='Export as JSON with full coordinate data')
    parser.add_argument('--csv', action='store_true',
                       help='Export as CSV for analysis')
    parser.add_argument('--features', action='store_true',
                       help='Export feature vectors for ML')
    parser.add_argument('--text', action='store_true',
                       help='Export text only (no coordinates)')
    parser.add_argument('--all', action='store_true',
                       help='Export in all formats')
    
    # Processing options
    parser.add_argument('--ocr', action='store_true',
                       help='Use OCR for scanned PDFs')
    parser.add_argument('--normalize', action='store_true',
                       help='Normalize coordinates to [0,1] range')
    parser.add_argument('--group', choices=['line', 'block', 'page'],
                       default='line',
                       help='Text grouping for text export (default: line)')
    
    # Output options
    parser.add_argument('--output-dir', default='output_data',
                       help='Output directory (default: output_data)')
    parser.add_argument('--output-name', 
                       help='Base name for output files (default: PDF filename)')
    
    args = parser.parse_args()
    
    # Validate PDF file
    if not os.path.exists(args.pdf_file):
        print(f"Error: PDF file not found: {args.pdf_file}")
        sys.exit(1)
        
    # Set output name
    if not args.output_name:
        args.output_name = os.path.splitext(os.path.basename(args.pdf_file))[0]
    
    # If no format specified, default to JSON
    if not any([args.json, args.csv, args.features, args.text, args.all]):
        args.json = True
        
    # If --all specified, enable all formats
    if args.all:
        args.json = True
        args.csv = True
        args.features = True
        args.text = True
    
    # Initialize components
    print(f"\nProcessing: {args.pdf_file}")
    print(f"Base output directory: {args.output_dir}")
    print(f"OCR enabled: {args.ocr}")
    print(f"Normalize coordinates: {args.normalize}")
    
    pdf_parser = PDFParser(use_ocr=args.ocr)
    text_processor = TextProcessor()
    exporter = DataExporter(output_dir=args.output_dir, source_file=args.pdf_file)
    
    print(f"Specific output directory: {exporter.output_dir}\n")
    
    # Extract text with coordinates
    print("Extracting text with coordinates...")
    elements = pdf_parser.extract_text_with_coordinates(args.pdf_file)
    
    if not elements:
        print("Warning: No text elements found in PDF")
        if not args.ocr:
            print("Tip: Try using --ocr flag for scanned PDFs")
        
        # For corrupted PDFs, still copy the original file and create directory structure
        copied_path = exporter.copy_original_file()
        if copied_path:
            print(f"Original file copied to: {copied_path}")
        
        print("Directory structure created despite extraction failure")
        print(f"Output directory: {exporter.output_dir}")
        sys.exit(1)
        
    # Copy original file after successful extraction
    copied_path = exporter.copy_original_file()
    if copied_path:
        print(f"Original file copied to: {copied_path}")
        
    print(f"Extracted {len(elements)} text elements")
    
    # Get page dimensions for normalization
    page_dims = pdf_parser.get_page_dimensions(args.pdf_file)
    
    # Normalize if requested
    if args.normalize:
        print("Normalizing coordinates...")
        elements = pdf_parser.normalize_coordinates(elements, page_dims)
    
    # Export in requested formats
    output_files = []
    
    if args.json:
        print("\nExporting JSON...")
        metadata = {
            "source_file": args.pdf_file,
            "ocr_used": args.ocr,
            "normalized": args.normalize,
            "page_count": len(page_dims)
        }
        json_path = exporter.export_to_json(elements, metadata, args.output_name)
        output_files.append(json_path)
        
    if args.csv:
        print("\nExporting CSV...")
        csv_path = exporter.export_to_csv(elements, args.output_name)
        output_files.append(csv_path)
        
    if args.features:
        print("\nExporting feature vectors...")
        feature_paths = exporter.export_feature_vectors(
            elements, page_dims, args.output_name
        )
        output_files.extend(feature_paths.values())
        
        # Also export clustering-ready data
        cluster_path = exporter.export_for_clustering(
            elements, normalize=True, output_name=f"{args.output_name}_clustering"
        )
        output_files.append(cluster_path)
        
    if args.text:
        print(f"\nExporting text (grouped by {args.group})...")
        text_path = exporter.export_text_only(
            elements, group_by=args.group, output_name=args.output_name
        )
        output_files.append(text_path)
    
    # Create visualization data
    print("\nCreating visualization data...")
    viz_path = exporter.create_visualization_data(elements, f"{args.output_name}_viz")
    output_files.append(viz_path)
    
    # Always create text with coordinates file (required by CLAUDE.md)
    print("\nCreating text with coordinates file...")
    coords_path = exporter.export_text_with_coordinates(elements, f"{args.output_name}_coordinates")
    output_files.append(coords_path)
    
    # Summary
    print("\n" + "="*50)
    print("Extraction complete!")
    print(f"Total elements extracted: {len(elements)}")
    print(f"Pages processed: {len(page_dims)}")
    print(f"\nOutput files created: {len(output_files)}")
    for file_path in output_files:
        print(f"  - {file_path}")
    
    # Print sample of extracted data
    print("\nSample extracted elements:")
    for i, elem in enumerate(elements[:3]):
        print(f"\n[{i+1}] Text: '{elem.text}'")
        print(f"    Position: ({elem.x0:.1f}, {elem.y0:.1f})")
        print(f"    Size: {elem.width:.1f} x {elem.height:.1f}")
        if elem.font_size:
            print(f"    Font size: {elem.font_size:.1f}")
    
    if len(elements) > 3:
        print(f"\n... and {len(elements) - 3} more elements")


if __name__ == "__main__":
    main()
