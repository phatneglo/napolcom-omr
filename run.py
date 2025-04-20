import uvicorn
import os
from pathlib import Path
import subprocess
import sys

# Generate the answer sheet and corner image if they don't exist
def generate_resources():
    base_dir = Path(__file__).resolve().parent
    original_sheet_path = base_dir / "app" / "static" / "img" / "answer-sheet.png"
    napolcom_sheet_path = base_dir / "app" / "static" / "img" / "napolcom-answer-sheet.png"
    corner_path = base_dir / "app" / "static" / "img" / "corner.png"
    
    # Generate original answer sheet if needed
    if not original_sheet_path.exists() or not corner_path.exists():
        print("Generating original answer sheet and corner image...")
        from app.utils.generate_sheet import main as generate_sheet
        generate_sheet()
    
    # Generate NAPOLCOM answer sheet if needed
    if not napolcom_sheet_path.exists():
        print("Generating NAPOLCOM answer sheet...")
        from app.utils.generate_napolcom_sheet import main as generate_napolcom_sheet
        generate_napolcom_sheet()

def main():
    # Check if we need to run the generation script
    generate_resources()
    
    # Start the FastAPI application
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
