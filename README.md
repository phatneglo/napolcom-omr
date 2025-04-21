# NAPOLCOM OMR Processing System

A comprehensive system for processing National Police Commission examination answer sheets using computer vision, machine learning, and optical mark recognition (OMR) techniques.

## Project Overview

This project implements an automated system for extracting data from NAPOLCOM examination answer sheets. It follows the guidelines for processing forms in a specific sequence:

1. **Get the Main Mark (#1)** - Establish the anchor point with 3 lines for alignment
2. **Auto Canvas (#2)** - Capture canvas size and ensure proper orientation
3. **Extract Personal Information** - Process fields like booklet number, dates, and names
4. **Set Type Processing** - Identify the set type (A, B, or C)
5. **Application Number Processing** - Process the 11-digit application number
6. **Answer Bubble Processing** - Process all 150 answer bubbles

## Features

- **Form Template Management**: Create and configure templates for different form types
- **Region Configuration**: Define regions of interest using an interactive drag-and-drop interface
- **Synthetic Data Generation**: Generate training data with various augmentations
- **Model Training**: Train YOLO v8 models to detect form elements
- **Form Processing**: Process forms with high accuracy and confidence scores
- **Grid Removal**: Extract text from fields with grid line removal
- **Results Validation**: Validate extracted data against expected formats
- **API Integration**: RESTful API for integrating with other systems
- **Web Interface**: User-friendly interface for managing the entire workflow

## Architecture

The system follows a SOLID design architecture:
- **Single Responsibility**: Each module handles one aspect of the system
- **Open/Closed**: Extensible for new form types without modifying existing code
- **Liskov Substitution**: Common interfaces for different form processors
- **Interface Segregation**: Specialized interfaces for bubble detection vs. text extraction
- **Dependency Inversion**: High-level modules independent of low-level implementation details

## Installation

### Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)
- SQLite database
- OpenCV dependencies

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/napolcom-omr.git
   cd napolcom-omr
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

5. Initialize the database:
   ```
   python init_db.py
   ```

6. Run the application:
   ```
   python run.py
   ```

7. Access the web interface at http://localhost:8000

## Usage

### Template Creation

1. Navigate to the Templates section
2. Click "New Template"
3. Upload a form image
4. Define regions of interest using the drag-and-drop interface
5. Save the template

### Synthetic Data Generation

1. Navigate to the Training section
2. Select a template
3. Configure generation parameters
4. Generate the dataset

### Model Training

1. Navigate to the Training section
2. Select a dataset
3. Configure training parameters
4. Start the training process

### Form Processing

1. Navigate to the Processing section
2. Select a template and model
3. Upload form images
4. Configure processing options
5. Process the forms
6. View and export results

## API Documentation

The system provides a RESTful API for integration with other systems. API documentation is available at http://localhost:8000/api/docs when the application is running.

## Development

### Project Structure

```
/app
  /api               # API endpoints
  /core              # Core configuration
  /crud              # Database operations
  /db                # Database models and session
  /models            # Database models
  /schemas           # Pydantic schemas
  /services          # Business logic
  /static            # Static files
  /templates         # HTML templates
  /utils             # Utility functions
  main.py            # FastAPI application
```

### Adding New Features

1. Define schema in `/app/schemas`
2. Add database model in `/app/models`
3. Implement CRUD operations in `/app/crud`
4. Add business logic in `/app/services`
5. Create API endpoint in `/app/api/v1/endpoints`
6. Add frontend template in `/app/templates`

## License

This project is proprietary and confidential. Unauthorized use is prohibited.

## Contributors

- Your Name <your.email@example.com>

## Acknowledgements

This project was developed based on the guidelines for NAPOLCOM OMR form processing. Special thanks to the contributors of the FastAPI, OpenCV, and PyTorch libraries.
