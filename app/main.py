import os
import uuid
import cv2
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import shutil
from typing import List, Optional
import aiofiles
import numpy as np

from app.utils.omr import get_answers as get_answers_original
from app.utils.napolcom_omr import get_answers as get_answers_napolcom

app = FastAPI(title="NAPOLCOM OMR Scanner", description="Optical Mark Recognition API for NAPOLCOM Answer Sheets")

# Configure static files and templates
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Make sure the UPLOAD_DIR exists
UPLOAD_DIR.mkdir(exist_ok=True)

# Path to the corner image
CORNER_IMG_PATH = BASE_DIR / "static" / "img" / "corner.png"

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process", response_class=HTMLResponse)
async def process_image(request: Request, file: UploadFile = File(...), sheet_type: str = Form("napolcom")):
    """Process the uploaded image and return the results"""
    try:
        # Create a unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        result_filename = f"result_{unique_filename}"
        result_path = UPLOAD_DIR / result_filename
        
        # Save the uploaded file
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        # Process the image based on sheet type
        if sheet_type == "napolcom":
            answers, annotated_image = get_answers_napolcom(str(file_path))
            # Format the answers - they're already in the correct format from napolcom_omr
            formatted_answers = answers
        else:  # Original format
            answers, annotated_image = get_answers_original(str(file_path), str(CORNER_IMG_PATH))
            # Format the answers for original format
            formatted_answers = [f"Q{i+1}: {answer}" for i, answer in enumerate(answers)]
        
        # Save the annotated image
        cv2.imwrite(str(result_path), annotated_image)
        
        # Return the results
        return templates.TemplateResponse(
            "result.html", 
            {
                "request": request, 
                "answers": formatted_answers, 
                "original_image": f"/image/{unique_filename}",
                "result_image": f"/image/{result_filename}",
                "sheet_type": sheet_type
            }
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "error": str(e), "details": error_details}
        )

@app.get("/image/{filename}")
async def get_image(filename: str):
    """Serve an image from the uploads directory"""
    return FileResponse(UPLOAD_DIR / filename)

@app.get("/download/answer-sheet")
async def download_answer_sheet(sheet_type: str = "napolcom"):
    """Download the blank answer sheet template"""
    if sheet_type == "napolcom":
        sheet_path = BASE_DIR / "static" / "img" / "napolcom-answer-sheet.pdf"
        filename = "napolcom-answer-sheet.pdf"
    else:
        sheet_path = BASE_DIR / "static" / "img" / "answer-sheet.pdf"
        filename = "answer-sheet.pdf"
    
    # If file doesn't exist, generate it
    if not sheet_path.exists():
        if sheet_type == "napolcom":
            from app.utils.generate_napolcom_sheet import main as generate_napolcom
            generate_napolcom()
        else:
            from app.utils.generate_sheet import main as generate_sheet
            generate_sheet()
    
    return FileResponse(
        path=sheet_path, 
        filename=filename, 
        media_type="application/pdf"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
