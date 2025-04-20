# NAPOLCOM OMR Scanner

This is a FastAPI implementation of an Optical Mark Recognition (OMR) system for NAPOLCOM (National Police Commission) exam answer sheets. It provides a web interface for scanning and processing OMR answer sheets, based on the [rbaron/omr](https://github.com/rbaron/omr) project but extended with special support for NAPOLCOM exam sheets.

## Features

- Upload and process photos of completed answer sheets
- Support for NAPOLCOM exam sheets (150 questions, 5 options each)
- Support for original OMR format (10 questions, 5 options each) 
- Automatically detect marked answers
- Display processed image with annotations
- Download blank answer sheet templates
- Export results as text files

## Installation

### Prerequisites

- Python 3.7+
- pip
- Virtual environment (recommended)

### Setup

1. Clone this repository:

```bash
git clone https://github.com/yourusername/napolcom-omr.git
cd napolcom-omr
```

2. Create and activate a virtual environment:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:

```bash
python run.py
```

2. Open your browser and navigate to http://localhost:8000

3. Download the answer sheet template, print it, and fill in your answers

4. Take a photo of the completed answer sheet

5. Upload the photo to the web interface

6. View the detected answers

## Project Structure

```
napolcom-omr/
├── app/
│   ├── main.py                    # FastAPI application
│   ├── static/                    # Static files
│   │   └── img/                   # Images (corner.png, answer sheets)
│   ├── templates/                 # HTML templates
│   │   ├── index.html            # Upload page
│   │   ├── result.html           # Results page
│   │   └── error.html            # Error page
│   ├── uploads/                  # Uploaded images
│   └── utils/                    # Utility modules
│       ├── omr.py                # Original OMR processing code
│       ├── napolcom_omr.py       # NAPOLCOM sheet processing
│       ├── generate_sheet.py     # Original sheet generator
│       └── generate_napolcom_sheet.py  # NAPOLCOM sheet generator
├── requirements.txt              # Dependencies
├── run.py                        # Application entry point
├── setup.bat                     # Setup script
├── start.bat                     # Start script
└── README.md                     # This file
```

## How It Works

### NAPOLCOM Sheet Processing:
1. The system identifies the signature box at the bottom of the sheet
2. It uses the signature box to determine the perspective and alignment of the sheet
3. The system transforms the sheet to a standard perspective/orientation
4. It extracts the grid of questions and options (150 questions, 5 columns)
5. For each bubble, it analyzes the percentage of filled (dark) pixels
6. Results are displayed with annotations on the processed image

### Original OMR Sheet Processing:
1. The system looks for four corner marks on the answer sheet to align the image
2. It extracts the regions where answers should be marked
3. For each question, it analyzes the darkness of each option bubble
4. The darkest bubble (if sufficiently darker than others) is considered marked
5. Results are displayed with annotations on the processed image

## Customization

You can customize the answer sheet layout by modifying the constants in `app/utils/generate_sheet.py` and `app/utils/omr.py`.

## Credits

This project is based on [rbaron/omr](https://github.com/rbaron/omr), which provides the core OMR functionality. The original implementation was refactored and extended with a FastAPI web interface.

## License

MIT License - see the original project for details.
