#!/usr/bin/env python3
"""
Text Processor Module - Process extracted text for feature vector generation
Handles text cleaning, grouping, and feature engineering
"""

import re
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from collections import defaultdict
from .pdf_parser import TextElement


class TextProcessor:
    """Process extracted text elements for feature vector generation"""
    
    def __init__(self):
        """Initialize text processor"""
        self.stop_words = set()  # Can be loaded from file if needed
        
    def clean_text(self, text: str) -> str:
        """
        Clean text for processing
        
        Args:
            text: Raw text string
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove non-printable characters
        text = ''.join(char for char in text if char.isprintable())
        
        return text
    
    def group_into_lines(self, elements: List[TextElement], 
                        y_tolerance: float = 5.0) -> List[List[TextElement]]:
        """
        Group text elements into lines based on Y coordinates
        
        Args:
            elements: List of TextElement objects
            y_tolerance: Maximum Y difference for same line
            
        Returns:
            List of lines, each line is a list of TextElement objects
        """
        if not elements:
            return []
            
        # Group by page first
        pages = defaultdict(list)
        for elem in elements:
            pages[elem.page_num].append(elem)
            
        all_lines = []
        
        for page_num, page_elements in pages.items():
            # Sort by Y coordinate (top to bottom), then X (left to right)
            page_elements.sort(key=lambda e: (e.y0, e.x0))
            
            lines = []
            current_line = [page_elements[0]]
            current_y = page_elements[0].y0
            
            for elem in page_elements[1:]:
                if abs(elem.y0 - current_y) <= y_tolerance:
                    current_line.append(elem)
                else:
                    # Sort line by X coordinate
                    current_line.sort(key=lambda e: e.x0)
                    lines.append(current_line)
                    current_line = [elem]
                    current_y = elem.y0
                    
            # Don't forget the last line
            if current_line:
                current_line.sort(key=lambda e: e.x0)
                lines.append(current_line)
                
            all_lines.extend(lines)
            
        return all_lines
    
    def group_into_blocks(self, elements: List[TextElement],
                         x_tolerance: float = 50.0,
                         y_tolerance: float = 20.0) -> List[List[TextElement]]:
        """
        Group text elements into blocks/paragraphs based on proximity
        
        Args:
            elements: List of TextElement objects
            x_tolerance: Maximum X gap between elements in same block
            y_tolerance: Maximum Y gap between lines in same block
            
        Returns:
            List of blocks, each block is a list of TextElement objects
        """
        lines = self.group_into_lines(elements, y_tolerance=5.0)
        
        if not lines:
            return []
            
        blocks = []
        current_block = [lines[0]]
        
        for line in lines[1:]:
            # Check if this line should be in the same block as previous
            prev_line = current_block[-1]
            
            # Get the rightmost X of previous line and leftmost X of current line
            prev_right = max(elem.x1 for elem in prev_line)
            prev_left = min(elem.x0 for elem in prev_line)
            curr_left = min(elem.x0 for elem in line)
            
            # Get Y positions
            prev_y = prev_line[0].y1  # Bottom of previous line
            curr_y = line[0].y0  # Top of current line
            
            # Check if lines are close enough
            y_gap = curr_y - prev_y
            x_aligned = abs(curr_left - prev_left) <= x_tolerance
            
            if y_gap <= y_tolerance and x_aligned:
                current_block.append(line)
            else:
                # Start new block
                blocks.append(current_block)
                current_block = [line]
                
        # Don't forget the last block
        if current_block:
            blocks.append(current_block)
            
        # Flatten blocks from lines to elements
        flattened_blocks = []
        for block in blocks:
            flattened = []
            for line in block:
                flattened.extend(line)
            flattened_blocks.append(flattened)
            
        return flattened_blocks
    
    def calculate_text_features(self, elements: List[TextElement]) -> Dict[str, Any]:
        """
        Calculate aggregate features from text elements
        
        Args:
            elements: List of TextElement objects
            
        Returns:
            Dictionary of calculated features
        """
        if not elements:
            return {
                'num_elements': 0,
                'total_area': 0.0,
                'avg_font_size': 0.0,
                'text_density': 0.0,
                'spatial_spread_x': 0.0,
                'spatial_spread_y': 0.0
            }
            
        # Basic statistics
        num_elements = len(elements)
        
        # Area calculations
        areas = [elem.area for elem in elements]
        total_area = sum(areas)
        avg_area = np.mean(areas)
        
        # Font size statistics (excluding None values)
        font_sizes = [elem.font_size for elem in elements if elem.font_size is not None]
        avg_font_size = np.mean(font_sizes) if font_sizes else 0.0
        
        # Spatial distribution
        x_coords = [elem.center_x for elem in elements]
        y_coords = [elem.center_y for elem in elements]
        
        spatial_spread_x = np.std(x_coords) if len(x_coords) > 1 else 0.0
        spatial_spread_y = np.std(y_coords) if len(y_coords) > 1 else 0.0
        
        # Text density (characters per unit area)
        total_chars = sum(len(elem.text) for elem in elements)
        text_density = total_chars / total_area if total_area > 0 else 0.0
        
        # Bounding box of all text
        if elements:
            min_x = min(elem.x0 for elem in elements)
            min_y = min(elem.y0 for elem in elements)
            max_x = max(elem.x1 for elem in elements)
            max_y = max(elem.y1 for elem in elements)
            bbox_area = (max_x - min_x) * (max_y - min_y)
            coverage_ratio = total_area / bbox_area if bbox_area > 0 else 0.0
        else:
            coverage_ratio = 0.0
            
        return {
            'num_elements': num_elements,
            'total_area': total_area,
            'avg_area': avg_area,
            'avg_font_size': avg_font_size,
            'text_density': text_density,
            'spatial_spread_x': spatial_spread_x,
            'spatial_spread_y': spatial_spread_y,
            'coverage_ratio': coverage_ratio,
            'total_chars': total_chars
        }
    
    def create_spatial_grid_features(self, elements: List[TextElement], 
                                   page_dimensions: Dict[int, Tuple[float, float]],
                                   grid_size: Tuple[int, int] = (10, 10)) -> np.ndarray:
        """
        Create spatial grid features by dividing page into grid cells
        
        Args:
            elements: List of TextElement objects
            page_dimensions: Page dimensions from PDFParser
            grid_size: (rows, cols) for the grid
            
        Returns:
            2D array of text density in each grid cell
        """
        rows, cols = grid_size
        
        # Group elements by page
        pages = defaultdict(list)
        for elem in elements:
            pages[elem.page_num].append(elem)
            
        # Create grid for each page
        grids = []
        
        for page_num in sorted(pages.keys()):
            if page_num not in page_dimensions:
                continue
                
            width, height = page_dimensions[page_num]
            grid = np.zeros((rows, cols))
            
            # Calculate cell dimensions
            cell_width = width / cols
            cell_height = height / rows
            
            # Assign text to grid cells
            for elem in pages[page_num]:
                # Find which cells this element overlaps
                start_col = int(elem.x0 / cell_width)
                end_col = int(elem.x1 / cell_width)
                start_row = int(elem.y0 / cell_height)
                end_row = int(elem.y1 / cell_height)
                
                # Clip to grid bounds
                start_col = max(0, min(start_col, cols - 1))
                end_col = max(0, min(end_col, cols - 1))
                start_row = max(0, min(start_row, rows - 1))
                end_row = max(0, min(end_row, rows - 1))
                
                # Add text length to overlapping cells
                text_len = len(elem.text)
                for r in range(start_row, end_row + 1):
                    for c in range(start_col, end_col + 1):
                        grid[r, c] += text_len
                        
            grids.append(grid)
            
        # Combine grids from all pages
        if grids:
            return np.stack(grids).mean(axis=0)  # Average across pages
        else:
            return np.zeros((rows, cols))
    
    def extract_text_patterns(self, elements: List[TextElement]) -> Dict[str, Any]:
        """
        Extract pattern-based features from text
        
        Args:
            elements: List of TextElement objects
            
        Returns:
            Dictionary of pattern features
        """
        all_text = ' '.join(elem.text for elem in elements)
        
        patterns = {
            'has_email': bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', all_text)),
            'has_phone': bool(re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', all_text)),
            'has_url': bool(re.search(r'https?://[^\s]+', all_text)),
            'has_date': bool(re.search(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', all_text)),
            'num_numbers': len(re.findall(r'\b\d+\b', all_text)),
            'num_uppercase_words': len(re.findall(r'\b[A-Z]{2,}\b', all_text)),
            'avg_word_length': np.mean([len(word) for word in all_text.split()]) if all_text else 0.0
        }
        
        return patterns
    
    def create_feature_matrix(self, elements: List[TextElement],
                            page_dimensions: Dict[int, Tuple[float, float]]) -> np.ndarray:
        """
        Create complete feature matrix for ML applications
        
        Args:
            elements: List of TextElement objects
            page_dimensions: Page dimensions from PDFParser
            
        Returns:
            2D numpy array of features
        """
        if not elements:
            return np.array([])
            
        # Individual element features
        element_features = []
        for elem in elements:
            features = elem.to_feature_vector()
            element_features.append(features)
            
        # Convert to numpy array
        feature_matrix = np.array(element_features)
        
        # Add aggregate features as additional rows
        agg_features = self.calculate_text_features(elements)
        agg_vector = list(agg_features.values())
        
        # Add pattern features
        pattern_features = self.extract_text_patterns(elements)
        pattern_vector = [float(v) if isinstance(v, bool) else v 
                         for v in pattern_features.values()]
        
        return feature_matrix, agg_vector, pattern_vector