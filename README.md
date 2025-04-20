# NAPOLCOM OMR Parser

From **scan → JSON** in seconds

## Quick-start

```bash
# 1. Set up the environment
$ python -m venv .venv
$ source .venv/bin/activate  # On Windows: .venv\Scripts\activate
$ pip install -r requirements.txt

# 2. Run the FastAPI server
$ python api.py
```

Then open your browser to http://localhost:8000 to access the web interface.

## Command-line Usage

```bash
# Create the layout template (only needed once)
$ python main.py --set-layout samples/blank_sheet.jpg template.json

# Process sheets
$ python main.py samples/*.jpg --out results.csv

# Process and grade sheets
$ python main.py samples/*.jpg --out results.csv --grade
```

## Requirements

- Python ≥ 3.9
- Tesseract-OCR (`sudo apt install tesseract-ocr` or download from https://github.com/UB-Mannheim/tesseract/wiki for Windows)
- Poppler (`sudo apt install poppler-utils` or download from https://github.com/oschwartz10612/poppler-windows/releases for Windows) – only if you plan to feed PDFs

## Directory Structure

```
napolcom-omr/
│  README.md          ← you are here
│  template.json       ← auto-generated map of every cell
│  main.py             ← command-line entry-point
│  api.py              ← FastAPI server
│  omr/                ← reusable library code
│  samples/            ← raw scans for testing
│  keys/               ← answer keys for grading
└─ requirements.txt    ← pip dependencies
```

## API Usage

You can use the FastAPI API directly:

```python
import requests

# Single sheet
files = {'file': open('sample.jpg', 'rb')}
response = requests.post('http://localhost:8000/grade', files=files)
result = response.json()

# Batch processing
files = [
    ('files', open('sample1.jpg', 'rb')),
    ('files', open('sample2.jpg', 'rb'))
]
response = requests.post('http://localhost:8000/batch', files=files)
results = response.json()
```

## Troubleshooting

If the OMR parser is not correctly identifying filled bubbles or text fields:

1. Make sure the scanned image is clear and well-lit
2. Try adjusting the preprocessing steps in `omr/processor.py` (thresholds, blur kernel size, etc.)
3. Use the debug mode in the web interface to see the processing steps
4. Regenerate the template if the form layout changes

For more detailed information, please refer to the original documentation.
