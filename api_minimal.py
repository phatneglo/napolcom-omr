#!/usr/bin/env python3
"""
Minimal API version with simplified processing to avoid the NumPy array error.
"""

import base64
import cv2
import numpy as np
import os
import json
import traceback
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create directories
os.makedirs("debug_output", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)

app = FastAPI(title="NAPOLCOM OMR Parser (Minimal)", 
              description="Minimal API for parsing NAPOLCOM examination answer sheets")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Constants
REFERENCE_WIDTH = 785
REFERENCE_HEIGHT = 1024

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Simple HTML form for uploading."""
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>NAPOLCOM OMR Parser (Minimal)</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .upload-form { border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; }
        .results { border: 1px solid #ddd; padding: 20px; margin-top: 20px; display: none; }
        img { max-width: 100%; border: 1px solid #ccc; margin-top: 10px; }
        .debug-images { display: flex; flex-wrap: wrap; gap: 10px; }
        .debug-image { flex: 1; min-width: 300px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>NAPOLCOM OMR Parser (Minimal)</h1>
        
        <div class="upload-form">
            <h2>Upload Answer Sheet</h2>
            <form id="upload-form" enctype="multipart/form-data">
                <input type="file" id="file-input" accept="image/*">
                <button type="submit">Process</button>
            </form>
        </div>
        
        <div id="results" class="results">
            <h2>Results</h2>
            <div id="status"></div>
            <div class="debug-images">
                <div class="debug-image">
                    <h3>Original</h3>
                    <img id="original-img" src="">
                </div>
                <div class="debug-image">
                    <h3>Preprocessed</h3>
                    <img id="preprocessed-img" src="">
                </div>
                <div class="debug-image">
                    <h3>Aligned</h3>
                    <img id="aligned-img" src="">
                </div>
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('upload-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const fileInput = document.getElementById('file-input');
            if (!fileInput.files.length) {
                alert('Please select a file');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            
            try {
                document.getElementById('status').innerHTML = 'Processing...';
                document.getElementById('results').style.display = 'block';
                
                const response = await fetch('/process', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.error) {
                    document.getElementById('status').innerHTML = `Error: ${result.error}`;
                } else {
                    document.getElementById('status').innerHTML = 'Processing completed successfully!';
                    
                    // Display debug images
                    document.getElementById('original-img').src = 'data:image/jpeg;base64,' + result.images.original;
                    document.getElementById('preprocessed-img').src = 'data:image/jpeg;base64,' + result.images.preprocessed;
                    document.getElementById('aligned-img').src = 'data:image/jpeg;base64,' + result.images.aligned;
                }
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('status').innerHTML = `Error: ${error.message}`;
            }
        });
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)

def preprocess_image(img):
    """Simplified preprocessing."""
    # Convert to grayscale if needed
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    
    # Apply blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply threshold
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 11, 2
    )
    
    return thresh

def align_image(img):
    """Simplified alignment."""
    # Find contours
    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Default to original size if no contours
    height, width = img.shape[:2]
    aligned = np.zeros((REFERENCE_HEIGHT, REFERENCE_WIDTH), dtype=np.uint8)
    
    if not contours:
        logger.warning("No contours found")
        # Just resize to reference dimensions
        aligned = cv2.resize(img, (REFERENCE_WIDTH, REFERENCE_HEIGHT))
        return aligned
    
    # Find largest contour
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Approximate contour
    peri = cv2.arcLength(largest_contour, True)
    approx = cv2.approxPolyDP(largest_contour, 0.02 * peri, True)
    
    # If we don't have 4 points, just resize
    if len(approx) != 4:
        logger.warning(f"Expected 4 corner points, got {len(approx)}")
        aligned = cv2.resize(img, (REFERENCE_WIDTH, REFERENCE_HEIGHT))
        return aligned
    
    # Order points
    pts = approx.reshape(4, 2)
    rect = np.zeros((4, 2), dtype=np.float32)
    
    # Sum x+y coordinates
    s = np.sum(pts, axis=1)
    # Top-left has smallest sum, bottom-right has largest sum
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    # Diff of coordinates (y-x)
    diff = np.diff(pts, axis=1)
    # Top-right has smallest diff, bottom-left has largest diff
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    # Destination points
    dst = np.array([
        [0, 0],
        [REFERENCE_WIDTH - 1, 0],
        [REFERENCE_WIDTH - 1, REFERENCE_HEIGHT - 1],
        [0, REFERENCE_HEIGHT - 1]
    ], dtype=np.float32)
    
    # Get perspective transform
    M = cv2.getPerspectiveTransform(rect, dst)
    aligned = cv2.warpPerspective(img, M, (REFERENCE_WIDTH, REFERENCE_HEIGHT))
    
    return aligned

@app.post("/process")
async def process_image(file: UploadFile = File(...)):
    """Process the uploaded image."""
    try:
        # Read file
        contents = await file.read()
        
        # Save original file
        filename = f"uploads/{file.filename}"
        with open(filename, "wb") as f:
            f.write(contents)
        
        # Convert to numpy array
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return JSONResponse(status_code=400, content={"error": "Invalid image file"})
        
        # Save a copy of original
        cv2.imwrite("debug_output/original.jpg", img)
        
        # Step 1: Preprocess
        processed = preprocess_image(img)
        cv2.imwrite("debug_output/preprocessed.jpg", processed)
        
        # Step 2: Align
        aligned = align_image(processed)
        cv2.imwrite("debug_output/aligned.jpg", aligned)
        
        # Convert images to base64 for response
        _, original_encoded = cv2.imencode('.jpg', img)
        _, processed_encoded = cv2.imencode('.jpg', processed)
        _, aligned_encoded = cv2.imencode('.jpg', aligned)
        
        # Return success with images
        return {
            "status": "success",
            "images": {
                "original": base64.b64encode(original_encoded).decode('utf-8'),
                "preprocessed": base64.b64encode(processed_encoded).decode('utf-8'),
                "aligned": base64.b64encode(aligned_encoded).decode('utf-8')
            }
        }
    
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
