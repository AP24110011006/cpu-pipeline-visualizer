@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   CPU PIPELINE STUDIO - Windows Startup Launcher
echo ===================================================
echo.

set PYTHON_CMD=python
py -3.12 --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=py -3.12
)

echo Checking Python environment (%PYTHON_CMD%)...
%PYTHON_CMD% -c "import sys; print(f'Detected Python {sys.version.split()[0]}')"

if not exist venv (
    echo Creating virtual environment in .\venv ...
    %PYTHON_CMD% -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    set RUNNER=python
) else (
    echo [WARNING] venv\Scripts\activate.bat not found. Using system %PYTHON_CMD%
    set RUNNER=%PYTHON_CMD%
)

REM Check if Streamlit is already installed to avoid repeated downloads
%RUNNER% -c "import streamlit, plotly, pandas, pytest" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing / verifying required dependencies from requirements.txt ...
    %RUNNER% -m pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Dependency installation encountered an issue.
        pause
        exit /b 1
    )
) else (
    echo Core dependencies (streamlit, plotly, pandas, pytest) verified.
)

echo.
echo Launching CPU PIPELINE STUDIO on http://localhost:8501 ...
%RUNNER% -m streamlit run app.py --server.port 8501
pause
