"""
Set type detection module

Implements steps #9-#10 of the core processing sequence:
9. Identify Set Type OMR (#9)
10. Get Set Type (#10)
"""
import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple

from ..utils.image_utils import (
    get_roi,
    apply_threshold,
    find_contours,
    detect_filled_bubbles
)

# Define the region of interest for set type bubbles
# These coordinates are placeholders and need to be calibrated for the actual form
SET_TYPE_ROI = {"x": 452, "y": 138, "width": 50, "height": 50}

# Define the expected positions of the A, B, C bubbles
SET_TYPE_BUBBLES = {
    "A": {"center_x": 15, "center_y": 15, "radius": 10},
    "B": {"center_x": 15, "center_y": 27, "radius": 10},
    "C": {"center_x": 15, "center_y": 39, "radius": 10}
}


def identify_set_type_region(image: np.ndarray) -> np.ndarray:
    """
    Identify the region containing the set type bubbles (A, B, C)
    
    Args:
        image: Aligned form image
        
    Returns:
        ROI containing the set type bubbles
    """
    # Extract the region of interest for set type
    roi = get_roi(image, SET_TYPE_ROI["x"], SET_TYPE_ROI["y"], 
                 SET_TYPE_ROI["width"], SET_TYPE_ROI["height"])
    
    return roi


def detect_set_type(image: np.ndarray, roi: np.ndarray = None) -> str:
    """
    Detect which set type (A, B, or C) is selected
    
    Args:
        image: Aligned form image
        roi: Optional pre-extracted ROI for set type
        
    Returns:
        Detected set type ('A', 'B', 'C', or 'Unknown')
    """
    if roi is None:
        roi = identify_set_type_region(image)
    
    # Convert to grayscale if needed
    if len(roi.shape) == 3:
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    else:
        gray_roi = roi.copy()
    
    # Apply threshold to highlight the bubbles
    thresh_roi = apply_threshold(gray_roi, method='adaptive')
    
    # Find all contours in the thresholded image
    contours = find_contours(thresh_roi, min_area=50, max_area=300)
    
    # If we found the expected number of bubbles
    if len(contours) >= 3:
        # Detect which bubbles are filled
        filled_bubbles = detect_filled_bubbles(gray_roi, contours, threshold_percentage=0.5)
        
        # Check if we have exactly one filled bubble
        if len(filled_bubbles) == 1:
            # Determine which bubble is filled (A, B, or C)
            filled_contour = filled_bubbles[0]
            M = cv2.moments(filled_contour)
            
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                # Check if the center is close to the expected position of A, B, or C
                if abs(cx - SET_TYPE_BUBBLES["A"]["center_x"]) < 10 and abs(cy - SET_TYPE_BUBBLES["A"]["center_y"]) < 10:
                    return "A"
                elif abs(cx - SET_TYPE_BUBBLES["B"]["center_x"]) < 10 and abs(cy - SET_TYPE_BUBBLES["B"]["center_y"]) < 10:
                    return "B"
                elif abs(cx - SET_TYPE_BUBBLES["C"]["center_x"]) < 10 and abs(cy - SET_TYPE_BUBBLES["C"]["center_y"]) < 10:
                    return "C"
    
    # If we couldn't determine the set type
    return "Unknown"


def process_set_type(image: np.ndarray) -> Dict[str, any]:
    """
    Process the set type detection
    
    Args:
        image: Aligned form image
        
    Returns:
        Dictionary with the detected set type and other metadata
    """
    # 9. Identify Set Type OMR
    set_type_roi = identify_set_type_region(image)
    
    # 10. Get Set Type
    set_type = detect_set_type(image, set_type_roi)
    
    return {
        "set_type": set_type,
        "roi": set_type_roi,
        "coordinates": SET_TYPE_ROI
    }
