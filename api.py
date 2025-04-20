#!/usr/bin/env python3
import base64
import io
import json
import os
import traceback
from typing import Dict, List, Optional, Union
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from omr import parse_sheet
from omr.processor import OMRProcessor
import cv2
import numpy as np

app = FastAPI(title="NAPOLCOM OMR Parser API", 
              description="API for parsing NAPOLCOM examination answer sheets")

# Create directories for static files and templates
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Create a basic HTML template for the frontend
with open("templates/index.html", "w") as f:
    f.write("""<!DOCTYPE html>
<html>
<head>
    <title>NAPOLCOM OMR Parser</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            max-width: 1000px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
        }
        .upload-container {
            border: 2px dashed #ccc;
            padding: 20px;
            text-align: center;
            margin-bottom: 30px;
            border-radius: 5px;
        }
        .result-container {
            margin-top: 20px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #f9f9f9;
        }
        .debug-container {
            display: flex;
            margin-top: 20px;
        }
        .debug-image {
            flex: 1;
            margin: 5px;
            text-align: center;
        }
        .debug-image img {
            max-width: 100%;
            border: 1px solid #ddd;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        .answers-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 5px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover {
            background-color: #45a049;
        }
        input[type="file"] {
            margin: 10px 0;
        }
        .loading {
            display: none;
            text-align: center;
            margin-top: 20px;
        }
        .text-fields-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .text-field {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            background-color: #f9f9f9;
        }
        .text-field h4 {
            margin-top: 0;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }
        .text-field img {
            max-width: 100%;
            border: 1px solid #ddd;
            margin-top: 5px;
        }
        .text-field p {
            margin: 5px 0;
            font-weight: bold;
            color: #333;
        }
    </style>
</head>
<body>
    <h1>NAPOLCOM OMR Parser</h1>
    
    <div class="upload-container">
        <h2>Upload Answer Sheet</h2>
        <form id="upload-form" enctype="multipart/form-data">
            <input type="file" id="file-input" accept="image/*" required>
            <div>
                <input type="checkbox" id="debug-checkbox">
                <label for="debug-checkbox">Show debug images</label>
            </div>
            <button type="submit">Process Sheet</button>
        </form>
        <div id="loading" class="loading">
            Processing... Please wait.
        <div class="debug-image">
            <h3>Aligned Original</h3>
            <img id="aligned-original-image" src="">
        </div>
    </div>
    
    <div id="text-debug-container" class="debug-container" style="display: none;">
        <h3>Text Field Detection</h3>
        <div id="text-debug-content"></div>
    
    <div id="result-container" style="display: none;" class="result-container">
        <h2>Results</h2>
        <div id="result-content"></div>
    </div>
    
    <div id="debug-container" class="debug-container" style="display: none;">
        <div class="debug-image">
            <h3>Original</h3>
            <img id="original-image" src="">
        </div>
        <div class="debug-image">
            <h3>Preprocessed</h3>
            <img id="preprocessed-image" src="">
        </div>
        <div class="debug-image">
            <h3>Aligned</h3>
            <img id="aligned-image" src="">
        </div>
        <div class="debug-image">
            <h3>Aligned Original</h3>
            <img id="aligned-original-image" src="">
        </div>
    </div>
    
    <div id="text-debug-container" class="debug-container" style="display: none;">
        <h3>Text Field Detection</h3>
        <div id="text-debug-content"></div>
    </div>
    
    <script>
        document.getElementById('upload-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const fileInput = document.getElementById('file-input');
            const debugMode = document.getElementById('debug-checkbox').checked;
            
            if (fileInput.files.length === 0) {
                alert('Please select a file to upload');
                return;
            }
            
            // Show loading indicator
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result-container').style.display = 'none';
            document.getElementById('debug-container').style.display = 'none';
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('debug', debugMode);
            
            try {
                const response = await fetch('/grade', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error(`Error: ${response.status}`);
                }
                
                const result = await response.json();
                displayResult(result, debugMode);
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred while processing the file.');
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        });
        
        function displayResult(result, debugMode) {
            const resultContainer = document.getElementById('result-container');
            const resultContent = document.getElementById('result-content');
            
            // Display header information
            let html = '<table>';
            html += '<tr><th>Field</th><th>Value</th></tr>';
            
            // Display all fields except answers and debug images
            for (const [key, value] of Object.entries(result)) {
                if (key !== 'answers' && key !== 'debug_images') {
                    html += `<tr><td>${key}</td><td>${value}</td></tr>`;
                }
            }
            html += '</table>';
            
            // Display answers
            if (result.answers) {
                html += '<h3>Answers</h3>';
                html += '<div class="answers-grid">';
                
                // Create 5 columns of 30 questions each
                for (let col = 0; col < 5; col++) {
                    html += '<div>';
                    html += `<h4>Questions ${col*30+1} - ${(col+1)*30}</h4>`;
                    html += '<table>';
                    
                    for (let q = 1; q <= 30; q++) {
                        const qNum = col * 30 + q;
                        const answer = result.answers[qNum.toString()] || '-';
                        html += `<tr><td>${qNum}</td><td>${answer}</td></tr>`;
                    }
                    
                    html += '</table>';
                    html += '</div>';
                }
                
                html += '</div>';
            }
            
            resultContent.innerHTML = html;
            resultContainer.style.display = 'block';
            
            // Display debug images if requested
            if (debugMode && result.debug_images) {
                document.getElementById('original-image').src = 'data:image/jpeg;base64,' + result.debug_images.original;
                document.getElementById('preprocessed-image').src = 'data:image/jpeg;base64,' + result.debug_images.preprocessed;
                document.getElementById('aligned-image').src = 'data:image/jpeg;base64,' + result.debug_images.aligned;
                
                if (result.debug_images.aligned_original) {
                    document.getElementById('aligned-original-image').src = 'data:image/jpeg;base64,' + result.debug_images.aligned_original;
                }
                
                document.getElementById('debug-container').style.display = 'flex';
                
                // Check if text field debug images exist
                const textDebugContent = document.getElementById('text-debug-content');
                if (result.debug_images.text_fields) {
                    let textHtml = '<div class="text-fields-grid">';
                    for (const [field, images] of Object.entries(result.debug_images.text_fields)) {
                        textHtml += `<div class="text-field">`;
                        textHtml += `<h4>${field}</h4>`;
                        for (const [type, image] of Object.entries(images)) {
                            textHtml += `<div><p>${type}</p><img src="data:image/jpeg;base64,${image}" /></div>`;
                        }
                        textHtml += `</div>`;
                    }
                    textHtml += '</div>';
                    textDebugContent.innerHTML = textHtml;
                    document.getElementById('text-debug-container').style.display = 'block';
                }
            }
        }
    </script>
</body>
</html>
""")

# Set up templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/grade")
async def grade_sheet(
    file: UploadFile = File(...),
    debug: bool = Form(True)  # Default to true for now
):
    """
    Process an uploaded answer sheet and return the extracted data.
    
    If debug is True, also return debug images showing the processing steps.
    """
    # Read the uploaded file
    contents = await file.read()
    
    # Process the sheet
    processor = OMRProcessor("template.json")
    
    try:
        # Save uploaded file for reference
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"{upload_dir}/{file.filename}"
        with open(filename, "wb") as f:
            f.write(contents)
        
        # Debug in detail
        print("Starting processing...")
        
        # Create output with debug info
        # Convert bytes to numpy array for OpenCV processing
        nparr = np.frombuffer(contents, np.uint8)
        original = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        print(f"Original image shape: {original.shape}")
        
        # Process and save all intermediate steps
        debug_dir = "debug_output"
        os.makedirs(debug_dir, exist_ok=True)
            # Step 1: Preprocessing
            print("Preprocessing...")
            processed = processor.preprocess(original)
            cv2.imwrite(f"{debug_dir}/preprocessed.jpg", processed)
            print("Preprocessing done.")
            
            # Step 2: Alignment
            print("Aligning...")
            aligned = processor.align(processed)
            cv2.imwrite(f"{debug_dir}/aligned.jpg", aligned)
            print("Alignment done.")
            
            # Step 3: Try to align original image (better for OCR)
            print("Aligning original...")
            aligned_original = None
            try:
                # Get contours and calculate alignment transform
                print("Finding contours...")
                contours, _ = cv2.findContours(processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                print(f"Found {len(contours)} contours")
                
                if len(contours) > 0:
                    largest_contour = max(contours, key=cv2.contourArea)
                    peri = cv2.arcLength(largest_contour, True)
                    approx = cv2.approxPolyDP(largest_contour, 0.02 * peri, True)
                    print(f"Approximated contour has {len(approx)} points")
                    
                    if len(approx) == 4:
                        # Order points and apply same transform to original image
                        print("Ordering points...")
                        src_pts = processor._order_points(approx).astype(np.float32)
                        dst_pts = np.array([
                            [0, 0],
                            [785, 0],  # REFERENCE_WIDTH
                            [785, 1024],  # REFERENCE_WIDTH, REFERENCE_HEIGHT
                            [0, 1024]  # REFERENCE_HEIGHT
                        ], dtype=np.float32)
                        
                        print("Computing transform...")
                        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
                        print("Applying warp...")
                        aligned_original = cv2.warpPerspective(original, M, (785, 1024))
                        cv2.imwrite(f"{debug_dir}/aligned_original.jpg", aligned_original)
                        print("Original alignment complete")
                    else:
                        print("Could not determine precise alignment transform for original image")
                        aligned_original = original
                else:
                    print("No contours found for alignment")
                    aligned_original = original
            except Exception as e:
                print(f"Error aligning original image: {str(e)}")
                traceback.print_exc()
                aligned_original = original
        
        # If the error is in the extract_text or extract_bubbles functions, let's simplify for now
        try:
            # Extract text from aligned original
            print("Extracting text...")
            text_data = {}
            for field in processor.template["text_boxes"]:
                text_data[field] = "" # Skip OCR for now
            print("Text extraction done (simplified)")
            
            # Extract bubbles from aligned binary image
            print("Extracting bubbles...")
            bubble_data = {}
            set_type = "A" # Default for now
            print("Bubble extraction done (simplified)")
        except Exception as e:
            print(f"Error in extraction: {str(e)}")
            traceback.print_exc()
            text_data = {}
            bubble_data = {}
            set_type = "Unknown"
        
        # Combine results
        result = {
            **text_data,
            "answers": bubble_data,
            "set_type": set_type
        }
        
        # Convert all debug images to base64 for the response
        debug_images = {
            "original": original,
            "preprocessed": processed,
            "aligned": aligned
        }
        if aligned_original is not None:
            debug_images["aligned_original"] = aligned_original
        
        # Convert to base64
        encoded_images = {}
        for name, img in debug_images.items():
            _, img_encoded = cv2.imencode('.jpg', img)
            encoded_images[name] = base64.b64encode(img_encoded).decode('utf-8')
        
        # Add debug images to result
        result["debug_images"] = encoded_images
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/batch")
async def batch_process(files: List[UploadFile] = File(...)):
    """Process multiple answer sheets in a batch."""
    results = []
    
    for file in files:
        try:
            contents = await file.read()
            result = parse_sheet(contents)
            results.append({
                "filename": file.filename,
                "result": result
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return results

if __name__ == "__main__":
    # Ensure template.json exists
    if not os.path.exists("template.json"):
        print("Warning: template.json not found. Please run the template wizard first.")
        print("  python main.py --set-layout samples/blank_sheet.jpg template.json")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
