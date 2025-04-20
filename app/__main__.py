"""
Entry point for running the application as a module.
Usage: python -m app
"""

import uvicorn
from pathlib import Path
import os

if __name__ == "__main__":
    # Auto-generate answer sheet and corner image if needed
    base_dir = Path(__file__).resolve().parent
    answer_sheet_path = base_dir / "static" / "img" / "answer-sheet.png"
    corner_path = base_dir / "static" / "img" / "corner.png"
    
    if not answer_sheet_path.exists() or not corner_path.exists():
        print("Generating answer sheet and corner image...")
        from app.utils.generate_sheet import main as generate_sheet
        generate_sheet()
    
    # Start the FastAPI application
    print("Starting OMR Scanner application...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
