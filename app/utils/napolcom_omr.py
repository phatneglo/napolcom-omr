import os
import cv2
import numpy as np
from pathlib import Path

# When the signature rectangle is identified, we will do a perspective
# transform to get a properly aligned view of the answer sheet
TRANSF_SIZE = 2000  # Higher resolution for better detail

#
# Answer sheet properties for NAPOLCOM format
#
N_QUESTIONS = 150
N_COLUMNS = 5
QUESTIONS_PER_COLUMN = 30
N_OPTIONS = 5

# Adjusted constants for NAPOLCOM sheet dimensions
ANSWER_SHEET_WIDTH = 2000
ANSWER_SHEET_HEIGHT = 2800

# Positions based on normalized coordinates
QUESTIONS_TOP = 0.15  # Where questions start vertically
QUESTIONS_BOTTOM = 0.85  # Where questions end vertically
SIGNATURE_BOX_TOP = 0.87  # Where signature box starts
SIGNATURE_BOX_BOTTOM = 0.94  # Where signature box ends
SIGNATURE_BOX_LEFT = 0.25  # Left side of signature box relative to page width
SIGNATURE_BOX_RIGHT = 0.75  # Right side of signature box relative to page width

# Column positioning
COLUMN_STARTS = [0.05, 0.25, 0.45, 0.65, 0.85]  # Start positions for each column
COLUMN_WIDTHS = 0.15  # Width of each column

def normalize(img):
    """Converts image to black and white for easier processing"""
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(img_gray, (5, 5), 0)
    # Apply adaptive thresholding with more sensitivity
    return cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 51, 9)  # Adjusted parameters

def find_signature_box(img):
    """Find the signature box at the bottom of the NAPOLCOM answer sheet"""
    img_height, img_width = img.shape[:2]
    
    # Create a copy of the image for rectangle detection
    img_copy = img.copy()
    
    # Focus on bottom part of the image where signature box is
    bottom_region = img_copy[int(img_height * 0.8):, :]
    
    # Convert to grayscale if not already
    if len(bottom_region.shape) == 3:
        bottom_gray = cv2.cvtColor(bottom_region, cv2.COLOR_BGR2GRAY)
    else:
        bottom_gray = bottom_region
    
    # Apply threshold to highlight the box
    _, thresh = cv2.threshold(bottom_gray, 200, 255, cv2.THRESH_BINARY_INV)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Look for the signature box - typically a large rectangular contour
    signature_contours = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        # Calculate aspect ratio and area to identify the signature box
        aspect_ratio = float(w) / h
        area = w * h
        area_ratio = area / (bottom_region.shape[0] * bottom_region.shape[1])
        
        # The signature box should be a large rectangle with specific aspect ratio
        if 2.0 < aspect_ratio < 6.0 and 0.05 < area_ratio < 0.3:
            # Adjust y coordinate to account for the bottom region crop
            y += int(img_height * 0.8)
            signature_contours.append((x, y, w, h, contour))
    
    # If signature box is found, return the best match
    if signature_contours:
        # Sort by area (larger is more likely to be the signature box)
        signature_contours.sort(key=lambda x: x[2] * x[3], reverse=True)
        x, y, w, h, contour = signature_contours[0]
        
        # Get the four corners of the signature box
        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        
        # Adjust y coordinates to account for the bottom region crop
        for i in range(len(box)):
            box[i][1] += int(img_height * 0.8)
        
        return box
    
    # If no signature box is found, try to estimate its position
    print("Warning: Signature box not detected, estimating position")
    
    # Estimate signature box position based on sheet dimensions
    left = int(img_width * SIGNATURE_BOX_LEFT)
    right = int(img_width * SIGNATURE_BOX_RIGHT)
    top = int(img_height * SIGNATURE_BOX_TOP)
    bottom = int(img_height * SIGNATURE_BOX_BOTTOM)
    
    # Return the four corners of the estimated box
    return np.array([
        [left, top],
        [right, top],
        [right, bottom],
        [left, bottom]
    ])

def get_sheet_corners(img, signature_box):
    """Determine the four corners of the answer sheet based on the signature box"""
    height, width = img.shape[:2]
    
    # Estimate the full sheet corners based on the signature box position
    # This assumes the signature box is positioned consistently on the page
    
    # Calculate signature box dimensions and center
    signature_points = np.array(signature_box)
    sig_left = np.min(signature_points[:, 0])
    sig_right = np.max(signature_points[:, 0])
    sig_top = np.min(signature_points[:, 1])
    sig_bottom = np.max(signature_points[:, 1])
    
    sig_width = sig_right - sig_left
    sig_height = sig_bottom - sig_top
    
    # Calculate page corners based on the signature box position
    # These proportions are based on the NAPOLCOM answer sheet layout
    
    # Estimate the full width of the page from the signature box
    full_width = sig_width / (SIGNATURE_BOX_RIGHT - SIGNATURE_BOX_LEFT)
    
    # Find left and right edges of full page
    left_edge = sig_left - (SIGNATURE_BOX_LEFT * full_width)
    right_edge = sig_left + ((1 - SIGNATURE_BOX_LEFT) * full_width)
    
    # Estimate the full height of the page from the signature box
    full_height = sig_top / SIGNATURE_BOX_TOP
    
    # Top and bottom edges
    top_edge = 0
    bottom_edge = full_height
    
    # Adjust if calculated edges are outside the image bounds
    left_edge = max(0, min(width - 1, left_edge))
    right_edge = max(0, min(width - 1, right_edge))
    top_edge = max(0, min(height - 1, top_edge))
    bottom_edge = max(0, min(height - 1, bottom_edge))
    
    # Return the four corners of the sheet
    return np.array([
        [left_edge, top_edge],  # Top-left
        [right_edge, top_edge],  # Top-right
        [right_edge, bottom_edge],  # Bottom-right
        [left_edge, bottom_edge]  # Bottom-left
    ], dtype=np.int32)

def perspective_transform(img, corners):
    """Apply perspective transform to get a properly aligned view of the answer sheet"""
    # Order the corners: top-left, top-right, bottom-right, bottom-left
    # Sort points based on x coordinates (left to right)
    sorted_x = corners[np.argsort(corners[:, 0])]
    
    # Separate left and right points
    left_points = sorted_x[:2]
    right_points = sorted_x[2:]
    
    # Sort each group by y coordinate (top to bottom)
    left_points = left_points[np.argsort(left_points[:, 1])]
    right_points = right_points[np.argsort(right_points[:, 1])]
    
    # Combine into ordered corners: top-left, top-right, bottom-right, bottom-left
    ordered_corners = np.array([
        left_points[0],   # top-left
        right_points[0],  # top-right
        right_points[1],  # bottom-right
        left_points[1]    # bottom-left
    ], dtype=np.float32)
    
    # Define the destination points for the transform
    dst = np.array([
        [0, 0],
        [TRANSF_SIZE, 0],
        [TRANSF_SIZE, TRANSF_SIZE],
        [0, TRANSF_SIZE]
    ], dtype=np.float32)
    
    # Compute the perspective transform matrix
    M = cv2.getPerspectiveTransform(ordered_corners, dst)
    
    # Apply the transform
    warped = cv2.warpPerspective(img, M, (TRANSF_SIZE, TRANSF_SIZE))
    
    return warped



def extract_questions_area(transformed_img):
    """Extract the area containing the answer bubbles"""
    height, width = transformed_img.shape[:2]
    
    # Define questions area based on normalized coordinates
    top = int(height * QUESTIONS_TOP)
    bottom = int(height * QUESTIONS_BOTTOM)
    
    # Extract the region containing all questions
    questions_area = transformed_img[top:bottom, :]
    
    return questions_area

def extract_answer_grid(questions_area):
    """Extract the grid of answer bubbles"""
    height, width = questions_area.shape[:2]
    
    # Adjust column positions for better accuracy
    adjusted_starts = [0.05, 0.25, 0.45, 0.65, 0.85]  # Fine-tuned column starts
    adjusted_widths = 0.17  # Slightly wider to ensure bubbles are captured
    
    # Divide the area into 5 columns
    columns = []
    for i in range(N_COLUMNS):
        left = int(width * adjusted_starts[i])
        right = int(left + width * adjusted_widths)
        column = questions_area[:, left:right]
        columns.append(column)
        
        # Add debug visualization - draw column boundaries
        if i > 0:  # Skip first column's left boundary
            cv2.line(questions_area, (left, 0), (left, height), (0, 255, 0), 1)
    
    return columns

def analyze_bubble(bubble, debug_col=None, pos=None):
    """Analyze a single bubble to determine if it's filled by examining pixel by pixel"""
    # Convert to grayscale if not already
    if len(bubble.shape) == 3:
        bubble_gray = cv2.cvtColor(bubble, cv2.COLOR_BGR2GRAY)
    else:
        bubble_gray = bubble
    
    # Get dimensions
    h, w = bubble_gray.shape[:2]
    
    # Calculate statistics from the center of the bubble
    center_area = bubble_gray[int(h*0.2):int(h*0.8), int(w*0.2):int(w*0.8)]
    
    if center_area.size > 0:
        # Calculate mean and standard deviation of center area
        mean_val = np.mean(center_area)
        std_val = np.std(center_area)
        
        # Count dark pixels (pixels below threshold)
        dark_threshold = 170  # Lowered threshold for more sensitivity
        dark_pixels = np.sum(center_area < dark_threshold)
        dark_ratio = dark_pixels / center_area.size
        
        # For debugging
        if debug_col is not None and pos is not None:
            left, top = pos
            text_pos = (left + 5, top + int(h/2))
            cv2.putText(debug_col, f"{mean_val:.0f}", text_pos, cv2.FONT_HERSHEY_PLAIN, 0.7, (0, 255, 255), 1)
        
        # Multiple checks for bubble filling:
        # 1. Mean darkness check - lower values mean darker overall
        # 2. Dark pixel ratio check - higher values mean more dark pixels
        # 3. Standard deviation check - higher values suggest markings (variation)
        is_filled = (mean_val < 170 or dark_ratio > 0.2 or (std_val > 30 and mean_val < 200))
        
        return is_filled
    
    return False

def process_column(column, start_question):
    """Process a single column of questions"""
    height, width = column.shape[:2]
    
    # Calculate grid parameters with adjusted spacing
    row_height = height / QUESTIONS_PER_COLUMN
    bubble_width = width / (N_OPTIONS + 0.5)  # Add some spacing to exclude question numbers
    
    # Debug visualization
    debug_col = column.copy() if len(column.shape) == 3 else cv2.cvtColor(column, cv2.COLOR_GRAY2BGR)
    
    answers = []
    
    # Process each question in the column
    for q in range(QUESTIONS_PER_COLUMN):
        question_answers = []
        question_number = start_question + q
        
        # Skip if question number is beyond our total
        if question_number > N_QUESTIONS:
            break
        
        # Define the row for this question with tight focus on bubbles
        mid_y = int((q + 0.5) * row_height)  # Center of the row
        row_margin = int(row_height * 0.3)  # Smaller area focused on bubbles
        top = mid_y - row_margin
        bottom = mid_y + row_margin
        
        # Debug - draw row boundaries
        cv2.line(debug_col, (0, top), (width, top), (0, 0, 255), 1)
        cv2.line(debug_col, (0, bottom), (width, bottom), (0, 0, 255), 1)
        
        # Draw question number for reference
        cv2.putText(debug_col, f"{question_number}", (5, mid_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        
        # Process each option (A, B, C, D, E)
        for option in range(N_OPTIONS):
            # Start a bit to the right to skip question number area
            offset = int(width * 0.2)  # Skip the question number area
            option_spacing = (width - offset) / N_OPTIONS
            left = offset + int(option * option_spacing)
            right = left + int(option_spacing * 0.7)  # Make bubble area slightly smaller
            
            # Ensure the boundaries are valid
            if top < 0 or bottom >= height or left < 0 or right >= width:
                question_answers.append(False)
                continue
                
            # Extract the bubble
            bubble = column[top:bottom, left:right]
            
            # Draw debug rectangle around bubble
            cv2.rectangle(debug_col, (left, top), (right, bottom), (255, 0, 0), 1)
            
            # Add option letter for reference
            option_letter = chr(65 + option)  # A, B, C, D, E
            cv2.putText(debug_col, option_letter, (left + 5, top - 5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            
            # Check if the bubble is filled
            filled = analyze_bubble(bubble, debug_col, (left, top))
            
            if filled:
                # Mark detected bubbles
                cv2.rectangle(debug_col, (left, top), (right, bottom), (0, 255, 0), 2)
                # Add 'FILLED' text
                cv2.putText(debug_col, "FILL", (left + 5, bottom - 5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
            
            question_answers.append(filled)
        
        # Find the marked answer (if any)
        marked = None
        for i, filled in enumerate(question_answers):
            if filled:
                if marked is not None:
                    # Multiple answers - consider invalid
                    marked = -1
                else:
                    marked = i
        
        answers.append((question_number, marked))
    
    return answers, debug_col

def interpret_answer(answer_index):
    """Convert numeric answer index to letter (A, B, C, D, E)"""
    if answer_index is None or answer_index == -1:
        return "N/A"
    return chr(65 + answer_index)  # 65 is ASCII for 'A'

def get_answers(image_path):
    """Process the NAPOLCOM answer sheet and return marked answers"""
    # Load the image
    original_img = cv2.imread(image_path)
    if original_img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    # Create a copy for visualization
    visual_img = original_img.copy()
    
    # Create a normalized (binary) version for processing
    normalized_img = normalize(original_img)
    
    # Also create an enhanced version for better bubble detection
    # Increase contrast to make markings more visible
    enhanced_img = original_img.copy()
    enhanced_gray = cv2.cvtColor(enhanced_img, cv2.COLOR_BGR2GRAY)
    enhanced_gray = cv2.equalizeHist(enhanced_gray)  # Enhance contrast
    
    # Find the signature box for alignment
    signature_box = find_signature_box(normalized_img)
    
    # Draw the signature box on the visual image
    cv2.drawContours(visual_img, [signature_box], 0, (0, 255, 0), 3)
    
    # Get the full sheet corners based on the signature box
    sheet_corners = get_sheet_corners(original_img, signature_box)
    
    # Draw the sheet corners on the visual image
    cv2.drawContours(visual_img, [sheet_corners], 0, (0, 0, 255), 3)
    
    # Apply perspective transform to get a properly aligned view
    transformed_orig = perspective_transform(original_img, sheet_corners)
    transformed_norm = perspective_transform(normalized_img, sheet_corners)
    transformed_enhanced = perspective_transform(enhanced_gray, sheet_corners)
    
    # Convert enhanced image back to BGR for visualization
    transformed_enhanced_bgr = cv2.cvtColor(transformed_enhanced, cv2.COLOR_GRAY2BGR)
    
    # Extract the questions area
    questions_area_orig = extract_questions_area(transformed_orig)
    questions_area_norm = extract_questions_area(transformed_norm)
    questions_area_enhanced = extract_questions_area(transformed_enhanced_bgr)
    
    # Choose the enhanced version for processing
    processing_image = questions_area_enhanced
    
    # Extract answer columns
    columns_orig = extract_answer_grid(questions_area_orig.copy())
    columns_proc = extract_answer_grid(processing_image.copy())
    
    # Process each column
    all_answers = []
    debug_cols = []
    
    for i in range(N_COLUMNS):
        start_question = i * QUESTIONS_PER_COLUMN + 1
        answers, debug_col = process_column(columns_proc[i], start_question)
        all_answers.extend(answers)
        debug_cols.append(debug_col)
    
    # Sort answers by question number
    all_answers.sort(key=lambda x: x[0])
    
    # Convert to readable format
    readable_answers = []
    for question, answer in all_answers:
        letter = interpret_answer(answer)
        readable_answers.append(f"Q{question}: {letter}")
    
    # Add debug visualization - replace original columns with debug versions
    h, w = questions_area_orig.shape[:2]
    for i in range(N_COLUMNS):
        # Calculate column position
        left = int(w * COLUMN_STARTS[i])
        debug_col = debug_cols[i]
        dh, dw = debug_col.shape[:2]
        
        # Place debug column in original image
        if left + dw <= w and dh <= h:
            questions_area_orig[:dh, left:left+dw] = debug_col
    
    # Create final image with debug markings
    final_vis_img = transformed_orig.copy()
    h_q, w_q = questions_area_orig.shape[:2]
    top = int(TRANSF_SIZE * QUESTIONS_TOP)
    final_vis_img[top:top+h_q, :w_q] = questions_area_orig
    
    # Add answer summary to the image
    summary_y = top + h_q + 30
    for i, (question, answer) in enumerate(all_answers[:20]):  # Show first 20 answers
        letter = interpret_answer(answer)
        text = f"Q{question}: {letter}"
        cv2.putText(final_vis_img, text, (50 + (i % 5) * 100, summary_y + (i // 5) * 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    
    return readable_answers, final_vis_img

if __name__ == "__main__":
    # Test on a sample image
    sample_path = "path/to/sample/image.jpg"
    if os.path.exists(sample_path):
        answers, marked_image = get_answers(sample_path)
        for answer in answers:
            print(answer)
        
        # Display or save the marked image
        cv2.imshow("Marked Answer Sheet", marked_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print(f"Sample image not found: {sample_path}")
