@echo off
echo Starting NEXAS Django Backend...
echo.

cd /d "%~dp0"

echo Activating virtual environment...
call venv_new\Scripts\activate

echo Starting Django development server...
python manage_minimal.py runserver

pause
