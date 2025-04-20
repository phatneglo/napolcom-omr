@echo off
echo Starting Napolcom OMR Scanner...

REM Check if virtual environment exists, if not create it
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    
    REM Activate virtual environment
    call venv\Scripts\activate
    
    REM Install requirements
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    REM Activate virtual environment
    call venv\Scripts\activate
)

REM Generate required answer sheet templates
echo Checking for answer sheet templates...
python -c "from app.utils.generate_sheet import main as gen1; from app.utils.generate_napolcom_sheet import main as gen2; gen1(); gen2()"

REM Run the application
echo Starting application...
python run.py

pause
