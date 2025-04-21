"""
Utility functions for image processing
"""
import cv2
import numpy as np
import imutils
from skimage import exposure
from typing import Tuple, List, Dict, Any, Optional


def load_image(image_path: str) -> np.ndarray:
    """
    Load an image from the specified path
    
    Args:
        image_path: Path to the image file
        
    Returns:
        The loaded image as a numpy array
    """
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image from {image_path}")
    return image


def resize_image(image: np.ndarray, width: int = 600) -> np.ndarray:
    """
    Resize image while maintaining aspect ratio
    
    Args:
        image: Input image
        width: Target width
        
    Returns:
        Resized image
    """
    return imutils.resize(image, width=width)


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Enhance image contrast using adaptive histogram equalization
    
    Args:
        image: Input image
        
    Returns:
        Contrast-enhanced image
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    return enhanced


def apply_threshold(image: np.ndarray, method: str = 'adaptive') -> np.ndarray:
    """
    Apply thresholding to an image
    
    Args:
        image: Input image
        method: Thresholding method ('otsu', 'adaptive', 'binary')
        
    Returns:
        Thresholded image
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    if method == 'otsu':
        # Otsu's thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    elif method == 'adaptive':
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY_INV, 11, 2)
    else:  # binary
        # Simple binary thresholding
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    
    return thresh


def find_contours(image: np.ndarray, min_area: int = 100, max_area: int = 10000) -> List[np.ndarray]:
    """
    Find contours in an image and filter by area
    
    Args:
        image: Input image (should be binary/thresholded)
        min_area: Minimum contour area to keep
        max_area: Maximum contour area to keep
        
    Returns:
        List of contours
    """
    # Find all contours
    contours = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    
    # Filter by area
    filtered_contours = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if min_area <= area <= max_area:
            filtered_contours.append(contour)
    
    return filtered_contours


def detect_filled_bubbles(image: np.ndarray, contours: List[np.ndarray], 
                          threshold_percentage: float = 0.5) -> List[np.ndarray]:
    """
    Detect which bubbles are filled based on the fill percentage
    
    Args:
        image: Original grayscale image
        contours: List of contours representing bubbles
        threshold_percentage: Minimum fill percentage to consider a bubble filled
        
    Returns:
        List of contours that are filled
    """
    filled_bubbles = []
    
    for contour in contours:
        # Create a mask for this contour
        mask = np.zeros(image.shape, dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, -1)
        
        # Calculate the mean pixel value inside the contour
        # Lower values indicate darker filling (more filled)
        mean_value = cv2.mean(image, mask=mask)[0]
        
        # Convert to a fill percentage (0-255 inverted to 0-1)
        fill_percentage = 1 - (mean_value / 255.0)
        
        # If the fill percentage is above the threshold, consider it filled
        if fill_percentage >= threshold_percentage:
            filled_bubbles.append(contour)
    
    return filled_bubbles


def draw_contours(image: np.ndarray, contours: List[np.ndarray], 
                  color: Tuple[int, int, int] = (0, 255, 0), 
                  thickness: int = 2) -> np.ndarray:
    """
    Draw contours on an image
    
    Args:
        image: Input image
        contours: List of contours to draw
        color: Color to use for drawing (B, G, R)
        thickness: Line thickness
        
    Returns:
        Image with contours drawn
    """
    result = image.copy()
    cv2.drawContours(result, contours, -1, color, thickness)
    return result


def remove_grid_lines(image: np.ndarray) -> np.ndarray:
    """
    Remove grid lines from an image
    
    Args:
        image: Input image (grayscale)
        
    Returns:
        Image with grid lines removed
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Apply threshold
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)
    
    # Create kernels for detecting horizontal and vertical lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
    
    # Detect horizontal lines
    horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
    
    # Detect vertical lines
    vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=1)
    
    # Combine horizontal and vertical lines
    grid_lines = cv2.add(horizontal_lines, vertical_lines)
    
    # Remove the grid lines from the thresholded image
    no_grid = cv2.subtract(thresh, grid_lines)
    
    # Clean up the result with a closing operation
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    cleaned = cv2.morphologyEx(no_grid, cv2.MORPH_CLOSE, kernel, iterations=1)
    
    return cleaned


def get_roi(image: np.ndarray, x: int, y: int, width: int, height: int) -> np.ndarray:
    """
    Extract a region of interest (ROI) from an image
    
    Args:
        image: Input image
        x, y: Top-left coordinates of ROI
        width, height: Dimensions of ROI
        
    Returns:
        Extracted ROI
    """
    return image[y:y+height, x:x+width]


def perspective_transform(image: np.ndarray, src_points: np.ndarray, 
                          dst_points: np.ndarray) -> np.ndarray:
    """
    Apply perspective transformation to an image
    
    Args:
        image: Input image
        src_points: Source points (4 points in the original image)
        dst_points: Destination points (where the source points should map to)
        
    Returns:
        Transformed image
    """
    # Get the perspective transform matrix
    M = cv2.getPerspectiveTransform(src_points, dst_points)
    
    # Apply the perspective transformation
    height, width = image.shape[:2]
    warped = cv2.warpPerspective(image, M, (width, height))
    
    return warped


def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    """
    Rotate an image by the specified angle
    
    Args:
        image: Input image
        angle: Rotation angle in degrees (positive is counterclockwise)
        
    Returns:
        Rotated image
    """
    return imutils.rotate_bound(image, angle)


def show_image(image: np.ndarray, window_name: str = "Image", wait: bool = True) -> None:
    """
    Display an image using OpenCV
    
    Args:
        image: Image to display
        window_name: Name of the display window
        wait: Whether to wait for a key press before continuing
    """
    cv2.imshow(window_name, image)
    if wait:
        cv2.waitKey(0)
        cv2.destroyAllWindows()
