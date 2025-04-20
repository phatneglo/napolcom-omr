#!/usr/bin/env python3
"""
This script generates a precise template for the NAPOLCOM answer sheet
by analyzing the sample images in the debug_output directory.
"""

import cv2
import numpy as np
import json
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants from processor.py
REFERENCE_WIDTH = 785
REFERENCE_HEIGHT = 1024

def analyze_grid(image_path, output_template_path):
    """
    Analyze the aligned image to automatically detect the grid pattern
    and generate a precise template.
    """
    # Load the aligned image (should be binary)
    if not os.path.exists(image_path):
        logger.error(f"Image not found: {image_path}")
        return False
        
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        logger.error(f"Failed to load image: {image_path}")
        return False
    
    # Create output directory for debug images
    debug_dir = "template_debug"
    os.makedirs(debug_dir, exist_ok=True)
    
    # Save a copy of the input image
    cv2.imwrite(f"{debug_dir}/input.jpg", img)
    
    # Create template structure
    template = {
        "text_boxes": {
            "test_booklet_number": [60, 95, 225, 40],
            "date_of_exam": [307, 95, 225, 40],
            "date_of_birth": [554, 95, 225, 40],
            "surname": [60, 150, 665, 38],
            "first_name": [60, 198, 665, 38],
            "middle_name": [60, 246, 665, 38],
            "application_number": [570, 40, 155, 170]
        },
        "set_type_bubbles": {
            "A": [365, 40, 30, 30],
            "B": [395, 40, 30, 30],
            "C": [425, 40, 30, 30]
        },
        "bubbles": {}
    }
    
    # Use horizontal projection to find rows of bubbles
    horizontal_projection = np.sum(img, axis=1)
    
    # Normalize for visualization
    norm_projection = horizontal_projection / np.max(horizontal_projection) * 255
    projection_img = np.zeros((REFERENCE_HEIGHT, 300), dtype=np.uint8)
    for i, val in enumerate(norm_projection):
        cv2.line(projection_img, (0, i), (int(val), i), 255, 1)
    
    cv2.imwrite(f"{debug_dir}/horizontal_projection.jpg", projection_img)
    
    # Determine the grid region (skip header area)
    grid_start_y = 300  # Approximate start of grid based on README
    grid_end_y = 1000   # Approximate end of grid
    
    # Find local maxima in the horizontal projection within the grid region
    # These indicate rows of bubbles
    row_positions = []
    for y in range(grid_start_y, grid_end_y):
        # Check if this is a local maximum
        if (horizontal_projection[y] > horizontal_projection[y-1] and 
            horizontal_projection[y] > horizontal_projection[y+1] and
            horizontal_projection[y] > np.mean(horizontal_projection[grid_start_y:grid_end_y])):
            row_positions.append(y)
    
    # If too many potential rows, filter them further (take top 30 by intensity)
    if len(row_positions) > 30:
        row_intensities = [(y, horizontal_projection[y]) for y in row_positions]
        row_intensities.sort(key=lambda x: x[1], reverse=True)
        row_positions = [y for y, _ in row_intensities[:30]]
        row_positions.sort()  # Sort back by y-position
    
    # Use vertical projection to find columns
    vertical_projection = np.sum(img, axis=0)
    
    # Normalize for visualization
    norm_projection = vertical_projection / np.max(vertical_projection) * 255
    projection_img = np.zeros((300, REFERENCE_WIDTH), dtype=np.uint8)
    for i, val in enumerate(norm_projection):
        cv2.line(projection_img, (i, 299), (i, 299-int(val)), 255, 1)
    
    cv2.imwrite(f"{debug_dir}/vertical_projection.jpg", projection_img)
    
    # Find columns (should have 5 main columns)
    column_start_x = 50   # Approximate start x based on README
    column_end_x = 735    # Approximate end x
    column_width = (column_end_x - column_start_x) / 5
    
    column_positions = []
    for col in range(5):
        col_center = int(column_start_x + (col + 0.5) * column_width)
        column_positions.append(col_center)
    
    # Create debug image to visualize the detected grid
    grid_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    
    # Draw rows
    for y in row_positions:
        cv2.line(grid_img, (0, y), (REFERENCE_WIDTH, y), (0, 255, 0), 1)
    
    # Draw columns
    for x in column_positions:
        cv2.line(grid_img, (x, 0), (x, REFERENCE_HEIGHT), (0, 0, 255), 1)
    
    cv2.imwrite(f"{debug_dir}/detected_grid.jpg", grid_img)
    
    # Calculate bubble positions based on detected grid
    bubble_radius = 7  # Half the bubble size
    
    # For each row and column, find the 5 bubble positions (5 options per question)
    # and add them to the template
    for row_idx, row_y in enumerate(row_positions):
        for col_idx, col_x in enumerate(column_positions):
            # Calculate question number (1-150)
            q_num = col_idx * 30 + row_idx + 1
            
            # For each option (1-5) in the question
            option_width = column_width / 5
            template["bubbles"][str(q_num)] = {}
            
            for opt in range(1, 6):
                # Calculate the center of the bubble
                option_center_x = int(col_x - column_width/2 + (opt - 0.5) * option_width)
                
                # Define the bubble region (square for simplicity)
                x1 = option_center_x - bubble_radius
                y1 = row_y - bubble_radius
                w = bubble_radius * 2
                h = bubble_radius * 2
                
                template["bubbles"][str(q_num)][str(opt)] = [x1, y1, w, h]
                
                # Draw the bubble on the debug image
                color = (255, 0, 255)  # Magenta for bubble regions
                cv2.rectangle(grid_img, (x1, y1), (x1+w, y1+h), color, 1)
                
                # Add question/option number for first few questions
                if q_num <= 5:
                    cv2.putText(grid_img, f"{q_num}.{opt}", (x1, y1-5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
    
    # Save the debug image with all bubbles
    cv2.imwrite(f"{debug_dir}/detected_bubbles.jpg", grid_img)
    
    # Save the template to file
    with open(output_template_path, 'w') as f:
        json.dump(template, f, indent=2)
    
    logger.info(f"Template saved to {output_template_path}")
    logger.info(f"Found {len(row_positions)} rows and {len(column_positions)} columns")
    
    return True

if __name__ == "__main__":
    # Check for aligned image in debug_output directory
    aligned_path = "debug_output/aligned.jpg"
    
    if not os.path.exists(aligned_path):
        logger.error(f"Aligned image not found: {aligned_path}")
        logger.error("Please process a sample image first using the API or main.py")
        sys.exit(1)
    
    output_path = "template_precise.json"
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    
    if analyze_grid(aligned_path, output_path):
        logger.info("Template generation successful!")
        logger.info("To use the new template:")
        logger.info(f"1. Edit api.py to use '{output_path}' instead of 'template.json'")
        logger.info(f"2. Or run: python main.py samples/*.jpg --out results.csv --template {output_path}")
    else:
        logger.error("Template generation failed")
        sys.exit(1)
