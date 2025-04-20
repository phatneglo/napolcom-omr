#!/usr/bin/env python3
"""
Simple test script to debug the NumPy array error.
"""

import cv2
import numpy as np
import os
import traceback

# Create output directory
os.makedirs("debug_output", exist_ok=True)

def process_image(image_path):
    """Process an image and find issues."""
    print(f"Processing {image_path}...")
    
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        print(f"Failed to load image: {image_path}")
        return
    
    print(f"Image loaded, shape: {img.shape}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply threshold
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    cv2.imwrite("debug_output/threshold.jpg", thresh)
    
    # Find contours - this is where the error likely occurs
    try:
        print("Finding contours...")
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"Found {len(contours)} contours")
        
        # Check if we have any contours
        if len(contours) > 0:
            # Find largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            print(f"Largest contour area: {cv2.contourArea(largest_contour)}")
            
            # Approximate contour
            peri = cv2.arcLength(largest_contour, True)
            approx = cv2.approxPolyDP(largest_contour, 0.02 * peri, True)
            print(f"Approximated contour has {len(approx)} points")
            
            # Draw the contour
            contour_img = img.copy()
            cv2.drawContours(contour_img, [approx], -1, (0, 255, 0), 2)
            cv2.imwrite("debug_output/contour.jpg", contour_img)
            
            # Check if we have a quadrilateral
            if len(approx) == 4:
                # Process as quadrilateral
                print("Found quadrilateral, processing...")
                
                # Get perspective transform
                # First order points
                rect = np.zeros((4, 2), dtype=np.float32)
                pts = approx.reshape(4, 2)
                
                s = pts.sum(axis=1)
                rect[0] = pts[np.argmin(s)]  # Top-left
                rect[2] = pts[np.argmax(s)]  # Bottom-right
                
                diff = np.diff(pts, axis=1)
                rect[1] = pts[np.argmin(diff)]  # Top-right
                rect[3] = pts[np.argmax(diff)]  # Bottom-left
                
                # Define destination points
                dst_pts = np.array([
                    [0, 0],
                    [500, 0],
                    [500, 700],
                    [0, 700]
                ], dtype=np.float32)
                
                # Get transform matrix
                M = cv2.getPerspectiveTransform(rect, dst_pts)
                
                # Apply transform
                warped = cv2.warpPerspective(img, M, (500, 700))
                cv2.imwrite("debug_output/warped.jpg", warped)
                print("Warping successful")
            else:
                print(f"Not a quadrilateral: {len(approx)} points")
        else:
            print("No contours found")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
    
    print("Processing complete")

if __name__ == "__main__":
    # Check if we have an uploaded image
    if os.path.exists("uploads"):
        uploaded_files = [f for f in os.listdir("uploads") if f.endswith((".jpg", ".jpeg", ".png"))]
        
        if uploaded_files:
            # Process the first uploaded image
            process_image(os.path.join("uploads", uploaded_files[0]))
        else:
            print("No uploaded images found")
    else:
        print("Uploads directory not found")
