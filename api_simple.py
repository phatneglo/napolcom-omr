#!/usr/bin/env python3
import base64
import io
import json
import os
from typing import Dict, List, Optional, Union
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from omr import parse_sheet
from omr.processor import OMRProcessor
import cv2
import numpy as np

app = FastAPI(title="NAPOLCOM OMR Parser API", 
              description="API for parsing NAPOLCOM examination answer sheets")

# Create directories for static files and templates
os.makedirs("static", exist_ok=True)

# Simple HTML response without Jinja2
@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_content = """<!DOCTYPE html>
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
        </div>
    </div>
    
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
                document.getElementById('debug-container').style.display = 'flex';
            }
        }
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/grade")
async def grade_sheet(
    file: UploadFile = File(...),
    debug: bool = Form(False)
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
        # Create output with extra debug info if requested
        if debug:
            # Convert bytes to numpy array for OpenCV processing
            nparr = np.frombuffer(contents, np.uint8)
            original = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Process step by step to capture intermediate images
            processed = processor.preprocess(original)
            aligned = processor.align(processed)
            
            # Extract data
            text_data = processor.extract_text(aligned)
            bubble_data = processor.extract_bubbles(aligned)
            set_type = processor.extract_set_type(aligned)
            
            # Convert images to base64 for sending in JSON
            _, original_encoded = cv2.imencode('.jpg', original)
            _, processed_encoded = cv2.imencode('.jpg', processed)
            _, aligned_encoded = cv2.imencode('.jpg', aligned)
            
            debug_images = {
                "original": base64.b64encode(original_encoded).decode('utf-8'),
                "preprocessed": base64.b64encode(processed_encoded).decode('utf-8'),
                "aligned": base64.b64encode(aligned_encoded).decode('utf-8')
            }
            
            # Combine results
            result = {
                **text_data,
                "answers": bubble_data,
                "set_type": set_type,
                "debug_images": debug_images
            }
        else:
            # Regular processing without debug images
            result = processor.process_sheet(contents)
            
        return result
        
    except Exception as e:
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
