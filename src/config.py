"""
Configuration parameters for the OMR processor
"""

# Basic configuration
DEBUG_MODE = False
DEFAULT_OUTPUT_DIR = "results"

# Image preprocessing parameters
RESIZE_WIDTH = 1000  # Width to resize images to for processing

# ROI coordinates for different fields
# These need to be calibrated for the specific form layout
ROI_COORDINATES = {
    "booklet_number": {"x": 207, "y": 143, "width": 285, "height": 30},
    "date_of_exam": {"x": 207, "y": 166, "width": 285, "height": 30},
    "date_of_birth": {"x": 207, "y": 188, "width": 285, "height": 30},
    "surname": {"x": 40, "y": 220, "width": 540, "height": 30},
    "first_name": {"x": 40, "y": 261, "width": 540, "height": 30},
    "middle_name": {"x": 40, "y": 303, "width": 540, "height": 30},
    "set_type": {"x": 452, "y": 138, "width": 50, "height": 50},
    "application_number": {"x": 690, "y": 177, "width": 125, "height": 183}
}

# Answer section coordinates
ANSWER_SECTIONS = [
    {"start_q": 1, "end_q": 30, "x": 155, "y": 453, "width": 125, "height": 587},
    {"start_q": 31, "end_q": 60, "x": 282, "y": 453, "width": 125, "height": 587},
    {"start_q": 61, "end_q": 90, "x": 409, "y": 453, "width": 125, "height": 587},
    {"start_q": 91, "end_q": 120, "x": 536, "y": 453, "width": 125, "height": 587},
    {"start_q": 121, "end_q": 150, "x": 663, "y": 453, "width": 125, "height": 587}
]

# Set type bubble positions
SET_TYPE_BUBBLES = {
    "A": {"center_x": 15, "center_y": 15, "radius": 10},
    "B": {"center_x": 15, "center_y": 27, "radius": 10},
    "C": {"center_x": 15, "center_y": 39, "radius": 10}
}

# Thresholds for bubble detection
BUBBLE_FILL_THRESHOLD = 0.5  # Minimum fill percentage to consider a bubble filled
MIN_BUBBLE_AREA = 20  # Minimum area for a bubble contour
MAX_BUBBLE_AREA = 200  # Maximum area for a bubble contour

# Application number parameters
APP_NUMBER_COLUMNS = 11  # Number of columns in the application number grid
APP_NUMBER_ROWS = 10  # Number of rows (digits 0-9)

# Answer bubble parameters
NUM_OPTIONS_PER_QUESTION = 5  # Number of options per question (A-E or 1-5)
TOTAL_QUESTIONS = 150  # Total number of questions
