import cv2
import numpy as np
import json
import os
from typing import Dict, Tuple, List, Union, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
REFERENCE_WIDTH = 785
REFERENCE_HEIGHT = 1024
PIXEL_THR = 0.50  # Threshold for considering a bubble filled

class SimpleOMRProcessor:
    """A simplified version of the OMR processor that doesn't require Tesseract OCR."""
    
    def __init__(self, template_path: str = None):
        """Initialize the OMR processor with a template."""
        self.template = None
        if template_path and os.path.exists(template_path):
            with open(template_path, 'r') as f:
                self.template = json.load(f)
            logger.info(f"Loaded template from {template_path}")
        else:
            logger.warning("No template provided or file not found")
    
    def preprocess(self, img: np.ndarray) -> np.ndarray:
        """
        Preprocess the image for better recognition:
        - Convert to grayscale if necessary
        - Apply blur
        - Apply adaptive thresholding
        - Binarize the image
        """
        # Convert to grayscale if the image is in color
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
            
        # Apply blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        return thresh
    
    def align(self, img: np.ndarray) -> np.ndarray:
        """
        Align the image:
        - Detect the outer contour
        - Apply perspective transform to get canonical 785×1024 canvas
        """
        # Find contours
        contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find the largest contour which should be the examination form
        max_area = 0
        max_contour = None
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > max_area:
                max_area = area
                max_contour = contour
        
        if max_contour is None:
            raise ValueError("No form contour detected")
            
        # Approximate the contour to a polygon
        peri = cv2.arcLength(max_contour, True)
        approx = cv2.approxPolyDP(max_contour, 0.02 * peri, True)
        
        # We need exactly 4 corners for perspective transform
        if len(approx) != 4:
            # If not exactly 4 points, try to find the 4 extreme points
            rect = cv2.minAreaRect(max_contour)
            box = cv2.boxPoints(rect)
            approx = np.int0(box)
            
        # Order the points: top-left, top-right, bottom-right, bottom-left
        approx = self._order_points(approx)
        
        # Get perspective transform
        dst_pts = np.array([
            [0, 0],
            [REFERENCE_WIDTH, 0],
            [REFERENCE_WIDTH, REFERENCE_HEIGHT],
            [0, REFERENCE_HEIGHT]
        ], dtype=np.float32)
        
        src_pts = np.array(approx, dtype=np.float32)
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        
        # Apply perspective transform
        warped = cv2.warpPerspective(img, M, (REFERENCE_WIDTH, REFERENCE_HEIGHT))
        
        return warped
    
    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """Order points in top-left, top-right, bottom-right, bottom-left order."""
        pts = pts.reshape(4, 2)
        rect = np.zeros((4, 2), dtype=np.float32)
        
        # Sum of coordinates: top-left has the smallest sum
        # Difference of coordinates: bottom-left has the smallest difference
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1)
        
        rect[0] = pts[np.argmin(s)]    # Top-left
        rect[2] = pts[np.argmax(s)]    # Bottom-right
        rect[1] = pts[np.argmin(diff)] # Top-right
        rect[3] = pts[np.argmax(diff)] # Bottom-left
        
        return rect
    
    def extract_bubbles(self, img: np.ndarray) -> Dict[str, str]:
        """
        Extract bubbles:
        - For each question, check all bubbles
        - Mark the first bubble with fill ratio >= threshold as selected
        """
        if self.template is None:
            raise ValueError("Template is required for bubble extraction")
            
        answers = {}
        
        for q_num, options in self.template["bubbles"].items():
            for opt_num, coords in options.items():
                x, y, w, h = coords
                roi = img[y:y+h, x:x+w]
                
                # Calculate fill ratio
                filled_pixels = cv2.countNonZero(roi)
                total_pixels = roi.shape[0] * roi.shape[1]
                fill_ratio = filled_pixels / total_pixels
                
                # If the fill ratio is greater than threshold, mark this option as selected
                if fill_ratio >= PIXEL_THR:
                    answers[q_num] = opt_num
                    break  # Only take the first filled bubble
        
        return answers
    
    def extract_set_type(self, img: np.ndarray) -> str:
        """
        Extract the set type (A/B/C) from the form:
        - Check the set type bubbles region
        - Return the selected option (A, B, or C)
        """
        if self.template is None or "set_type_bubbles" not in self.template:
            raise ValueError("Template with set_type_bubbles is required")
            
        set_types = ["A", "B", "C"]
        selected_set = None
        
        for i, set_type in enumerate(set_types):
            coords = self.template["set_type_bubbles"][set_type]
            x, y, w, h = coords
            roi = img[y:y+h, x:x+w]
            
            # Calculate fill ratio
            filled_pixels = cv2.countNonZero(roi)
            total_pixels = roi.shape[0] * roi.shape[1]
            fill_ratio = filled_pixels / total_pixels
            
            if fill_ratio >= PIXEL_THR:
                selected_set = set_type
                break
                
        return selected_set or "Unknown"
    
    def process_sheet(self, img_data: bytes) -> Dict[str, Union[str, int]]:
        """
        Process a complete sheet focusing only on bubbles:
        - Convert bytes to numpy array
        - Preprocess the image
        - Align the sheet
        - Extract bubble answers
        """
        # Convert bytes to numpy array
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Process the image
        processed = self.preprocess(img)
        aligned = self.align(processed)
        
        # Extract data - no text extraction, just bubbles
        bubble_data = self.extract_bubbles(aligned)
        set_type = self.extract_set_type(aligned)
        
        # Combine results
        result = {
            "answers": bubble_data,
            "set_type": set_type
        }
        
        return result, {
            "original": img,
            "processed": processed,
            "aligned": aligned
        }
