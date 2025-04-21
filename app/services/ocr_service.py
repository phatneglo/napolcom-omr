"""
OCR service for text extraction from form fields
"""
import os
import cv2
import numpy as np
import pytesseract
from typing import Dict, Any, Optional

from app.utils.image_utils import remove_grid_lines


async def extract_text_from_image(image_path: str, roi: Dict[str, int]) -> str:
    """
    Extract text from an image ROI using OCR
    
    Args:
        image_path: Path to the image file
        roi: Region of interest {x, y, width, height}
        
    Returns:
        Extracted text
    """
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image from {image_path}")
    
    # Extract the ROI
    x, y, width, height = roi["x"], roi["y"], roi["width"], roi["height"]
    roi_image = image[y:y+height, x:x+width]
    
    # Preprocess the ROI
    # 1. Remove grid lines
    no_grid = remove_grid_lines(roi_image)
    
    # 2. Apply thresholding to improve OCR
    _, binary = cv2.threshold(no_grid, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    # 3. Optional: Apply morphological operations to enhance characters
    kernel = np.ones((2, 2), np.uint8)
    enhanced = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    # Perform OCR
    text = pytesseract.image_to_string(enhanced, config='--psm 6')
    
    # Clean up the text
    text = text.strip()
    
    return text


async def extract_personal_info(
    image_path: str, rois: Dict[str, Dict[str, int]]
) -> Dict[str, str]:
    """
    Extract personal information from a form image
    
    Args:
        image_path: Path to the form image
        rois: Dictionary of ROIs for each field
        
    Returns:
        Dictionary of extracted fields
    """
    result = {}
    
    # Process each field
    for field_name, roi in rois.items():
        try:
            text = await extract_text_from_image(image_path, roi)
            result[field_name] = text
        except Exception as e:
            result[field_name] = f"Error: {str(e)}"
    
    return result


async def validate_field(field_name: str, value: str) -> bool:
    """
    Validate an extracted field
    
    Args:
        field_name: Name of the field
        value: Extracted value
        
    Returns:
        True if valid, False otherwise
    """
    if not value:
        return False
    
    # Field-specific validation
    if field_name == "booklet_number":
        # Should be 6 digits
        return value.isdigit() and len(value) == 6
    
    elif field_name in ["date_of_exam", "date_of_birth"]:
        # Should be in mm/dd/yyyy format
        parts = value.split("/")
        if len(parts) != 3:
            return False
        
        mm, dd, yyyy = parts
        try:
            mm = int(mm)
            dd = int(dd)
            yyyy = int(yyyy)
            
            # Basic validation
            if not (1 <= mm <= 12 and 1 <= dd <= 31 and 1900 <= yyyy <= 2100):
                return False
                
        except ValueError:
            return False
            
        return True
    
    elif field_name in ["surname", "first_name", "middle_name"]:
        # Should contain only letters and spaces
        return all(c.isalpha() or c.isspace() for c in value)
    
    # Default: accept any non-empty value
    return True
