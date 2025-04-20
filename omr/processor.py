import cv2
import numpy as np
import pytesseract
import os
import sys

# Set Tesseract path - modify this to match your installation path
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
import json
import os
from typing import Dict, Tuple, List, Union, Optional
import logging

# Add parent directory to path to import grid_detector
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from grid_detector import detect_grid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
REFERENCE_WIDTH = 785
REFERENCE_HEIGHT = 1024
PIXEL_THR = 0.50  # Threshold for considering a bubble filled

class OMRProcessor:
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
        - Normalize brightness and contrast
        - Apply blur to reduce noise
        - Apply adaptive thresholding
        - Clean up with morphological operations
        """
        # Convert to grayscale if the image is in color
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
            
        # Resize if the image is too large (helps with performance and consistency)
        height, width = gray.shape[:2]
        max_dimension = 2000  # Limit maximum dimension
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_AREA)
            logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
        
        # Normalize brightness and contrast
        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
        
        # Apply bilateral filter to reduce noise while preserving edges
        filtered = cv2.bilateralFilter(gray, 11, 17, 17)
        
        # Apply Gaussian blur to further reduce noise
        blurred = cv2.GaussianBlur(filtered, (5, 5), 0)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Clean up with morphological operations
        kernel = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        return cleaned
    
    def align(self, img: np.ndarray) -> np.ndarray:
        """
        Align the image:
        - Detect the outer contour
        - Apply perspective transform to get canonical 785×1024 canvas
        """
        # Make a copy of the image for drawing debugging info
        debug_img = None
        if len(img.shape) == 2:  # If grayscale, convert to BGR for debugging
            debug_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        else:
            debug_img = img.copy()
        
        # Image size
        img_h, img_w = img.shape[:2]
        
        # Apply morphological operations to clean up the image before contour detection
        kernel = np.ones((5, 5), np.uint8)
        cleaned = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
        
        # Find contours - try with different retrieval modes if needed
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            # If no external contours found, try with all contours
            contours, _ = cv2.findContours(cleaned, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            
        if not contours:
            # Last resort - try with the original image
            contours, _ = cv2.findContours(img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area to avoid noise
        min_area = 0.10 * img_w * img_h  # Must be at least 10% of the image
        valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
        
        if not valid_contours:
            # If still no valid contours, use boundary of the whole image
            logger.warning("No form contour detected, using image boundary")
            # Create a contour that covers the entire image
            boundary_points = np.array([[0, 0], [img_w-1, 0], [img_w-1, img_h-1], [0, img_h-1]])
            max_contour = boundary_points.reshape(-1, 1, 2).astype(np.int32)
        else:
            # Find the largest contour which should be the examination form
            max_contour = max(valid_contours, key=cv2.contourArea)
            
        # Draw the detected contour for debugging
        cv2.drawContours(debug_img, [max_contour], -1, (0, 255, 0), 3)
        
        # Approximate the contour to a polygon
        peri = cv2.arcLength(max_contour, True)
        
        # Try different epsilon values to get 4 points
        epsilon_values = [0.02, 0.03, 0.05, 0.01, 0.005]  # Different approximation levels
        
        for epsilon in epsilon_values:
            approx = cv2.approxPolyDP(max_contour, epsilon * peri, True)
            if len(approx) == 4:
                break
        
        # If still not exactly 4 points, use the minimum area rectangle
        if len(approx) != 4:
            logger.warning(f"Could not find 4 corners (found {len(approx)}), using minimum area rectangle")
            rect = cv2.minAreaRect(max_contour)
            box = cv2.boxPoints(rect)
            approx = np.int0(box)
        
        # Draw the corner points for debugging
        for point in approx:
            cv2.circle(debug_img, tuple(point.ravel()), 10, (0, 0, 255), -1)
        
        # Order the points: top-left, top-right, bottom-right, bottom-left
        approx = self._order_points(approx)
        
        # Add padding to ensure we capture the entire form
        padding = 0  # No padding for now, but can be adjusted if needed
        
        # Get perspective transform
        dst_pts = np.array([
            [0, 0],
            [REFERENCE_WIDTH, 0],
            [REFERENCE_WIDTH, REFERENCE_HEIGHT],
            [0, REFERENCE_HEIGHT]
        ], dtype=np.float32)
        
        src_pts = np.array(approx, dtype=np.float32)
        
        # Apply some sanity checks to the source points
        # Check that points form a reasonable quadrilateral
        # Minimum area check
        quad_area = cv2.contourArea(src_pts.reshape(-1, 1, 2))
        if quad_area < 0.1 * img_w * img_h:  # Less than 10% of the image
            logger.warning(f"Quadrilateral area too small: {quad_area}, using image boundary")
            # Use the whole image instead
            src_pts = np.array([[0, 0], [img_w-1, 0], [img_w-1, img_h-1], [0, img_h-1]], dtype=np.float32)
        
        # Compute the perspective transform matrix
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        
        # Apply perspective transform
        warped = cv2.warpPerspective(img, M, (REFERENCE_WIDTH, REFERENCE_HEIGHT))
        
        # Apply grid-based alignment for extra correction
        try:
            grid_aligned = detect_grid(warped, debug=True)
            # If grid detection succeeded, use the grid-aligned image
            if grid_aligned is not None and grid_aligned.shape == warped.shape:
                warped = grid_aligned
                logger.info("Successfully applied grid-based alignment")
        except Exception as e:
            logger.warning(f"Grid alignment failed: {str(e)}")
        
        # Draw a grid on the debug image to verify alignment
        warped_debug = warped.copy()
        for i in range(0, REFERENCE_WIDTH, 100):
            cv2.line(warped_debug, (i, 0), (i, REFERENCE_HEIGHT), 128, 1)
        for i in range(0, REFERENCE_HEIGHT, 100):
            cv2.line(warped_debug, (0, i), (REFERENCE_WIDTH, i), 128, 1)
        
        # Save debug image
        cv2.imwrite('debug_alignment.jpg', warped_debug)
        cv2.imwrite('debug_contours.jpg', debug_img)
        
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
    
    def extract_text(self, img: np.ndarray) -> Dict[str, str]:
        """
        Extract text from header fields using OCR-optimized processing:
        - For each text box in the template, extract the region
        - Apply OCR to get the text
        """
        if self.template is None:
            raise ValueError("Template is required for text extraction")
            
        text_data = {}
        
        # Create a separate copy of the image for text processing
        # For OCR, we want less aggressive thresholding to preserve text details
        gray = img.copy()
        if len(gray.shape) > 2:
            gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
        
        # Denoise and normalize for better OCR
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
        
        # Apply a less aggressive threshold for text - using OTSU which works better for text
        _, ocr_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Debug images for each field
        debug_dir = "text_debug"
        os.makedirs(debug_dir, exist_ok=True)
        
        for field, coords in self.template["text_boxes"].items():
            try:
                x, y, w, h = coords
                
                # Extract ROI for this field
                roi = ocr_img[y:y+h, x:x+w]
                
                # Save the ROI for debugging
                cv2.imwrite(f"{debug_dir}/{field}_roi.jpg", roi)
                
                # For handwritten text, sometimes dilation helps
                kernel = np.ones((2, 2), np.uint8)
                dilated_roi = cv2.dilate(roi, kernel, iterations=1)
                
                # Create a clean border around the text region
                bordered_roi = cv2.copyMakeBorder(dilated_roi, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=0)
                
                # Save the processed ROI for debugging
                cv2.imwrite(f"{debug_dir}/{field}_processed.jpg", bordered_roi)
                
                # Apply OCR with optimized settings
                # PSM 7 = Treat image as a single text line
                text = pytesseract.image_to_string(
                    bordered_roi, 
                    config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ/-'
                ).strip()
                
                # If text extraction fails, try inverting the image
                if not text:
                    inverted_roi = cv2.bitwise_not(bordered_roi)
                    cv2.imwrite(f"{debug_dir}/{field}_inverted.jpg", inverted_roi)
                    
                    text = pytesseract.image_to_string(
                        inverted_roi, 
                        config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ/-'
                    ).strip()
                
                logger.info(f"Field '{field}' extracted text: '{text}'")
                text_data[field] = text
                
            except Exception as e:
                logger.error(f"Error extracting text for field '{field}': {str(e)}")
                text_data[field] = ""
                
        return text_data
    
    def extract_bubbles(self, img: np.ndarray) -> Dict[str, str]:
        """
        Extract bubbles:
        - For each question, check all bubbles
        - Mark the bubble with highest fill ratio as selected if it meets the threshold
        """
        if self.template is None:
            raise ValueError("Template is required for bubble extraction")
            
        answers = {}
        
        # Create a debug image if needed
        debug_img = None
        if len(img.shape) == 2:  # If grayscale, convert to BGR for debugging
            debug_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        else:
            debug_img = img.copy()
        
        for q_num, options in self.template["bubbles"].items():
            max_fill_ratio = 0
            selected_opt = None
            
            # Check all options for this question
            for opt_num, coords in options.items():
                try:
                    x, y, w, h = coords
                    
                    # Ensure coordinates are within image bounds
                    if y < 0 or y + h >= img.shape[0] or x < 0 or x + w >= img.shape[1]:
                        logger.warning(f"Bubble coordinates out of bounds for Q{q_num} option {opt_num}")
                        continue
                    
                    # Extract the region of interest
                    roi = img[y:y+h, x:x+w]
                    
                    # Calculate fill ratio
                    filled_pixels = cv2.countNonZero(roi)
                    total_pixels = roi.shape[0] * roi.shape[1]
                    fill_ratio = filled_pixels / total_pixels
                    
                    # For debugging - draw the bubble and fill ratio
                    color = (0, 0, 255) if fill_ratio >= PIXEL_THR else (0, 255, 0)
                    cv2.rectangle(debug_img, (x, y), (x+w, y+h), color, 1)
                    
                    # Keep track of the option with the highest fill ratio
                    if fill_ratio > max_fill_ratio:
                        max_fill_ratio = fill_ratio
                        selected_opt = opt_num
                        
                except Exception as e:
                    logger.error(f"Error processing bubble Q{q_num} option {opt_num}: {str(e)}")
            
            # If the highest fill ratio meets the threshold, mark it as selected
            if max_fill_ratio >= PIXEL_THR and selected_opt is not None:
                answers[q_num] = selected_opt
                # For debugging - draw the selected bubble
                if q_num in self.template["bubbles"] and selected_opt in self.template["bubbles"][q_num]:
                    x, y, w, h = self.template["bubbles"][q_num][selected_opt]
                    cv2.rectangle(debug_img, (x, y), (x+w, y+h), (255, 0, 0), 2)
        
        # Save debug image if needed
        # cv2.imwrite('debug_bubbles.jpg', debug_img)
        
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
        max_fill_ratio = 0.0
        
        for set_type in set_types:
            if set_type not in self.template["set_type_bubbles"]:
                logger.warning(f"Set type {set_type} not in template")
                continue
                
            coords = self.template["set_type_bubbles"][set_type]
            x, y, w, h = coords
            
            # Check bounds
            if y < 0 or y + h >= img.shape[0] or x < 0 or x + w >= img.shape[1]:
                logger.warning(f"Set type {set_type} coordinates out of bounds")
                continue
            
            # Extract region
            roi = img[y:y+h, x:x+w]
            
            # Calculate fill ratio
            filled_pixels = cv2.countNonZero(roi)
            total_pixels = roi.shape[0] * roi.shape[1]
            fill_ratio = float(filled_pixels) / float(total_pixels) if total_pixels > 0 else 0.0
            
            # Keep track of the option with the highest fill ratio
            if fill_ratio > max_fill_ratio:
                max_fill_ratio = fill_ratio
                selected_set = set_type
            
            logger.info(f"Set type {set_type} fill ratio: {fill_ratio:.2f}")
                
        # Check if any set type was detected with sufficient fill ratio
        if max_fill_ratio >= PIXEL_THR and selected_set is not None:
            logger.info(f"Selected set type: {selected_set} with fill ratio {max_fill_ratio:.2f}")
            return selected_set
        else:
            logger.warning(f"No set type detected with sufficient fill ratio (max: {max_fill_ratio:.2f})")
            return "Unknown"
    
    def grade(self, answers: Dict[str, str], answer_key_path: str) -> int:
        """
        Grade the answers using the provided answer key:
        - Load the answer key
        - Count the number of correct answers
        """
        if not os.path.exists(answer_key_path):
            raise FileNotFoundError(f"Answer key not found: {answer_key_path}")
            
        with open(answer_key_path, 'r') as f:
            correct_answers = json.load(f)
            
        score = sum(
            1 for q, ans in correct_answers.items() 
            if answers.get(q) == ans
        )
        
        return score
    
    def process_sheet(self, img_data: bytes) -> Dict[str, Union[str, int]]:
        """
        Process a complete sheet:
        - Convert bytes to numpy array
        - Preprocess the image
        - Align the sheet
        - Extract text fields
        - Extract bubble answers
        - Optional: Grade the sheet
        """
        # Convert bytes to numpy array
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Save original image for reference
        cv2.imwrite('original.jpg', img)
        
        # Process the image for alignment and bubbles
        processed = self.preprocess(img)
        cv2.imwrite('preprocessed.jpg', processed)
        
        aligned = self.align(processed)
        cv2.imwrite('aligned.jpg', aligned)
        
        # Extract data - note we're sending the original color image
        # through the same alignment transform for text extraction
        height, width = img.shape[:2]
        aligned_original = None
        
        try:
            # Get contours and calculate alignment transform
            contours, _ = cv2.findContours(processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if len(contours) > 0:
                largest_contour = max(contours, key=cv2.contourArea)
                peri = cv2.arcLength(largest_contour, True)
                approx = cv2.approxPolyDP(largest_contour, 0.02 * peri, True)
                
                if len(approx) == 4:
                    # Order points and apply same transform to original image
                    src_pts = self._order_points(approx).astype(np.float32)
                    dst_pts = np.array([
                        [0, 0],
                        [REFERENCE_WIDTH, 0],
                        [REFERENCE_WIDTH, REFERENCE_HEIGHT],
                        [0, REFERENCE_HEIGHT]
                    ], dtype=np.float32)
                    
                    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
                    aligned_original = cv2.warpPerspective(img, M, (REFERENCE_WIDTH, REFERENCE_HEIGHT))
                    cv2.imwrite('aligned_original.jpg', aligned_original)
                else:
                    logger.warning("Could not determine precise alignment transform for original image")
                    aligned_original = img  # Fallback
            else:
                logger.warning("No contours found for alignment")
                aligned_original = img  # Fallback
        except Exception as e:
            logger.error(f"Error aligning original image: {str(e)}")
            aligned_original = img  # Fallback
        
        # If we couldn't align the original, use the binary version for everything
        if aligned_original is None:
            aligned_original = aligned
        
        # Extract text from the aligned original (better for OCR) 
        text_data = self.extract_text(aligned_original)
        
        # Extract bubbles from the binary aligned image (better for bubble detection)
        bubble_data = self.extract_bubbles(aligned)
        set_type = self.extract_set_type(aligned)
        
        # Combine results
        result = {
            **text_data,
            "answers": bubble_data,
            "set_type": set_type
        }
        
        return result
    
    def generate_template(self, img_path: str, output_path: str) -> None:
        """
        Generate a template from a blank sheet:
        - This would typically be an interactive wizard
        - For now, we'll use hard-coded values that match the README
        """
        # Read the image and preprocess
        img = cv2.imread(img_path)
        processed = self.preprocess(img)
        aligned = self.align(processed)
        
        # Define text boxes based on README
        text_boxes = {
            "test_booklet_number": [60, 95, 225, 40],
            "date_of_exam": [307, 95, 225, 40],
            "date_of_birth": [554, 95, 225, 40],
            "surname": [60, 150, 665, 38],
            "first_name": [60, 198, 665, 38],
            "middle_name": [60, 246, 665, 38],
            "application_number": [570, 40, 155, 170]
        }
        
        # Define set type bubbles
        set_type_bubbles = {
            "A": [365, 40, 30, 30],
            "B": [395, 40, 30, 30],
            "C": [425, 40, 30, 30]
        }
        
        # Generate bubble grid
        bubbles = {}
        grid = {
            "x0": 50,   # leftmost pixel of col-1
            "y0": 300,  # topmost pixel of row-1
            "w": 685,   # total width of all 5 columns
            "h": 700,   # total height of 30 rows
            "cols": 5,
            "rows": 30
        }
        
        cell_w = grid['w'] / grid['cols']   # 137 px
        cell_h = grid['h'] / grid['rows']   # 23.3px
        
        for q in range(150):
            row, col = divmod(q, 30)
            base_x = grid['x0'] + col * cell_w
            base_y = grid['y0'] + row * cell_h
            
            q_str = str(q + 1)  # 1-indexed
            bubbles[q_str] = {}
            
            for opt in range(5):    # choices 1-5
                opt_str = str(opt + 1)  # 1-indexed
                x = int(base_x + (opt + 0.25) * cell_w / 5)
                y = int(base_y + cell_h / 2)
                
                # Define a 14x14 square ROI centered at (x,y)
                bubbles[q_str][opt_str] = [x - 7, y - 7, 14, 14]
        
        # Combine everything into the template
        template = {
            "text_boxes": text_boxes,
            "set_type_bubbles": set_type_bubbles,
            "bubbles": bubbles
        }
        
        # Save the template
        with open(output_path, 'w') as f:
            json.dump(template, f, indent=2)
            
        logger.info(f"Template generated and saved to {output_path}")
