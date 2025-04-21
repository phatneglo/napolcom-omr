"""
Personal information extraction module

Implements steps #3-#8 of the core processing sequence:
3. Extract Booklet Number (#3)
4. Extract Date of Exam (#4)
5. Extract Date of Birth (#5)
6. Extract Surname (#6)
7. Extract First Name (#7)
8. Extract Middle Name (#8)
"""
import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple

from ..utils.image_utils import (
    remove_grid_lines,
    get_roi,
    apply_threshold
)

# Define regions of interest for different fields
# These coordinates are placeholders and need to be calibrated for the actual form
ROI_COORDINATES = {
    "booklet_number": {"x": 207, "y": 143, "width": 285, "height": 30},
    "date_of_exam": {"x": 207, "y": 166, "width": 285, "height": 30},
    "date_of_birth": {"x": 207, "y": 188, "width": 285, "height": 30},
    "surname": {"x": 40, "y": 220, "width": 540, "height": 30},
    "first_name": {"x": 40, "y": 261, "width": 540, "height": 30},
    "middle_name": {"x": 40, "y": 303, "width": 540, "height": 30}
}


def extract_booklet_number(image: np.ndarray) -> Dict[str, any]:
    """
    Extract the booklet number from the form
    
    Args:
        image: Aligned form image
        
    Returns:
        Dictionary with the extracted booklet number region and other metadata
    """
    # Get the ROI for the booklet number
    roi_coords = ROI_COORDINATES["booklet_number"]
    roi = get_roi(image, roi_coords["x"], roi_coords["y"], 
                 roi_coords["width"], roi_coords["height"])
    
    # Remove grid lines to isolate the handwritten/filled content
    cleaned_roi = remove_grid_lines(roi)
    
    return {
        "field_name": "booklet_number",
        "roi": roi,
        "cleaned_roi": cleaned_roi,
        "coordinates": roi_coords
    }


def extract_date_of_exam(image: np.ndarray) -> Dict[str, any]:
    """
    Extract the date of exam from the form
    
    Args:
        image: Aligned form image
        
    Returns:
        Dictionary with the extracted date of exam region and other metadata
    """
    # Get the ROI for the date of exam
    roi_coords = ROI_COORDINATES["date_of_exam"]
    roi = get_roi(image, roi_coords["x"], roi_coords["y"], 
                 roi_coords["width"], roi_coords["height"])
    
    # Remove grid lines to isolate the handwritten/filled content
    cleaned_roi = remove_grid_lines(roi)
    
    return {
        "field_name": "date_of_exam",
        "roi": roi,
        "cleaned_roi": cleaned_roi,
        "coordinates": roi_coords
    }


def extract_date_of_birth(image: np.ndarray) -> Dict[str, any]:
    """
    Extract the date of birth from the form
    
    Args:
        image: Aligned form image
        
    Returns:
        Dictionary with the extracted date of birth region and other metadata
    """
    # Get the ROI for the date of birth
    roi_coords = ROI_COORDINATES["date_of_birth"]
    roi = get_roi(image, roi_coords["x"], roi_coords["y"], 
                 roi_coords["width"], roi_coords["height"])
    
    # Remove grid lines to isolate the handwritten/filled content
    cleaned_roi = remove_grid_lines(roi)
    
    return {
        "field_name": "date_of_birth",
        "roi": roi,
        "cleaned_roi": cleaned_roi,
        "coordinates": roi_coords
    }


def extract_surname(image: np.ndarray) -> Dict[str, any]:
    """
    Extract the surname from the form
    
    Args:
        image: Aligned form image
        
    Returns:
        Dictionary with the extracted surname region and other metadata
    """
    # Get the ROI for the surname
    roi_coords = ROI_COORDINATES["surname"]
    roi = get_roi(image, roi_coords["x"], roi_coords["y"], 
                 roi_coords["width"], roi_coords["height"])
    
    # Remove grid lines to isolate the handwritten/filled content
    cleaned_roi = remove_grid_lines(roi)
    
    return {
        "field_name": "surname",
        "roi": roi,
        "cleaned_roi": cleaned_roi,
        "coordinates": roi_coords
    }


def extract_first_name(image: np.ndarray) -> Dict[str, any]:
    """
    Extract the first name from the form
    
    Args:
        image: Aligned form image
        
    Returns:
        Dictionary with the extracted first name region and other metadata
    """
    # Get the ROI for the first name
    roi_coords = ROI_COORDINATES["first_name"]
    roi = get_roi(image, roi_coords["x"], roi_coords["y"], 
                 roi_coords["width"], roi_coords["height"])
    
    # Remove grid lines to isolate the handwritten/filled content
    cleaned_roi = remove_grid_lines(roi)
    
    return {
        "field_name": "first_name",
        "roi": roi,
        "cleaned_roi": cleaned_roi,
        "coordinates": roi_coords
    }


def extract_middle_name(image: np.ndarray) -> Dict[str, any]:
    """
    Extract the middle name from the form
    
    Args:
        image: Aligned form image
        
    Returns:
        Dictionary with the extracted middle name region and other metadata
    """
    # Get the ROI for the middle name
    roi_coords = ROI_COORDINATES["middle_name"]
    roi = get_roi(image, roi_coords["x"], roi_coords["y"], 
                 roi_coords["width"], roi_coords["height"])
    
    # Remove grid lines to isolate the handwritten/filled content
    cleaned_roi = remove_grid_lines(roi)
    
    return {
        "field_name": "middle_name",
        "roi": roi,
        "cleaned_roi": cleaned_roi,
        "coordinates": roi_coords
    }


def extract_all_personal_info(image: np.ndarray) -> Dict[str, Dict[str, any]]:
    """
    Extract all personal information from the form
    
    Args:
        image: Aligned form image
        
    Returns:
        Dictionary with all extracted personal information fields
    """
    return {
        "booklet_number": extract_booklet_number(image),
        "date_of_exam": extract_date_of_exam(image),
        "date_of_birth": extract_date_of_birth(image),
        "surname": extract_surname(image),
        "first_name": extract_first_name(image),
        "middle_name": extract_middle_name(image)
    }
