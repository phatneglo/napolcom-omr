"""
Form alignment module for OMR processing

Implements steps #1 and #2 of the core processing sequence:
1. Get the Main Mark (#1) - Establish the anchor point with 3 lines for alignment
2. Auto Canvas (#2) - Capture canvas size and ensure proper orientation
"""
import cv2
import numpy as np
import imutils
from typing import Dict, Tuple, List, Optional

from ..utils.image_utils import (
    enhance_contrast, 
    apply_threshold,
    find_contours,
    perspective_transform
)

def detect_main_mark(image: np.ndarray) -> Optional[np.ndarray]:
    """
    Detect the main mark (anchor point with 3 lines) in the form
    
    Args:
        image: Input image
        
    Returns:
        Numpy array of the main mark coordinates or None if not found
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Enhance contrast and apply threshold
    enhanced = enhance_contrast(gray)
    thresh = apply_threshold(enhanced, method='adaptive')
    
    # Find contours
    contours = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    
    # Sort contours by area (largest first)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    # Check the top contours to find the main mark with 3 lines
    for contour in contours[:50]:  # Check top 50 contours
        # Approximate the contour
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        
        # Check if it has the right number of vertices
        # This is a simplified check - in a real implementation,
        # we'd need more sophisticated detection based on the exact form layout
        if len(approx) == 4:  # Assuming the main mark is rectangular
            # Additional checks can be added here to verify this is the correct mark
            # For now, we'll return the first good candidate
            return approx
    
    # If no suitable contour found
    return None


def align_form(image: np.ndarray, main_mark: np.ndarray) -> Dict[str, any]:
    """
    Align the form based on the detected main mark
    
    Args:
        image: Input image
        main_mark: Coordinates of the main mark
        
    Returns:
        Dict containing:
            - aligned_image: The aligned image
            - transform_matrix: The transformation matrix used
    """
    # Extract the corners of the main mark
    if main_mark is None:
        raise ValueError("Main mark not detected. Cannot align form.")
    
    # Get image dimensions
    height, width = image.shape[:2]
    
    # Convert main_mark to the right format if needed
    if len(main_mark) == 4:
        # Assuming it's a rectangle with 4 corners
        marker_points = np.array([p[0] for p in main_mark], dtype=np.float32)
    else:
        marker_points = main_mark.astype(np.float32)
    
    # Define target points (where the corners should be in the aligned image)
    # This depends on the specific form layout
    target_points = np.array([
        [width * 0.1, height * 0.1],  # Top-left
        [width * 0.9, height * 0.1],  # Top-right
        [width * 0.9, height * 0.9],  # Bottom-right
        [width * 0.1, height * 0.9]   # Bottom-left
    ], dtype=np.float32)
    
    # Make sure points are in the correct order (top-left, top-right, bottom-right, bottom-left)
    # This is a simplified approach - real implementation would need proper ordering
    # based on the specific form layout
    marker_points = order_points(marker_points)
    
    # Get the perspective transform matrix
    matrix = cv2.getPerspectiveTransform(marker_points, target_points)
    
    # Apply the perspective transformation
    aligned = cv2.warpPerspective(image, matrix, (width, height))
    
    return {
        "aligned_image": aligned,
        "transform_matrix": matrix
    }


def order_points(pts: np.ndarray) -> np.ndarray:
    """
    Order points in top-left, top-right, bottom-right, bottom-left order
    
    Args:
        pts: Input points
        
    Returns:
        Ordered points
    """
    # Initialize a list of coordinates that will be ordered
    rect = np.zeros((4, 2), dtype="float32")
    
    # The top-left point will have the smallest sum, whereas
    # the bottom-right point will have the largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    # Now, compute the difference between the points, the
    # top-right point will have the smallest difference,
    # whereas the bottom-left will have the largest difference
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    # Return the ordered coordinates
    return rect


def process_form_alignment(image: np.ndarray) -> Dict[str, any]:
    """
    Process form alignment following steps #1 and #2
    
    Args:
        image: Input image
        
    Returns:
        Dict containing:
            - aligned_image: The aligned image
            - main_mark: The detected main mark
            - transform_matrix: The transformation matrix used
    """
    # 1. Get the main mark (#1)
    main_mark = detect_main_mark(image)
    
    if main_mark is None:
        raise ValueError("Main mark not detected. Cannot proceed with processing.")
    
    # 2. Auto canvas (#2)
    alignment_result = align_form(image, main_mark)
    
    return {
        "aligned_image": alignment_result["aligned_image"],
        "main_mark": main_mark,
        "transform_matrix": alignment_result["transform_matrix"]
    }
