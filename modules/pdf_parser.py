#!/usr/bin/env python3
"""
PDF Parser Module - Extract text with coordinates for feature vector generation
Handles PDF text extraction with precise coordinate tracking
"""

import pdfplumber
import sys
import os
from contextlib import redirect_stderr
from io import StringIO

# Avoid conflicts with other 'fitz' packages
fitz = None
try:
    # Try the direct import first
    import fitz as pymupdf_fitz
    fitz = pymupdf_fitz
    print("PyMuPDF loaded successfully.")
except ImportError:
    try:
        import pymupdf
        fitz = pymupdf
        print("PyMuPDF loaded via pymupdf module.")
    except ImportError:
        print("Warning: PyMuPDF not installed. Using pdfplumber only.")
        # We'll rely on pdfplumber for all operations
        
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
from dataclasses import dataclass, asdict

@dataclass
class TextElement:
    """Represents a text element with position and properties for feature extraction"""
    text: str
    x0: float  # Left coordinate
    y0: float  # Top coordinate  
    x1: float  # Right coordinate
    y1: float  # Bottom coordinate
    width: float
    height: float
    page_num: int
    font_size: Optional[float] = None
    font_name: Optional[str] = None
    
    @property
    def center_x(self) -> float:
        """X coordinate of text center"""
        return (self.x0 + self.x1) / 2
    
    @property
    def center_y(self) -> float:
        """Y coordinate of text center"""
        return (self.y0 + self.y1) / 2
    
    @property
    def area(self) -> float:
        """Area of text bounding box"""
        return self.width * self.height
    
    def to_feature_vector(self) -> List[float]:
        """Convert to numerical feature vector for ML"""
        return [
            self.x0, self.y0, self.x1, self.y1,
            self.center_x, self.center_y,
            self.width, self.height, self.area,
            self.font_size or 0.0,
            float(self.page_num)
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary including computed properties"""
        data = asdict(self)
        data.update({
            'center_x': self.center_x,
            'center_y': self.center_y,
            'area': self.area
        })
        return data


class PDFParser:
    """Extract text and coordinates from PDF for feature vector generation"""
    
    def __init__(self, use_ocr: bool = True):
        """
        Initialize PDF parser
        
        Args:
            use_ocr: Whether to use OCR for scanned PDFs
        """
        self.use_ocr = use_ocr
        
    def extract_with_pdfplumber(self, pdf_path: str) -> List[TextElement]:
        """
        Extract text using pdfplumber (better for structured PDFs)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of TextElement objects
        """
        elements = []
        
        try:
            # Suppress stderr to hide corruption warnings
            with redirect_stderr(StringIO()):
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages, 1):
                        # Extract words with bounding boxes
                        words = page.extract_words(
                            x_tolerance=3,
                            y_tolerance=3,
                            keep_blank_chars=False,
                            use_text_flow=True,
                            extra_attrs=['fontname', 'size']
                        )
                    
                        for word in words:
                            # Check if word has required fields
                            # pdfplumber uses 'top' and 'bottom' instead of 'y0' and 'y1'
                            if all(key in word for key in ['text', 'x0', 'x1']):
                                # Get y coordinates - pdfplumber uses 'top' and 'bottom'
                                y0 = word.get('top', word.get('y0'))
                                y1 = word.get('bottom', word.get('y1'))
                                
                                if y0 is not None and y1 is not None:
                                    element = TextElement(
                                        text=word['text'],
                                        x0=float(word['x0']),
                                        y0=float(y0),
                                        x1=float(word['x1']),
                                        y1=float(y1),
                                        width=float(word['x1'] - word['x0']),
                                        height=float(y1 - y0),
                                        page_num=page_num,
                                        font_size=word.get('size'),
                                        font_name=word.get('fontname')
                                    )
                                    elements.append(element)
                                else:
                                    print(f"Warning: Missing y coordinates for word: {word['text']}")
                        
        except Exception as e:
            print(f"Error with pdfplumber: {str(e)}")
            # Don't print traceback for common PDF issues
            
        return elements
    
    def extract_with_pymupdf(self, pdf_path: str) -> List[TextElement]:
        """
        Extract text using PyMuPDF (better for scanned PDFs and OCR)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of TextElement objects
        """
        elements = []
        
        if fitz is None:
            print("PyMuPDF not available. Skipping PyMuPDF extraction.")
            return elements
        
        try:
            pdf = fitz.open(pdf_path)
            
            if pdf.page_count == 0:
                print(f"PyMuPDF: PDF has 0 pages - file may be corrupted")
                pdf.close()
                return elements
            
            print(f"PyMuPDF: Processing {pdf.page_count} pages")
            
            for page_num, page in enumerate(pdf, 1):
                # Get text blocks with position info
                blocks = page.get_text("dict")
                
                for block in blocks["blocks"]:
                    if "lines" in block:  # Text block
                        for line in block["lines"]:
                            for span in line["spans"]:
                                bbox = span["bbox"]
                                element = TextElement(
                                    text=span["text"],
                                    x0=float(bbox[0]),
                                    y0=float(bbox[1]),
                                    x1=float(bbox[2]),
                                    y1=float(bbox[3]),
                                    width=float(bbox[2] - bbox[0]),
                                    height=float(bbox[3] - bbox[1]),
                                    page_num=page_num,
                                    font_size=float(span["size"]),
                                    font_name=span["font"]
                                )
                                elements.append(element)
                
                # If no text found and OCR is enabled, try OCR
                if not elements and self.use_ocr:
                    print(f"No text found on page {page_num}, attempting OCR...")
                    elements.extend(self._ocr_page(page, page_num))
                    
            pdf.close()
            
        except Exception as e:
            print(f"Error with PyMuPDF: {str(e)}")
            
        return elements
    
    def _ocr_page(self, page, page_num: int) -> List[TextElement]:
        """
        Perform OCR on a page using PyMuPDF's built-in OCR
        
        Args:
            page: PyMuPDF page object
            page_num: Page number
            
        Returns:
            List of TextElement objects from OCR
        """
        elements = []
        
        try:
            # Get page as image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scale for better OCR
            
            # Perform OCR
            text_page = page.get_textpage_ocr(flags=0, language="eng")
            text_dict = text_page.extractDICT()
            
            for block in text_dict["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            bbox = span["bbox"]
                            element = TextElement(
                                text=span["text"],
                                x0=float(bbox[0]),
                                y0=float(bbox[1]),
                                x1=float(bbox[2]),
                                y1=float(bbox[3]),
                                width=float(bbox[2] - bbox[0]),
                                height=float(bbox[3] - bbox[1]),
                                page_num=page_num,
                                font_size=None,  # OCR doesn't provide font info
                                font_name=None
                            )
                            elements.append(element)
                            
        except Exception as e:
            print(f"OCR error on page {page_num}: {str(e)}")
            
        return elements
    
    def extract_text_with_coordinates(self, pdf_path: str, method: str = "auto") -> List[TextElement]:
        """
        Extract text with coordinates from PDF
        
        Args:
            pdf_path: Path to PDF file
            method: Extraction method - "pdfplumber", "pymupdf", or "auto"
            
        Returns:
            List of TextElement objects
        """
        if method == "auto":
            # Try pdfplumber first for structured PDFs
            elements = self.extract_with_pdfplumber(pdf_path)
            
            # If no text found, try PyMuPDF with OCR
            if not elements:
                print("No text found with pdfplumber, trying PyMuPDF...")
                elements = self.extract_with_pymupdf(pdf_path)
                
        elif method == "pdfplumber":
            elements = self.extract_with_pdfplumber(pdf_path)
        elif method == "pymupdf":
            elements = self.extract_with_pymupdf(pdf_path)
        else:
            raise ValueError(f"Unknown method: {method}")
            
        return elements
    
    def get_page_dimensions(self, pdf_path: str) -> Dict[int, Tuple[float, float]]:
        """
        Get dimensions of each page in PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary mapping page number to (width, height)
        """
        dimensions = {}
        
        # Try PyMuPDF first
        if fitz is not None:
            try:
                pdf = fitz.open(pdf_path)
                for page_num, page in enumerate(pdf, 1):
                    rect = page.rect
                    dimensions[page_num] = (rect.width, rect.height)
                pdf.close()
                return dimensions
            except Exception as e:
                print(f"PyMuPDF error getting page dimensions: {str(e)}")
        
        # Fallback to pdfplumber
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    dimensions[page_num] = (page.width, page.height)
        except Exception as e:
            print(f"Error getting page dimensions: {str(e)}")
            
        return dimensions
    
    def normalize_coordinates(self, elements: List[TextElement], 
                            page_dimensions: Dict[int, Tuple[float, float]]) -> List[TextElement]:
        """
        Normalize coordinates to [0, 1] range for consistent feature vectors
        
        Args:
            elements: List of TextElement objects
            page_dimensions: Page dimensions from get_page_dimensions()
            
        Returns:
            List of TextElement objects with normalized coordinates
        """
        normalized = []
        
        for elem in elements:
            if elem.page_num in page_dimensions:
                width, height = page_dimensions[elem.page_num]
                
                # Create normalized copy
                norm_elem = TextElement(
                    text=elem.text,
                    x0=elem.x0 / width,
                    y0=elem.y0 / height,
                    x1=elem.x1 / width,
                    y1=elem.y1 / height,
                    width=elem.width / width,
                    height=elem.height / height,
                    page_num=elem.page_num,
                    font_size=elem.font_size,
                    font_name=elem.font_name
                )
                normalized.append(norm_elem)
            else:
                normalized.append(elem)
                
        return normalized