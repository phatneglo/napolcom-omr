import cv2
import numpy as np
from pathlib import Path
import os

# Constants for sheet generation
SHEET_WIDTH = 2100
SHEET_HEIGHT = 2970  # A4 paper in portrait orientation
MARGIN = 80
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.7
FONT_SMALL = 0.5
FONT_LARGE = 1.0
FONT_COLOR = (0, 0, 0)
FONT_THICKNESS = 1

# Answer sheet properties
N_QUESTIONS = 150
N_COLUMNS = 5
QUESTIONS_PER_COLUMN = 30
N_OPTIONS = 5
OPTION_LETTERS = ['1', '2', '3', '4', '5']
BUBBLE_RADIUS = 12
BUBBLE_SPACING_H = 40
BUBBLE_SPACING_V = 30
COLUMN_WIDTH = 380

def create_napolcom_answer_sheet(output_path):
    """Creates a blank NAPOLCOM answer sheet and saves it to the specified path."""
    # Create a white image
    sheet = np.ones((SHEET_HEIGHT, SHEET_WIDTH, 3), dtype=np.uint8) * 255
    
    # Add logo and header text
    logo_x = MARGIN
    logo_y = MARGIN
    logo_size = 120
    # Draw a circle as placeholder for logo
    cv2.circle(sheet, (logo_x + logo_size//2, logo_y + logo_size//2), logo_size//2, (200, 200, 200), 2)
    
    # Add header text
    header_text = "NATIONAL POLICE COMMISSION"
    subheader_text = "Examination Answer Sheet"
    
    header_x = logo_x + logo_size + 50
    header_y = logo_y + 50
    
    cv2.putText(sheet, header_text, (header_x, header_y), FONT, FONT_LARGE, FONT_COLOR, 2)
    cv2.putText(sheet, subheader_text, (header_x, header_y + 40), FONT, FONT_SCALE, FONT_COLOR, 1)
    
    # Add form fields
    field_y = logo_y + logo_size + 30
    
    # Test Booklet Number
    cv2.putText(sheet, "Test Booklet Number", (MARGIN, field_y), FONT, FONT_SCALE, FONT_COLOR, 1)
    # Draw boxes for Test Booklet Number
    for i in range(6):
        cv2.rectangle(sheet, (MARGIN + 220 + i*40, field_y - 25), (MARGIN + 220 + (i+1)*40, field_y + 15), (0, 0, 0), 1)
    
    # Set Type
    cv2.putText(sheet, "Set Type", (MARGIN + 500, field_y), FONT, FONT_SCALE, FONT_COLOR, 1)
    # Draw circles for Set Type (A, B, C)
    for i, letter in enumerate(['A', 'B', 'C']):
        cv2.circle(sheet, (MARGIN + 600 + i*60, field_y - 5), 15, (0, 0, 0), 1)
        cv2.putText(sheet, letter, (MARGIN + 595 + i*60, field_y), FONT, FONT_SMALL, FONT_COLOR, 1)
    
    # Application Number
    cv2.putText(sheet, "Application Number", (MARGIN + 800, field_y), FONT, FONT_SCALE, FONT_COLOR, 1)
    # Draw boxes for Application Number
    for i in range(12):
        cv2.rectangle(sheet, (MARGIN + 1000 + i*40, field_y - 25), (MARGIN + 1000 + (i+1)*40, field_y + 15), (0, 0, 0), 1)
    
    # Date of Exam
    field_y += 50
    cv2.putText(sheet, "Date of Exam (mm/dd/yyyy)", (MARGIN, field_y), FONT, FONT_SCALE, FONT_COLOR, 1)
    # Draw boxes for Date
    for i in range(8):
        cv2.rectangle(sheet, (MARGIN + 220 + i*40, field_y - 25), (MARGIN + 220 + (i+1)*40, field_y + 15), (0, 0, 0), 1)
    
    # Date of Birth
    field_y += 50
    cv2.putText(sheet, "Date of Birth (mm/dd/yyyy)", (MARGIN, field_y), FONT, FONT_SCALE, FONT_COLOR, 1)
    # Draw boxes for Date
    for i in range(8):
        cv2.rectangle(sheet, (MARGIN + 220 + i*40, field_y - 25), (MARGIN + 220 + (i+1)*40, field_y + 15), (0, 0, 0), 1)
    
    # Number grid (for the form fields)
    grid_y = field_y + 70
    grid_x = MARGIN + 550
    
    # Draw grid numbers (0-9)
    for row in range(10):
        for col in range(10):
            digit = str((row + col) % 10)
            circle_x = grid_x + col * 40
            circle_y = grid_y + row * 40
            
            cv2.circle(sheet, (circle_x, circle_y), 15, (0, 0, 0), 1)
            cv2.putText(sheet, digit, (circle_x - 5, circle_y + 5), FONT, FONT_SMALL, FONT_COLOR, 1)
    
    # Name fields
    name_y = field_y + 50
    
    # Surname
    cv2.putText(sheet, "Surname", (MARGIN, name_y), FONT, FONT_SCALE, FONT_COLOR, 1)
    # Draw boxes for Surname (20 boxes)
    for i in range(20):
        cv2.rectangle(sheet, (MARGIN + 120 + i*35, name_y - 25), (MARGIN + 120 + (i+1)*35, name_y + 15), (0, 0, 0), 1)
    
    # First Name
    name_y += 50
    cv2.putText(sheet, "First Name", (MARGIN, name_y), FONT, FONT_SCALE, FONT_COLOR, 1)
    # Draw boxes for First Name (20 boxes)
    for i in range(20):
        cv2.rectangle(sheet, (MARGIN + 120 + i*35, name_y - 25), (MARGIN + 120 + (i+1)*35, name_y + 15), (0, 0, 0), 1)
    
    # Middle Name
    name_y += 50
    cv2.putText(sheet, "Middle Name", (MARGIN, name_y), FONT, FONT_SCALE, FONT_COLOR, 1)
    # Draw boxes for Middle Name (20 boxes)
    for i in range(20):
        cv2.rectangle(sheet, (MARGIN + 120 + i*35, name_y - 25), (MARGIN + 120 + (i+1)*35, name_y + 15), (0, 0, 0), 1)
    
    # Answer bubble section
    answer_section_y = name_y + 100
    
    # Add column headers (1-5, 1-5, etc. for each column)
    for col in range(N_COLUMNS):
        col_x = MARGIN + col * COLUMN_WIDTH
        
        # Draw option numbers (1-5)
        for opt in range(N_OPTIONS):
            opt_x = col_x + opt * BUBBLE_SPACING_H + BUBBLE_SPACING_H
            cv2.putText(sheet, OPTION_LETTERS[opt], (opt_x - 5, answer_section_y), FONT, FONT_SCALE, FONT_COLOR, 1)
    
    # Draw question numbers and bubbles
    for col in range(N_COLUMNS):
        col_x = MARGIN + col * COLUMN_WIDTH
        col_start_q = col * QUESTIONS_PER_COLUMN + 1
        
        for q in range(QUESTIONS_PER_COLUMN):
            q_num = col_start_q + q
            q_y = answer_section_y + 40 + q * BUBBLE_SPACING_V
            
            # Question number
            cv2.putText(sheet, str(q_num), (col_x, q_y + 5), FONT, FONT_SCALE, FONT_COLOR, 1)
            
            # Draw bubbles for this question
            for opt in range(N_OPTIONS):
                opt_x = col_x + opt * BUBBLE_SPACING_H + BUBBLE_SPACING_H
                cv2.circle(sheet, (opt_x, q_y), BUBBLE_RADIUS, (0, 0, 0), 1)
    
    # Add signature box at the bottom
    sig_box_y = SHEET_HEIGHT - MARGIN - 100
    sig_box_width = SHEET_WIDTH - 2 * MARGIN * 2
    sig_box_height = 80
    
    cv2.rectangle(sheet, 
                 (MARGIN*2, sig_box_y), 
                 (SHEET_WIDTH - MARGIN*2, sig_box_y + sig_box_height), 
                 (0, 0, 0), 1)
    
    # Save the sheet
    cv2.imwrite(output_path, sheet)
    return sheet

def main():
    # Get the path to save the answer sheet
    base_dir = Path(__file__).resolve().parent.parent
    output_dir = base_dir / "static" / "img"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Create and save the answer sheet
    output_path = output_dir / "napolcom-answer-sheet.png"
    create_napolcom_answer_sheet(str(output_path))
    
    print(f"NAPOLCOM Answer sheet created at {output_path}")
    
    # Convert to PDF
    try:
        from PIL import Image
        img = Image.open(output_path)
        pdf_path = output_dir / "napolcom-answer-sheet.pdf"
        img.save(pdf_path)
        print(f"PDF version created at {pdf_path}")
    except Exception as e:
        print(f"Could not create PDF version: {e}")
        print("You'll need to install Pillow: pip install pillow")

if __name__ == "__main__":
    main()
