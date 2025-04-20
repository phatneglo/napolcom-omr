import cv2
import numpy as np
from pathlib import Path

# Constants for sheet generation
SHEET_WIDTH = 740
SHEET_HEIGHT = 1049  # A4 aspect ratio in portrait
MARGIN = 50
CORNER_SIZE = 30
LINE_THICKNESS = 2
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.6
FONT_THICKNESS = 2
FONT_COLOR = (0, 0, 0)

# Answer sheet properties
NUM_QUESTIONS = 10
NUM_OPTIONS = 5
CIRCLE_RADIUS = 10
CIRCLE_SPACING = 60
QUESTION_SPACING = 70
OPTION_LETTERS = ['A', 'B', 'C', 'D', 'E']

def create_blank_answer_sheet(output_path):
    """Creates a blank answer sheet and saves it to the specified path."""
    # Create a white image
    sheet = np.ones((SHEET_HEIGHT, SHEET_WIDTH, 3), dtype=np.uint8) * 255
    
    # Draw the corners
    # Top-left corner
    cv2.rectangle(sheet, (MARGIN, MARGIN), (MARGIN + CORNER_SIZE, MARGIN + CORNER_SIZE), (0, 0, 0), -1)
    # Top-right corner
    cv2.rectangle(sheet, (SHEET_WIDTH - MARGIN - CORNER_SIZE, MARGIN), 
                 (SHEET_WIDTH - MARGIN, MARGIN + CORNER_SIZE), (0, 0, 0), -1)
    # Bottom-left corner
    cv2.rectangle(sheet, (MARGIN, SHEET_HEIGHT - MARGIN - CORNER_SIZE), 
                 (MARGIN + CORNER_SIZE, SHEET_HEIGHT - MARGIN), (0, 0, 0), -1)
    # Bottom-right corner
    cv2.rectangle(sheet, (SHEET_WIDTH - MARGIN - CORNER_SIZE, SHEET_HEIGHT - MARGIN - CORNER_SIZE), 
                 (SHEET_WIDTH - MARGIN, SHEET_HEIGHT - MARGIN), (0, 0, 0), -1)
    
    # Draw title
    title = "OMR ANSWER SHEET"
    title_size = cv2.getTextSize(title, FONT, FONT_SCALE * 2, FONT_THICKNESS * 2)
    title_width = title_size[0][0]
    title_x = (SHEET_WIDTH - title_width) // 2
    cv2.putText(sheet, title, (title_x, MARGIN * 2), FONT, FONT_SCALE * 2, FONT_COLOR, FONT_THICKNESS * 2)
    
    # Draw instructions
    instructions = "Fill in the bubble completely for your answer. Erase all marks completely if you change your answer."
    instr_size = cv2.getTextSize(instructions, FONT, FONT_SCALE, FONT_THICKNESS)
    instr_width = instr_size[0][0]
    instr_x = (SHEET_WIDTH - instr_width) // 2
    cv2.putText(sheet, instructions, (instr_x, MARGIN * 3), FONT, FONT_SCALE, FONT_COLOR, FONT_THICKNESS)
    
    # Starting position for questions
    start_y = MARGIN * 4
    
    # Draw questions and answer options
    for q in range(1, NUM_QUESTIONS + 1):
        q_y = start_y + QUESTION_SPACING * (q - 1)
        
        # Draw question number
        q_text = f"Q{q}."
        cv2.putText(sheet, q_text, (MARGIN * 2, q_y + 10), FONT, FONT_SCALE, FONT_COLOR, FONT_THICKNESS)
        
        # Draw options for this question
        for opt in range(NUM_OPTIONS):
            opt_x = MARGIN * 4 + CIRCLE_SPACING * opt
            
            # Draw option circle
            cv2.circle(sheet, (opt_x, q_y), CIRCLE_RADIUS, (0, 0, 0), 1)
            
            # Draw option letter
            letter_size = cv2.getTextSize(OPTION_LETTERS[opt], FONT, FONT_SCALE, FONT_THICKNESS)
            letter_x = opt_x - letter_size[0][0] // 2
            letter_y = q_y - CIRCLE_RADIUS - 5
            cv2.putText(sheet, OPTION_LETTERS[opt], (letter_x, letter_y), FONT, FONT_SCALE, FONT_COLOR, FONT_THICKNESS)
    
    # Save the sheet
    cv2.imwrite(output_path, sheet)
    return sheet

def main():
    # Get the path to save the answer sheet
    base_dir = Path(__file__).resolve().parent.parent
    output_dir = base_dir / "static" / "img"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Create and save the answer sheet
    output_path = output_dir / "answer-sheet.png"
    create_blank_answer_sheet(str(output_path))
    
    # Also create corner image
    corner_path = output_dir / "corner.png"
    corner = np.ones((100, 100, 3), dtype=np.uint8) * 255
    cv2.rectangle(corner, (35, 35), (65, 65), (0, 0, 0), -1)
    cv2.imwrite(str(corner_path), corner)
    
    print(f"Answer sheet created at {output_path}")
    print(f"Corner image created at {corner_path}")
    
    # Convert to PDF
    try:
        from PIL import Image
        img = Image.open(output_path)
        pdf_path = output_dir / "answer-sheet.pdf"
        img.save(pdf_path)
        print(f"PDF version created at {pdf_path}")
    except Exception as e:
        print(f"Could not create PDF version: {e}")
        print("You'll need to install Pillow: pip install pillow")

if __name__ == "__main__":
    main()
