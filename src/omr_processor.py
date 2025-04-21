"""
Main OMR Form Processor module

Combines all processing steps in the required sequence:
1. Get the Main Mark (#1)
2. Auto Canvas (#2)
3-8. Extract Personal Information
9-10. Set Type Processing
11. Application Number Processing
12. Answer Bubble Processing
"""
import cv2
import numpy as np
import json
from typing import Dict, List, Optional, Tuple

from .preprocessing.form_alignment import process_form_alignment
from .detection.personal_info import extract_all_personal_info
from .detection.set_type import process_set_type
from .detection.application_number import process_application_number
from .detection.answer_bubbles import process_answer_bubbles
from .utils.image_utils import load_image, resize_image


class OMRProcessor:
    """
    Main processor class for OMR form processing
    """
    
    def __init__(self, debug_mode: bool = False):
        """
        Initialize the OMR processor
        
        Args:
            debug_mode: Whether to enable debug mode (save intermediate results)
        """
        self.debug_mode = debug_mode
        self.results = {}
        self.debug_images = {}
    
    def process_image(self, image_path: str) -> Dict[str, any]:
        """
        Process an OMR form image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with all extracted information
        """
        # Reset results
        self.results = {}
        self.debug_images = {}
        
        # Load the image
        image = load_image(image_path)
        self.results["original_image"] = image
        
        if self.debug_mode:
            self.debug_images["original"] = image.copy()
        
        # 1-2. Align the form
        print("Processing steps #1-#2: Main Mark Detection and Form Alignment")
        alignment_result = process_form_alignment(image)
        aligned_image = alignment_result["aligned_image"]
        self.results["aligned_image"] = aligned_image
        self.results["main_mark"] = alignment_result["main_mark"]
        
        if self.debug_mode:
            self.debug_images["aligned"] = aligned_image.copy()
        
        # 3-8. Extract personal information
        print("Processing steps #3-#8: Personal Information Extraction")
        personal_info = extract_all_personal_info(aligned_image)
        self.results["personal_info"] = personal_info
        
        if self.debug_mode:
            # Save ROIs for each personal info field
            for field_name, field_data in personal_info.items():
                self.debug_images[f"personal_info_{field_name}"] = field_data["roi"]
                self.debug_images[f"personal_info_{field_name}_cleaned"] = field_data["cleaned_roi"]
        
        # 9-10. Process set type
        print("Processing steps #9-#10: Set Type Detection")
        set_type_result = process_set_type(aligned_image)
        self.results["set_type"] = set_type_result
        
        if self.debug_mode:
            self.debug_images["set_type"] = set_type_result["roi"]
        
        # 11. Process application number
        print("Processing step #11: Application Number Processing")
        app_number_result = process_application_number(aligned_image)
        self.results["application_number"] = app_number_result
        
        if self.debug_mode:
            self.debug_images["application_number"] = app_number_result["roi"]
        
        # 12. Process answer bubbles
        print("Processing step #12: Answer Bubble Processing")
        answers_result = process_answer_bubbles(aligned_image)
        self.results["answers"] = answers_result
        
        # Combine all results into a clean format
        extracted_data = self.format_results()
        self.results["extracted_data"] = extracted_data
        
        return self.results
    
    def format_results(self) -> Dict[str, any]:
        """
        Format the results into a clean dictionary
        
        Returns:
            Formatted results dictionary
        """
        # Format the personal information fields
        # In a real implementation, we would use OCR to extract text from these fields
        
        # Format the answers
        answers = {}
        if "answers" in self.results and "answers" in self.results["answers"]:
            for q_num, option in self.results["answers"]["answers"].items():
                answers[str(q_num)] = option if option is not None else "No answer"
        
        # Compile the formatted results
        formatted = {
            "booklet_number": "To be extracted with OCR",  # Placeholder
            "date_of_exam": "To be extracted with OCR",    # Placeholder
            "date_of_birth": "To be extracted with OCR",   # Placeholder
            "surname": "To be extracted with OCR",         # Placeholder
            "first_name": "To be extracted with OCR",      # Placeholder
            "middle_name": "To be extracted with OCR",     # Placeholder
            "set_type": self.results.get("set_type", {}).get("set_type", "Unknown"),
            "application_number": self.results.get("application_number", {}).get("application_number", "Unknown"),
            "answers": answers
        }
        
        return formatted
    
    def save_debug_images(self, output_dir: str) -> None:
        """
        Save debug images to the specified directory
        
        Args:
            output_dir: Directory to save images to
        """
        if not self.debug_mode:
            print("Debug mode is not enabled. No images to save.")
            return
        
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        for name, image in self.debug_images.items():
            output_path = os.path.join(output_dir, f"{name}.png")
            cv2.imwrite(output_path, image)
            print(f"Saved debug image: {output_path}")
    
    def save_results(self, output_path: str) -> None:
        """
        Save the results to a JSON file
        
        Args:
            output_path: Path to save the results to
        """
        # Create a copy of the results without the image data
        results_to_save = self.results["extracted_data"].copy()
        
        with open(output_path, 'w') as f:
            json.dump(results_to_save, f, indent=2)
        
        print(f"Results saved to: {output_path}")
