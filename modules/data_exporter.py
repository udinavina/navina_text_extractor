#!/usr/bin/env python3
"""
Data Exporter Module - Save extracted data in various formats for feature vectors
Handles exporting to JSON, CSV, NumPy arrays, and other ML-friendly formats
"""

import json
import csv
import os
import hashlib
import shutil
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from .pdf_parser import TextElement
from .text_processor import TextProcessor


class DataExporter:
    """Export extracted text data in formats suitable for feature vectors"""
    
    def __init__(self, output_dir: str = "output_data", source_file: str = None):
        """
        Initialize data exporter
        
        Args:
            output_dir: Base directory to save output files
            source_file: Source PDF file path for creating subdirectory
        """
        self.base_output_dir = output_dir
        self.source_file = source_file
        
        if source_file:
            # Create subdirectory with file_name_lastsha256
            file_name = os.path.splitext(os.path.basename(source_file))[0]
            full_hash = self._calculate_file_hash(source_file)
            last_8_hash = full_hash[-8:]  # Last 8 characters for directory
            self.output_dir = os.path.join(output_dir, f"{file_name}_{last_8_hash}")
            self.file_hash = full_hash  # Full hash for filename
        else:
            self.output_dir = output_dir
            self.file_hash = None
            
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Don't copy file in constructor - do it after successful extraction
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate SHA256 hash of file
        
        Args:
            file_path: Path to file
            
        Returns:
            First 8 characters of SHA256 hash
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()  # Use full SHA256 hash
        except Exception as e:
            print(f"Error calculating hash for {file_path}: {e}")
            return "unknown"
    
    def _copy_original_file(self, source_file: str) -> str:
        """
        Copy original file to output directory with SHA256 filename
        
        Args:
            source_file: Path to original file
            
        Returns:
            Path to copied file
        """
        try:
            # Get file extension
            _, ext = os.path.splitext(source_file)
            
            # Create destination path: <sha256>.filetype
            dest_filename = f"{self.file_hash}{ext}"
            dest_path = os.path.join(self.output_dir, dest_filename)
            
            # Copy the file
            shutil.copy2(source_file, dest_path)
            
            return dest_path
            
        except Exception as e:
            print(f"Error copying original file: {e}")
            return ""
    
    def copy_original_file(self) -> str:
        """
        Copy original file to output directory (public method)
        
        Returns:
            Path to copied file
        """
        if self.source_file and self.file_hash:
            return self._copy_original_file(self.source_file)
        return ""
        
    def _get_output_path(self, base_name: str, extension: str) -> str:
        """Generate output file path with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_name}_{timestamp}.{extension}"
        return os.path.join(self.output_dir, filename)
    
    def export_to_json(self, elements: List[TextElement], 
                      metadata: Optional[Dict[str, Any]] = None,
                      output_name: str = "extracted_text") -> str:
        """
        Export to JSON format with full text and coordinate data
        
        Args:
            elements: List of TextElement objects
            metadata: Additional metadata to include
            output_name: Base name for output file
            
        Returns:
            Path to saved file
        """
        output_path = self._get_output_path(output_name, "json")
        
        data = {
            "metadata": metadata or {},
            "extraction_timestamp": datetime.now().isoformat(),
            "total_elements": len(elements),
            "elements": [elem.to_dict() for elem in elements]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"Exported JSON to: {output_path}")
        return output_path
    
    def export_to_csv(self, elements: List[TextElement],
                     output_name: str = "extracted_text") -> str:
        """
        Export to CSV format for easy analysis
        
        Args:
            elements: List of TextElement objects
            output_name: Base name for output file
            
        Returns:
            Path to saved file
        """
        output_path = self._get_output_path(output_name, "csv")
        
        fieldnames = [
            'text', 'x0', 'y0', 'x1', 'y1', 'width', 'height',
            'center_x', 'center_y', 'area', 'page_num', 
            'font_size', 'font_name'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for elem in elements:
                row = elem.to_dict()
                writer.writerow(row)
                
        print(f"Exported CSV to: {output_path}")
        return output_path
    
    def export_feature_vectors(self, elements: List[TextElement],
                             page_dimensions: Dict[int, tuple],
                             output_name: str = "feature_vectors") -> Dict[str, str]:
        """
        Export feature vectors for ML applications
        
        Args:
            elements: List of TextElement objects
            page_dimensions: Page dimensions from PDFParser
            output_name: Base name for output files
            
        Returns:
            Dictionary of output file paths
        """
        processor = TextProcessor()
        output_paths = {}
        
        # Create feature matrix
        feature_matrix, agg_features, pattern_features = processor.create_feature_matrix(
            elements, page_dimensions
        )
        
        # Save raw feature matrix as NumPy array
        if len(feature_matrix) > 0:
            npy_path = self._get_output_path(f"{output_name}_matrix", "npy")
            np.save(npy_path, feature_matrix)
            output_paths['feature_matrix'] = npy_path
            print(f"Exported feature matrix to: {npy_path}")
        
        # Save aggregate features
        agg_path = self._get_output_path(f"{output_name}_aggregate", "json")
        agg_data = processor.calculate_text_features(elements)
        with open(agg_path, 'w') as f:
            json.dump(agg_data, f, indent=2)
        output_paths['aggregate_features'] = agg_path
        print(f"Exported aggregate features to: {agg_path}")
        
        # Save spatial grid features
        grid_features = processor.create_spatial_grid_features(
            elements, page_dimensions, grid_size=(10, 10)
        )
        grid_path = self._get_output_path(f"{output_name}_spatial_grid", "npy")
        np.save(grid_path, grid_features)
        output_paths['spatial_grid'] = grid_path
        print(f"Exported spatial grid to: {grid_path}")
        
        # Create comprehensive DataFrame for analysis
        df_data = []
        for elem in elements:
            row = elem.to_dict()
            row['text_length'] = len(elem.text)
            row['is_numeric'] = elem.text.replace('.', '').replace(',', '').strip().isdigit()
            row['is_uppercase'] = elem.text.isupper()
            df_data.append(row)
            
        df = pd.DataFrame(df_data)
        
        # Save as Parquet for efficient storage (if available)
        try:
            parquet_path = self._get_output_path(f"{output_name}_full", "parquet")
            df.to_parquet(parquet_path, index=False)
            output_paths['full_data'] = parquet_path
            print(f"Exported full data to: {parquet_path}")
        except ImportError:
            # Fallback to CSV if parquet not available
            csv_path = self._get_output_path(f"{output_name}_full", "csv")
            df.to_csv(csv_path, index=False)
            output_paths['full_data'] = csv_path
            print(f"Exported full data to CSV (parquet not available): {csv_path}")
        
        # Save summary statistics
        summary_path = self._get_output_path(f"{output_name}_summary", "json")
        summary = {
            "total_elements": len(elements),
            "total_pages": len(set(elem.page_num for elem in elements)),
            "aggregate_features": agg_data,
            "pattern_features": processor.extract_text_patterns(elements),
            "spatial_grid_shape": grid_features.shape,
            "feature_matrix_shape": feature_matrix.shape if len(feature_matrix) > 0 else [0, 0]
        }
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        output_paths['summary'] = summary_path
        print(f"Exported summary to: {summary_path}")
        
        return output_paths
    
    def export_for_clustering(self, elements: List[TextElement],
                            normalize: bool = True,
                            output_name: str = "clustering_data") -> str:
        """
        Export data optimized for clustering algorithms
        
        Args:
            elements: List of TextElement objects
            normalize: Whether to normalize coordinates
            output_name: Base name for output file
            
        Returns:
            Path to saved file
        """
        # Prepare clustering features
        features = []
        labels = []
        
        for elem in elements:
            # Spatial features
            feature_vec = [
                elem.center_x,
                elem.center_y,
                elem.width,
                elem.height,
                elem.area,
                len(elem.text),  # Text length as feature
                elem.font_size or 0.0
            ]
            features.append(feature_vec)
            labels.append(elem.text)
            
        features = np.array(features)
        
        # Normalize if requested
        if normalize and len(features) > 0:
            try:
                from sklearn.preprocessing import StandardScaler
                scaler = StandardScaler()
                features = scaler.fit_transform(features)
                
                # Save scaler parameters
                scaler_path = self._get_output_path(f"{output_name}_scaler", "json")
                scaler_params = {
                    "mean": scaler.mean_.tolist(),
                    "scale": scaler.scale_.tolist()
                }
                with open(scaler_path, 'w') as f:
                    json.dump(scaler_params, f, indent=2)
            except ImportError:
                print("Warning: scikit-learn not available for normalization")
                
        # Save features and labels
        output_path = self._get_output_path(output_name, "npz")
        np.savez(output_path, features=features, labels=labels)
        
        print(f"Exported clustering data to: {output_path}")
        return output_path
    
    def export_text_only(self, elements: List[TextElement],
                        group_by: str = "line",
                        output_name: str = "extracted_text") -> str:
        """
        Export just the text content, optionally grouped
        
        Args:
            elements: List of TextElement objects
            group_by: How to group text - "line", "block", or "page"
            output_name: Base name for output file
            
        Returns:
            Path to saved file
        """
        output_path = self._get_output_path(output_name, "txt")
        processor = TextProcessor()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if group_by == "line":
                lines = processor.group_into_lines(elements)
                for line in lines:
                    line_text = ' '.join(elem.text for elem in line)
                    f.write(line_text + '\n')
                    
            elif group_by == "block":
                blocks = processor.group_into_blocks(elements)
                for block in blocks:
                    block_text = ' '.join(elem.text for elem in block)
                    f.write(block_text + '\n\n')
                    
            elif group_by == "page":
                pages = {}
                for elem in elements:
                    if elem.page_num not in pages:
                        pages[elem.page_num] = []
                    pages[elem.page_num].append(elem)
                    
                for page_num in sorted(pages.keys()):
                    f.write(f"--- Page {page_num} ---\n")
                    page_text = ' '.join(elem.text for elem in pages[page_num])
                    f.write(page_text + '\n\n')
                    
            else:
                # Just dump all text
                all_text = ' '.join(elem.text for elem in elements)
                f.write(all_text)
                
        print(f"Exported text to: {output_path}")
        return output_path
    
    def create_visualization_data(self, elements: List[TextElement],
                                output_name: str = "visualization") -> str:
        """
        Create data file for visualization purposes
        
        Args:
            elements: List of TextElement objects
            output_name: Base name for output file
            
        Returns:
            Path to saved file
        """
        output_path = self._get_output_path(output_name, "json")
        
        # Group by page for visualization
        pages = {}
        for elem in elements:
            if elem.page_num not in pages:
                pages[elem.page_num] = []
                
            viz_elem = {
                "text": elem.text,
                "bbox": [elem.x0, elem.y0, elem.x1, elem.y1],
                "center": [elem.center_x, elem.center_y],
                "size": elem.font_size,
                "area": elem.area
            }
            pages[elem.page_num].append(viz_elem)
            
        viz_data = {
            "pages": pages,
            "total_pages": len(pages),
            "total_elements": len(elements)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(viz_data, f, indent=2)
            
        print(f"Exported visualization data to: {output_path}")
        return output_path
    
    def export_text_with_coordinates(self, elements: List[TextElement],
                                   output_name: str = "text_with_coordinates") -> str:
        """
        Export text with vector coordinates next to each extracted text
        
        Args:
            elements: List of TextElement objects
            output_name: Base name for output file
            
        Returns:
            Path to saved file
        """
        output_path = self._get_output_path(output_name, "txt")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("Extracted Text with Vector Coordinates\n")
            f.write("=" * 50 + "\n")
            f.write(f"Total elements: {len(elements)}\n")
            f.write(f"Extraction date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Group by page
            pages = {}
            for elem in elements:
                if elem.page_num not in pages:
                    pages[elem.page_num] = []
                pages[elem.page_num].append(elem)
            
            for page_num in sorted(pages.keys()):
                f.write(f"PAGE {page_num}\n")
                f.write("-" * 20 + "\n")
                
                page_elements = pages[page_num]
                # Sort by Y position (top to bottom), then X position (left to right)
                page_elements.sort(key=lambda e: (e.y0, e.x0))
                
                for i, elem in enumerate(page_elements, 1):
                    # Format: [ID] "text" -> (x0, y0, x1, y1) [center: (cx, cy)] [size: widthheight] [font: size]
                    f.write(f"[{i:3d}] \"{elem.text}\" -> ")
                    f.write(f"({elem.x0:.1f}, {elem.y0:.1f}, {elem.x1:.1f}, {elem.y1:.1f}) ")
                    f.write(f"[center: ({elem.center_x:.1f}, {elem.center_y:.1f})] ")
                    f.write(f"[size: {elem.width:.1f}{elem.height:.1f}]")
                    if elem.font_size:
                        f.write(f" [font: {elem.font_size:.1f}pt]")
                    if elem.font_name:
                        f.write(f" [{elem.font_name}]")
                    f.write("\n")
                
                f.write("\n")
            
            # Add summary statistics
            f.write("SUMMARY STATISTICS\n")
            f.write("=" * 20 + "\n")
            
            # Calculate statistics
            total_chars = sum(len(elem.text) for elem in elements)
            avg_font_size = np.mean([elem.font_size for elem in elements if elem.font_size is not None])
            
            # Bounding box of all text
            if elements:
                min_x = min(elem.x0 for elem in elements)
                min_y = min(elem.y0 for elem in elements)
                max_x = max(elem.x1 for elem in elements)
                max_y = max(elem.y1 for elem in elements)
                
                f.write(f"Total characters: {total_chars}\n")
                f.write(f"Average font size: {avg_font_size:.1f}pt\n")
                f.write(f"Text bounding box: ({min_x:.1f}, {min_y:.1f}) to ({max_x:.1f}, {max_y:.1f})\n")
                f.write(f"Document area covered: {(max_x - min_x):.1f}  {(max_y - min_y):.1f}\n")
            
            # Font analysis
            font_counts = {}
            for elem in elements:
                if elem.font_name:
                    font_counts[elem.font_name] = font_counts.get(elem.font_name, 0) + 1
            
            if font_counts:
                f.write(f"\nFonts used:\n")
                for font, count in sorted(font_counts.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"  {font}: {count} elements\n")
                    
        print(f"Exported text with coordinates to: {output_path}")
        return output_path