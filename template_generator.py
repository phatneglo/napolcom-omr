#!/usr/bin/env python3
"""
Interactive template generator for NAPOLCOM OMR parser.

This script helps create a template by allowing the user to select regions on the image.
"""

import argparse
import cv2
import json
import numpy as np
import os
from typing import Dict, List, Tuple

# Constants
REFERENCE_WIDTH = 785
REFERENCE_HEIGHT = 1024

# Global variables for mouse callback
drawing = False
roi_pts = []
current_roi = None
image = None
orig_image = None
window_name = "Template Generator"

def mouse_callback(event, x, y, flags, param):
    global drawing, roi_pts, current_roi, image, orig_image
    
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        roi_pts = [(x, y)]
        
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            # Draw a rectangle for reference
            temp_img = orig_image.copy()
            cv2.rectangle(temp_img, roi_pts[0], (x, y), (0, 255, 0), 2)
            image = temp_img
            
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        roi_pts.append((x, y))
        
        # Ensure first point is top-left and second is bottom-right
        x1, y1 = min(roi_pts[0][0], roi_pts[1][0]), min(roi_pts[0][1], roi_pts[1][1])
        x2, y2 = max(roi_pts[0][0], roi_pts[1][0]), max(roi_pts[0][1], roi_pts[1][1])
        
        # Calculate width and height
        w, h = x2 - x1, y2 - y1
        
        # Store ROI
        current_roi = [x1, y1, w, h]
        
        # Draw the final rectangle
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)


def preprocess(img: np.ndarray) -> np.ndarray:
    """Preprocess the image for better recognition."""
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


def align(img: np.ndarray) -> np.ndarray:
    """Align the image to get canonical 785×1024 canvas."""
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
    approx = order_points(approx)
    
    # Get perspective transform
    dst_pts = np.array([
        [0, 0],
        [REFERENCE_WIDTH, 0],
        [REFERENCE_WIDTH, REFERENCE_HEIGHT],
        [0, REFERENCE_HEIGHT]
    ], dtype=np.float32)
    
    src_pts = np.array(approx, dtype=np.float32)
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    
    # Apply perspective transform to both binary and original
    warped = cv2.warpPerspective(img, M, (REFERENCE_WIDTH, REFERENCE_HEIGHT))
    
    return warped


def order_points(pts: np.ndarray) -> np.ndarray:
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


def select_roi(img: np.ndarray, field_name: str) -> List[int]:
    """Select a region of interest (ROI) from the image."""
    global current_roi, image, orig_image
    
    # Reset globals
    current_roi = None
    orig_image = img.copy()
    image = img.copy()
    
    # Create window and set mouse callback
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, mouse_callback)
    
    # Instruct user
    print(f"Select region for {field_name}")
    print("Click and drag to select the region, then press Enter to confirm or 'r' to retry")
    
    while True:
        # Display the image
        cv2.imshow(window_name, image)
        key = cv2.waitKey(1) & 0xFF
        
        # Enter key confirms selection
        if key == 13 and current_roi is not None:
            break
            
        # 'r' key resets selection
        if key == ord('r'):
            current_roi = None
            image = orig_image.copy()
    
    # Clean up
    cv2.destroyWindow(window_name)
    
    return current_roi


def generate_template(img_path: str, output_path: str) -> None:
    """Generate a template from a blank sheet."""
    # Read the image
    orig_img = cv2.imread(img_path)
    if orig_img is None:
        raise ValueError(f"Failed to load image: {img_path}")
    
    # Preprocess and align
    processed = preprocess(orig_img)
    aligned_binary = align(processed)
    
    # Create a color version of the aligned image for visualization
    aligned_color = cv2.cvtColor(aligned_binary, cv2.COLOR_GRAY2BGR)
    
    # Define text boxes to select
    text_boxes = [
        "test_booklet_number",
        "date_of_exam",
        "date_of_birth",
        "surname",
        "first_name",
        "middle_name",
        "application_number"
    ]
    
    # Dictionary to store ROIs
    template = {
        "text_boxes": {},
        "set_type_bubbles": {},
        "bubbles": {}
    }
    
    # Select text boxes
    print("Let's select regions for each text field:")
    for field in text_boxes:
        roi = select_roi(aligned_color, field)
        template["text_boxes"][field] = roi
        
        # Draw the selected region on the image for reference
        x, y, w, h = roi
        cv2.rectangle(aligned_color, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(aligned_color, field, (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Select set type bubbles
    print("\nNow let's select regions for set type bubbles (A, B, C):")
    for set_type in ["A", "B", "C"]:
        roi = select_roi(aligned_color, f"Set Type {set_type}")
        template["set_type_bubbles"][set_type] = roi
        
        # Draw the selected region
        x, y, w, h = roi
        cv2.rectangle(aligned_color, (x, y), (x+w, y+h), (0, 0, 255), 2)
        cv2.putText(aligned_color, f"Set {set_type}", (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
    # Select bubble grid layout
    print("\nNow let's define the bubble grid:")
    print("1. Select the top-left corner of the grid")
    top_left = select_roi(aligned_color, "Grid Top-Left Corner")[0:2]
    cv2.circle(aligned_color, top_left, 5, (255, 0, 0), -1)
    
    print("2. Select the bottom-right corner of the grid")
    bottom_right = select_roi(aligned_color, "Grid Bottom-Right Corner")[0:2]
    cv2.circle(aligned_color, bottom_right, 5, (255, 0, 0), -1)
    
    # Draw the grid outline
    x1, y1 = top_left
    x2, y2 = bottom_right
    cv2.rectangle(aligned_color, (x1, y1), (x2, y2), (255, 0, 0), 2)
    
    # Calculate grid dimensions
    grid = {
        "x0": x1,
        "y0": y1,
        "w": x2 - x1,
        "h": y2 - y1,
        "cols": 5,
        "rows": 30
    }
    
    # Calculate the width and height of each cell
    cell_w = grid["w"] / grid["cols"]
    cell_h = grid["h"] / grid["rows"]
    
    # Draw grid lines for reference
    for col in range(1, grid["cols"]):
        x = int(x1 + col * cell_w)
        cv2.line(aligned_color, (x, y1), (x, y2), (255, 0, 0), 1)
        
    for row in range(1, grid["rows"]):
        y = int(y1 + row * cell_h)
        cv2.line(aligned_color, (x1, y), (x2, y), (255, 0, 0), 1)
    
    # Show the grid layout
    cv2.namedWindow("Grid Layout")
    cv2.imshow("Grid Layout", aligned_color)
    print("Press any key to continue with bubble generation...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    # Generate bubble positions
    print("Generating bubble positions...")
    for q in range(1, 151):
        # Calculate which column and row this question belongs to
        col = (q - 1) // 30  # 0-based column index (0-4)
        row = (q - 1) % 30   # 0-based row index (0-29)
        
        # Calculate base coordinates for this question
        base_x = grid["x0"] + col * cell_w
        base_y = grid["y0"] + row * cell_h
        
        template["bubbles"][str(q)] = {}
        
        # Generate 5 bubble positions for each question
        for opt in range(1, 6):
            x = int(base_x + (opt - 0.75) * (cell_w / 5))
            y = int(base_y + cell_h / 2)
            
            # Define a 14x14 square ROI centered at (x,y)
            template["bubbles"][str(q)][str(opt)] = [x - 7, y - 7, 14, 14]
            
            # Mark bubble positions on the image
            if q <= 5:  # Only show first few for clarity
                cv2.circle(aligned_color, (x, y), 7, (0, 255, 255), 1)
                cv2.putText(aligned_color, f"{q}.{opt}", (x-5, y+3),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 255), 1)
    
    # Show the first few bubbles for verification
    cv2.namedWindow("Bubble Layout (first few)")
    cv2.imshow("Bubble Layout (first few)", aligned_color)
    print("Press any key to save the template...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    # Save the template
    with open(output_path, 'w') as f:
        json.dump(template, f, indent=2)
        
    print(f"Template saved to {output_path}")
    
    # Save an annotated image for reference
    reference_path = os.path.splitext(output_path)[0] + "_reference.jpg"
    cv2.imwrite(reference_path, aligned_color)
    print(f"Reference image saved to {reference_path}")


def main():
    parser = argparse.ArgumentParser(description="NAPOLCOM OMR Template Generator")
    parser.add_argument("input", help="Input image file (blank form)")
    parser.add_argument("output", help="Output template JSON file")
    
    args = parser.parse_args()
    
    try:
        generate_template(args.input, args.output)
    except Exception as e:
        print(f"Error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())
