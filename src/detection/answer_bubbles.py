"""
Answer bubble detection module

Implements the processing of answer bubbles for all 150 questions
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

# Define the regions of interest for answer sections (5 columns of 30 questions)
# These coordinates are placeholders and need to be calibrated for the actual form
ANSWER_SECTIONS = [
    {"start_q": 1, "end_q": 30, "x": 155, "y": 453, "width": 125, "height": 587},
    {"start_q": 31, "end_q": 60, "x": 282, "y": 453, "width": 125, "height": 587},
    {"start_q": 61, "end_q": 90, "x": 409, "y": 453, "width": 125, "height": 587},
    {"start_q": 91, "end_q": 120, "x": 536, "y": 453, "width": 125, "height": 587},
    {"start_q": 121, "end_q": 150, "x": 663, "y": 453, "width": 125, "height": 587}
]

# Number of options per question (A, B, C, D, E or 1, 2, 3, 4, 5)
NUM_OPTIONS = 5


def identify_answer_sections(image: np.ndarray) -> List[Dict[str, any]]:
    """
    Identify all answer section regions in the form
    
    Args:
        image: Aligned form image
        
    Returns:
        List of dictionaries, each containing an answer section ROI and metadata
    """
    answer_sections = []
    
    for section in ANSWER_SECTIONS:
        # Extract the region of interest for this section
        roi = get_roi(image, section["x"], section["y"], 
                     section["width"], section["height"])
        
        answer_sections.append({
            "start_q": section["start_q"],
            "end_q": section["end_q"],
            "roi": roi,
            "coordinates": {
                "x": section["x"],
                "y": section["y"],
                "width": section["width"],
                "height": section["height"]
            }
        })
    
    return answer_sections


def detect_answers_in_section(section_roi: np.ndarray, num_questions: int = 30) -> List[Optional[int]]:
    """
    Detect the selected answers in a section of questions
    
    Args:
        section_roi: ROI containing one section of answer bubbles
        num_questions: Number of questions in this section
        
    Returns:
        List of detected answers (0-based index, None if no answer detected)
    """
    # Convert to grayscale if needed
    if len(section_roi.shape) == 3:
        gray_roi = cv2.cvtColor(section_roi, cv2.COLOR_BGR2GRAY)
    else:
        gray_roi = section_roi.copy()
    
    # Apply threshold to highlight the bubbles
    thresh_roi = apply_threshold(gray_roi, method='adaptive')
    
    # Calculate cell dimensions
    # Each question has NUM_OPTIONS options
    cell_height = section_roi.shape[0] // num_questions
    cell_width = section_roi.shape[1] // NUM_OPTIONS
    
    # Initialize answers
    answers = [None] * num_questions
    
    # Process each question
    for q in range(num_questions):
        # Extract the ROI for this question's answer options
        q_y = q * cell_height
        q_roi = thresh_roi[q_y:q_y + cell_height, :]
        
        # Find contours for this question
        contours = find_contours(q_roi, min_area=20, max_area=200)
        
        # If contours were found
        if contours:
            # Create a mask for this question's ROI to keep coordinate systems aligned
            mask = np.zeros_like(thresh_roi)
            mask[q_y:q_y + cell_height, :] = q_roi
            
            # Use the original coordinates for contour detection
            adjusted_contours = []
            for contour in contours:
                # Adjust y-coordinates of each contour point
                adjusted_contour = contour.copy()
                adjusted_contour[:, :, 1] += q_y
                adjusted_contours.append(adjusted_contour)
            
            # Detect filled bubbles
            filled_bubbles = detect_filled_bubbles(gray_roi, adjusted_contours, threshold_percentage=0.5)
            
            # If exactly one bubble is filled
            if len(filled_bubbles) == 1:
                # Determine which option is selected
                filled_contour = filled_bubbles[0]
                M = cv2.moments(filled_contour)
                
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    option = cx // cell_width
                    
                    # Record the selected option (0-based index)
                    answers[q] = option
    
    return answers


def detect_all_answers(image: np.ndarray) -> Dict[int, Optional[int]]:
    """
    Detect all answers for all 150 questions
    
    Args:
        image: Aligned form image
        
    Returns:
        Dictionary mapping question numbers (1-150) to selected options (0-4, None if no answer)
    """
    # Identify all answer sections
    sections = identify_answer_sections(image)
    
    # Initialize answers dictionary
    all_answers = {}
    
    # Process each section
    for section in sections:
        # Detect answers in this section
        section_answers = detect_answers_in_section(section["roi"], 
                                                  section["end_q"] - section["start_q"] + 1)
        
        # Add to the complete answers dictionary
        for i, answer in enumerate(section_answers):
            question_num = section["start_q"] + i
            all_answers[question_num] = answer
    
    return all_answers


def convert_answer_indices_to_options(answers: Dict[int, Optional[int]]) -> Dict[int, Optional[str]]:
    """
    Convert 0-based answer indices to option letters or numbers
    
    Args:
        answers: Dictionary mapping question numbers to option indices
        
    Returns:
        Dictionary mapping question numbers to option letters (A-E) or numbers (1-5)
    """
    # Define mapping from index to option
    # index_to_option = {0: "A", 1: "B", 2: "C", 3: "D", 4: "E"}  # Use this for letters
    index_to_option = {0: "1", 1: "2", 2: "3", 3: "4", 4: "5"}  # Use this for numbers
    
    converted_answers = {}
    for question, answer_index in answers.items():
        if answer_index is not None:
            converted_answers[question] = index_to_option.get(answer_index)
        else:
            converted_answers[question] = None
    
    return converted_answers


def process_answer_bubbles(image: np.ndarray) -> Dict[str, any]:
    """
    Process all answer bubbles in the form
    
    Args:
        image: Aligned form image
        
    Returns:
        Dictionary with all detected answers and other metadata
    """
    # Detect answers (0-based indices)
    answers_indices = detect_all_answers(image)
    
    # Convert to option letters or numbers
    answers_options = convert_answer_indices_to_options(answers_indices)
    
    # Collect answer sections for metadata
    answer_sections = identify_answer_sections(image)
    section_info = []
    for section in answer_sections:
        section_info.append({
            "start_q": section["start_q"],
            "end_q": section["end_q"],
            "coordinates": section["coordinates"]
        })
    
    return {
        "answers": answers_options,
        "answer_indices": answers_indices,
        "sections": section_info
    }
