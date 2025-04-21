"""
OMR processing service

Implements the core OMR form processing functionality:
1. Get the Main Mark (#1)
2. Auto Canvas (#2) 
3-8. Extract Personal Information
9-10. Set Type Processing
11. Application Number Processing
12. Answer Bubble Processing
"""
import os
import cv2
import numpy as np
import json
import logging
from typing import Dict, Any, Optional, List, Tuple

from app.utils.image_utils import (
    load_image,
    resize_image,
    enhance_contrast,
    apply_threshold,
    find_contours,
    detect_filled_bubbles,
    remove_grid_lines,
    get_roi,
    perspective_transform
)

logger = logging.getLogger(__name__)


class OMRProcessor:
    """
    Core OMR processing implementation
    """
    
    def __init__(self, debug_mode: bool = False):
        """
        Initialize the OMR processor
        
        Args:
            debug_mode: Whether to save intermediate results for debugging
        """
        self.debug_mode = debug_mode
        self.results = {}
        self.debug_images = {}
        
        # Define ROIs based on template - these would normally come from the database
        self.roi_coordinates = {
            "booklet_number": {"x": 207, "y": 143, "width": 285, "height": 30},
            "date_of_exam": {"x": 207, "y": 166, "width": 285, "height": 30},
            "date_of_birth": {"x": 207, "y": 188, "width": 285, "height": 30},
            "surname": {"x": 40, "y": 220, "width": 540, "height": 30},
            "first_name": {"x": 40, "y": 261, "width": 540, "height": 30},
            "middle_name": {"x": 40, "y": 303, "width": 540, "height": 30},
            "set_type": {"x": 452, "y": 138, "width": 50, "height": 50},
            "application_number": {"x": 690, "y": 177, "width": 125, "height": 183}
        }
        
        # Define answer bubble sections
        self.answer_sections = [
            {"start_q": 1, "end_q": 30, "x": 155, "y": 453, "width": 125, "height": 587},
            {"start_q": 31, "end_q": 60, "x": 282, "y": 453, "width": 125, "height": 587},
            {"start_q": 61, "end_q": 90, "x": 409, "y": 453, "width": 125, "height": 587},
            {"start_q": 91, "end_q": 120, "x": 536, "y": 453, "width": 125, "height": 587},
            {"start_q": 121, "end_q": 150, "x": 663, "y": 453, "width": 125, "height": 587}
        ]
        
        # Set type bubbles
        self.set_type_bubbles = {
            "A": {"center_x": 15, "center_y": 15, "radius": 10},
            "B": {"center_x": 15, "center_y": 27, "radius": 10},
            "C": {"center_x": 15, "center_y": 39, "radius": 10}
        }
        
        # Processing parameters
        self.app_number_columns = 11
        self.app_number_rows = 10  # 0-9
        self.num_options_per_question = 5  # A-E or 1-5
        self.bubble_fill_threshold = 0.5
    
    async def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        Process an OMR form image following the required sequence
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing image: {image_path}")
        
        # Reset results
        self.results = {}
        self.debug_images = {}
        
        try:
            # Load the image
            image = load_image(image_path)
            self.results["original_image"] = image
            
            if self.debug_mode:
                self.debug_images["original"] = image.copy()
            
            # 1-2. Main Mark Detection and Form Alignment
            logger.info("Steps #1-#2: Main Mark Detection and Form Alignment")
            alignment_result = await self.detect_main_mark_and_align(image)
            aligned_image = alignment_result["aligned_image"]
            self.results["aligned_image"] = aligned_image
            self.results["main_mark"] = alignment_result["main_mark"]
            
            if self.debug_mode:
                self.debug_images["aligned"] = aligned_image.copy()
            
            # 3-8. Extract Personal Information
            logger.info("Steps #3-#8: Personal Information Extraction")
            personal_info = await self.extract_personal_info(aligned_image)
            self.results["personal_info"] = personal_info
            
            if self.debug_mode:
                for field_name, field_data in personal_info.items():
                    self.debug_images[f"personal_info_{field_name}"] = field_data["roi"]
                    self.debug_images[f"personal_info_{field_name}_cleaned"] = field_data["cleaned_roi"]
            
            # 9-10. Set Type Detection
            logger.info("Steps #9-#10: Set Type Detection")
            set_type_result = await self.detect_set_type(aligned_image)
            self.results["set_type"] = set_type_result
            
            if self.debug_mode:
                self.debug_images["set_type"] = set_type_result["roi"]
            
            # 11. Application Number Processing
            logger.info("Step #11: Application Number Processing")
            app_number_result = await self.process_application_number(aligned_image)
            self.results["application_number"] = app_number_result
            
            if self.debug_mode:
                self.debug_images["application_number"] = app_number_result["roi"]
            
            # 12. Answer Bubble Processing
            logger.info("Step #12: Answer Bubble Processing")
            answers_result = await self.process_answer_bubbles(aligned_image)
            self.results["answers"] = answers_result
            
            # Format results
            extracted_data = await self.format_results()
            self.results["extracted_data"] = extracted_data
            
            logger.info("Image processing completed successfully")
            
            return self.results
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}", exc_info=True)
            raise
    
    async def detect_main_mark_and_align(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Steps #1 and #2: Detect the main mark and align the form
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with alignment results
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Enhance contrast
        enhanced = enhance_contrast(gray)
        
        # Apply threshold
        thresh = apply_threshold(enhanced, method='adaptive')
        
        # Find contours
        contours = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[0] if len(contours) == 2 else contours[1]
        
        # Sort contours by area (largest first)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        # Look for the main mark
        main_mark = None
        for contour in contours[:50]:  # Check the 50 largest contours
            # Approximate the contour
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            
            # The main mark should have 3 distinct line segments
            # This is a simplified check - in production we would have more
            # sophisticated detection based on the exact form layout
            if len(approx) >= 3 and len(approx) <= 5:
                main_mark = approx
                break
        
        if main_mark is None:
            raise ValueError("Main mark (#1) not detected. Cannot proceed with processing.")
        
        # Calculate the destination points to ensure exact ratio is maintained
        h, w = image.shape[:2]
        marker_points = np.array([p[0] for p in main_mark], dtype=np.float32)
        
        # Define target points (where the corners should be in the aligned image)
        # These values would be calibrated based on the exact form layout
        target_points = np.array([
            [50, 50],               # Top-left
            [w - 50, 50],           # Top-right
            [w - 50, h - 50],       # Bottom-right
            [50, h - 50]            # Bottom-left
        ], dtype=np.float32)
        
        # If we have more or fewer than 4 points, adjust accordingly
        if len(marker_points) != 4:
            # Use a simplified approach based on bounding box
            x, y, w_rect, h_rect = cv2.boundingRect(main_mark)
            marker_points = np.array([
                [x, y],                     # Top-left
                [x + w_rect, y],            # Top-right
                [x + w_rect, y + h_rect],   # Bottom-right
                [x, y + h_rect]             # Bottom-left
            ], dtype=np.float32)
        
        # Order points in clockwise direction (top-left, top-right, bottom-right, bottom-left)
        marker_points = self.order_points(marker_points)
        
        # Get the perspective transform matrix
        matrix = cv2.getPerspectiveTransform(marker_points, target_points)
        
        # Apply the perspective transformation
        aligned = cv2.warpPerspective(image, matrix, (w, h))
        
        return {
            "aligned_image": aligned,
            "main_mark": main_mark,
            "transform_matrix": matrix
        }
    
    def order_points(self, pts: np.ndarray) -> np.ndarray:
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
    
    async def extract_personal_info(self, image: np.ndarray) -> Dict[str, Dict[str, Any]]:
        """
        Steps #3-#8: Extract personal information fields
        
        Args:
            image: Aligned image
            
        Returns:
            Dictionary with personal information fields
        """
        # Initialize results
        results = {}
        
        # Process each personal information field
        for field_name, roi_coords in self.roi_coordinates.items():
            # Skip non-personal info fields
            if field_name in ["set_type", "application_number"]:
                continue
            
            # Extract ROI
            roi = get_roi(image, roi_coords["x"], roi_coords["y"], 
                         roi_coords["width"], roi_coords["height"])
            
            # Remove grid lines
            cleaned_roi = remove_grid_lines(roi)
            
            # Store results
            results[field_name] = {
                "field_name": field_name,
                "roi": roi,
                "cleaned_roi": cleaned_roi,
                "coordinates": roi_coords
            }
        
        return results
    
    async def detect_set_type(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Steps #9-#10: Detect set type (A, B, or C)
        
        Args:
            image: Aligned image
            
        Returns:
            Dictionary with set type results
        """
        # Get ROI for set type
        roi_coords = self.roi_coordinates["set_type"]
        roi = get_roi(image, roi_coords["x"], roi_coords["y"], 
                     roi_coords["width"], roi_coords["height"])
        
        # Convert to grayscale
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold
        thresh_roi = apply_threshold(gray_roi, method='adaptive')
        
        # Find contours
        contours = find_contours(thresh_roi, min_area=50, max_area=300)
        
        # Detect filled bubbles
        filled_bubbles = detect_filled_bubbles(gray_roi, contours, threshold_percentage=self.bubble_fill_threshold)
        
        # Determine set type
        set_type = "Unknown"
        if len(filled_bubbles) == 1:
            # Get center of the filled bubble
            M = cv2.moments(filled_bubbles[0])
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                # Check if it matches any of the expected positions
                for type_name, bubble in self.set_type_bubbles.items():
                    if (abs(cx - bubble["center_x"]) < bubble["radius"] and 
                        abs(cy - bubble["center_y"]) < bubble["radius"]):
                        set_type = type_name
                        break
        
        return {
            "set_type": set_type,
            "roi": roi,
            "coordinates": roi_coords
        }
    
    async def process_application_number(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Step #11: Process the application number
        
        Args:
            image: Aligned image
            
        Returns:
            Dictionary with application number results
        """
        # Get ROI for application number
        roi_coords = self.roi_coordinates["application_number"]
        roi = get_roi(image, roi_coords["x"], roi_coords["y"], 
                     roi_coords["width"], roi_coords["height"])
        
        # Convert to grayscale
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold
        thresh_roi = apply_threshold(gray_roi, method='adaptive')
        
        # Calculate grid cell dimensions
        cell_width = roi.shape[1] // self.app_number_columns
        cell_height = roi.shape[0] // self.app_number_rows
        
        # Initialize application number
        app_number = [""] * self.app_number_columns
        
        # Process each column
        for col in range(self.app_number_columns):
            # Extract column ROI
            col_x = col * cell_width
            col_roi = thresh_roi[:, col_x:col_x + cell_width]
            
            # Find contours
            contours = find_contours(col_roi, min_area=20, max_area=200)
            
            # Create a mask for this column to maintain coordinates
            mask = np.zeros_like(thresh_roi)
            mask[:, col_x:col_x + cell_width] = col_roi
            
            # Adjust contours to the original coordinates
            adjusted_contours = []
            for contour in contours:
                adjusted_contour = contour.copy()
                adjusted_contour[:, :, 0] += col_x
                adjusted_contours.append(adjusted_contour)
            
            # Detect filled bubbles
            filled_bubbles = detect_filled_bubbles(gray_roi, adjusted_contours, 
                                                 threshold_percentage=self.bubble_fill_threshold)
            
            # Determine which bubble is filled
            if len(filled_bubbles) == 1:
                # Get center of the filled bubble
                M = cv2.moments(filled_bubbles[0])
                if M["m00"] != 0:
                    cy = int(M["m01"] / M["m00"])
                    row = cy // cell_height
                    
                    # Map row to digit (0-9)
                    digit = row
                    app_number[col] = str(digit)
        
        # Combine digits
        app_number_str = "".join([digit if digit else "X" for digit in app_number])
        
        return {
            "application_number": app_number_str,
            "roi": roi,
            "coordinates": roi_coords
        }
    
    async def process_answer_bubbles(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Step #12: Process answer bubbles
        
        Args:
            image: Aligned image
            
        Returns:
            Dictionary with answer bubble results
        """
        # Initialize answers
        answers = {}
        
        # Process each answer section
        for section in self.answer_sections:
            # Extract section ROI
            roi = get_roi(image, section["x"], section["y"], 
                         section["width"], section["height"])
            
            # Convert to grayscale
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold
            thresh_roi = apply_threshold(gray_roi, method='adaptive')
            
            # Calculate dimensions
            num_questions = section["end_q"] - section["start_q"] + 1
            cell_height = roi.shape[0] // num_questions
            cell_width = roi.shape[1] // self.num_options_per_question
            
            # Process each question
            for q_idx in range(num_questions):
                question_num = section["start_q"] + q_idx
                
                # Extract ROI for this question
                q_y = q_idx * cell_height
                q_roi = thresh_roi[q_y:q_y + cell_height, :]
                
                # Find contours
                contours = find_contours(q_roi, min_area=20, max_area=200)
                
                # Create a mask for this question to maintain coordinates
                mask = np.zeros_like(thresh_roi)
                mask[q_y:q_y + cell_height, :] = q_roi
                
                # Adjust contours to the original coordinates
                adjusted_contours = []
                for contour in contours:
                    adjusted_contour = contour.copy()
                    adjusted_contour[:, :, 1] += q_y
                    adjusted_contours.append(adjusted_contour)
                
                # Detect filled bubbles
                filled_bubbles = detect_filled_bubbles(gray_roi, adjusted_contours, 
                                                     threshold_percentage=self.bubble_fill_threshold)
                
                # Determine which option is selected
                if len(filled_bubbles) == 1:
                    # Get center of the filled bubble
                    M = cv2.moments(filled_bubbles[0])
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        option_idx = cx // cell_width
                        
                        # Map to option (A-E or 1-5)
                        option = self.map_option_index_to_letter(option_idx)
                        answers[str(question_num)] = option
        
        return {
            "answers": answers,
            "sections": self.answer_sections
        }
    
    def map_option_index_to_letter(self, index: int) -> str:
        """
        Map a 0-based index to an option letter or number
        
        Args:
            index: 0-based index
            
        Returns:
            Option letter (A-E) or number (1-5)
        """
        # Use letters (A-E)
        options = ["A", "B", "C", "D", "E"]
        
        # Alternatively, use numbers (1-5)
        # options = ["1", "2", "3", "4", "5"]
        
        if 0 <= index < len(options):
            return options[index]
        else:
            return "?"
    
    async def format_results(self) -> Dict[str, Any]:
        """
        Format the results for output
        
        Returns:
            Formatted results dictionary
        """
        # In a real implementation, we would use OCR to extract text from personal info fields
        # Here we'll just use placeholders
        
        # Get answers
        answers = {}
        if "answers" in self.results and "answers" in self.results["answers"]:
            answers = self.results["answers"]["answers"]
        
        # Format results
        formatted = {
            "booklet_number": "123456",  # Placeholder - would use OCR in real implementation
            "date_of_exam": "04/15/2025",  # Placeholder
            "date_of_birth": "01/01/1990",  # Placeholder
            "surname": "SMITH",  # Placeholder
            "first_name": "JOHN",  # Placeholder
            "middle_name": "DOE",  # Placeholder
            "set_type": self.results.get("set_type", {}).get("set_type", "Unknown"),
            "application_number": self.results.get("application_number", {}).get("application_number", "Unknown"),
            "answers": answers
        }
        
        return formatted
    
    async def save_debug_images(self, output_dir: str) -> Dict[str, str]:
        """
        Save debug images to the specified directory
        
        Args:
            output_dir: Directory to save images to
            
        Returns:
            Dictionary mapping image names to saved paths
        """
        if not self.debug_mode:
            logger.warning("Debug mode is not enabled. No images to save.")
            return {}
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Save images
        saved_paths = {}
        for name, image in self.debug_images.items():
            output_path = os.path.join(output_dir, f"{name}.jpg")
            cv2.imwrite(output_path, image)
            saved_paths[name] = output_path
            logger.debug(f"Saved debug image: {output_path}")
        
        return saved_paths


# Create singleton instance
omr_processor = OMRProcessor(debug_mode=True)
