@echo off
cd /d "%~dp0"
python run_workbench.py
if errorlevel 1 (
  echo.
  echo Python 3.10+ with Tkinter is required. Check python.org.
  pause
)
