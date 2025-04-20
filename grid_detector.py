import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

def detect_grid(img, debug=False):
    """
    Detect grid lines in the image to help with alignment.
    Returns a corrected image aligned to the grid.
    """
    height, width = img.shape[:2]
    debug_img = None
    
    if debug:
        if len(img.shape) == 2:
            debug_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        else:
            debug_img = img.copy()
    
    # Apply edge detection
    edges = cv2.Canny(img, 50, 150, apertureSize=3)
    
    # Use Hough Line Transform to detect lines
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)
    
    if lines is None or len(lines) < 10:
        logger.warning("Not enough lines detected for grid analysis")
        return img
    
    # Separate horizontal and vertical lines
    horizontal_lines = []
    vertical_lines = []
    
    for line in lines:
        x1, y1, x2, y2 = line[0]
        
        # Calculate line angle
        angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
        
        # Categorize as horizontal or vertical (with some tolerance)
        if angle < 20 or angle > 160:
            horizontal_lines.append(line[0])
            if debug_img is not None:
                cv2.line(debug_img, (x1, y1), (x2, y2), (0, 255, 0), 1)
        elif 70 < angle < 110:
            vertical_lines.append(line[0])
            if debug_img is not None:
                cv2.line(debug_img, (x1, y1), (x2, y2), (0, 0, 255), 1)
    
    logger.info(f"Detected {len(horizontal_lines)} horizontal and {len(vertical_lines)} vertical lines")
    
    # If not enough lines detected, return original image
    if len(horizontal_lines) < 5 or len(vertical_lines) < 5:
        logger.warning("Not enough horizontal or vertical lines for grid analysis")
        return img
    
    # Find the predominant angle for horizontal lines
    horizontal_angles = []
    for x1, y1, x2, y2 in horizontal_lines:
        angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
        horizontal_angles.append(angle)
    
    # Calculate the median angle (more robust than mean)
    horizontal_angle = np.median(horizontal_angles)
    
    # Find the predominant angle for vertical lines
    vertical_angles = []
    for x1, y1, x2, y2 in vertical_lines:
        angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
        # Normalize angle to be around 90 degrees
        if angle < 0:
            angle += 180
        vertical_angles.append(angle)
    
    vertical_angle = np.median(vertical_angles)
    
    # Calculate the rotation angle (difference from horizontal/vertical)
    if abs(horizontal_angle) < abs(vertical_angle - 90):
        rotation_angle = horizontal_angle
    else:
        rotation_angle = vertical_angle - 90
    
    logger.info(f"Calculated rotation angle: {rotation_angle} degrees")
    
    # If the angle is too large, it's likely a false detection
    if abs(rotation_angle) > 20:
        logger.warning(f"Rotation angle {rotation_angle} too large, limiting to ±20 degrees")
        rotation_angle = np.sign(rotation_angle) * 20
    
    # Rotate the image to correct the skew
    center = (width // 2, height // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, rotation_angle, 1.0)
    rotated_img = cv2.warpAffine(img, rotation_matrix, (width, height), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    if debug and debug_img is not None:
        cv2.imwrite('grid_detection_debug.jpg', debug_img)
    
    return rotated_img
