@echo off
echo Setting up Napolcom OMR Scanner...

REM Create virtual environment
if exist venv (
    echo Removing existing virtual environment...
    rmdir /s /q venv
)

echo Creating new virtual environment...
python -m venv venv
call venv\Scripts\activate

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt

REM Create necessary directories if they don't exist
echo Creating necessary directories...
if not exist app\uploads mkdir app\uploads
if not exist app\static\img mkdir app\static\img

REM Generate answer sheet templates
echo Generating answer sheet templates...
python -c "from app.utils.generate_sheet import main as gen1; from app.utils.generate_napolcom_sheet import main as gen2; gen1(); gen2()"

echo.
echo Setup completed successfully!
echo.
echo To start the application, run: start.bat
echo.
pause
