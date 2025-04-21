"""
Application number detection module

Implements step #11 of the core processing sequence:
11. Application Number Processing - Extract all 11 vertical columns (digits 1-0)
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

# Define the region of interest for application number
# These coordinates are placeholders and need to be calibrated for the actual form
APP_NUMBER_ROI = {"x": 690, "y": 177, "width": 125, "height": 183}

# Number of columns and rows in the application number grid
NUM_COLUMNS = 11
NUM_ROWS = 10  # Digits 0-9


def identify_application_number_region(image: np.ndarray) -> np.ndarray:
    """
    Identify the region containing the application number bubbles
    
    Args:
        image: Aligned form image
        
    Returns:
        ROI containing the application number bubbles
    """
    # Extract the region of interest for application number
    roi = get_roi(image, APP_NUMBER_ROI["x"], APP_NUMBER_ROI["y"], 
                 APP_NUMBER_ROI["width"], APP_NUMBER_ROI["height"])
    
    return roi


def detect_application_number(image: np.ndarray, roi: np.ndarray = None) -> str:
    """
    Detect the application number from the form
    
    Args:
        image: Aligned form image
        roi: Optional pre-extracted ROI for application number
        
    Returns:
        Detected application number as a string
    """
    if roi is None:
        roi = identify_application_number_region(image)
    
    # Convert to grayscale if needed
    if len(roi.shape) == 3:
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    else:
        gray_roi = roi.copy()
    
    # Apply threshold to highlight the bubbles
    thresh_roi = apply_threshold(gray_roi, method='adaptive')
    
    # Calculate grid cell dimensions
    cell_width = roi.shape[1] // NUM_COLUMNS
    cell_height = roi.shape[0] // NUM_ROWS
    
    # Initialize the application number with empty digits
    app_number = [""] * NUM_COLUMNS
    
    # Process each column
    for col in range(NUM_COLUMNS):
        # Extract the column ROI
        col_x = col * cell_width
        col_roi = thresh_roi[:, col_x:col_x + cell_width]
        
        # Find contours in this column
        contours = find_contours(col_roi, min_area=20, max_area=200)
        
        # If contours were found
        if contours:
            # Detect filled bubbles
            filled_bubbles = detect_filled_bubbles(gray_roi[:, col_x:col_x + cell_width], 
                                                 contours, threshold_percentage=0.5)
            
            # If exactly one bubble is filled in this column
            if len(filled_bubbles) == 1:
                # Determine which row (digit) is filled
                filled_contour = filled_bubbles[0]
                M = cv2.moments(filled_contour)
                
                if M["m00"] != 0:
                    cy = int(M["m01"] / M["m00"])
                    row = cy // cell_height
                    
                    # Map row to digit (0-9)
                    # Row 0 corresponds to digit 1, row 1 to digit 2, etc.
                    # Row 9 corresponds to digit 0
                    digit = (row + 1) % 10
                    app_number[col] = str(digit)
            
            # If multiple or no bubbles are filled, leave it blank
            # (this could be improved with more sophisticated detection)
    
    # Combine the digits into a single string
    # Replace empty digits with placeholders
    app_number_str = "".join([digit if digit else "X" for digit in app_number])
    
    return app_number_str


def process_application_number(image: np.ndarray) -> Dict[str, any]:
    """
    Process the application number detection
    
    Args:
        image: Aligned form image
        
    Returns:
        Dictionary with the detected application number and other metadata
    """
    # Extract the application number region
    app_number_roi = identify_application_number_region(image)
    
    # Detect the application number
    app_number = detect_application_number(image, app_number_roi)
    
    return {
        "application_number": app_number,
        "roi": app_number_roi,
        "coordinates": APP_NUMBER_ROI
    }
