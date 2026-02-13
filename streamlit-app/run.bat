@echo off
REM Quick startup script for the MCP Agent app
echo ============================================
echo  MCP Agent - Pharmaceutical Research Assistant
echo  Powered by Claude Sonnet 4.5
echo ============================================
echo.

REM Check if venv exists and activate it
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] No virtual environment found. Using system Python.
    echo Run: python -m venv venv ^&^& venv\Scripts\activate ^&^& pip install -r requirements.txt
)

REM Check for ANTHROPIC_API_KEY
if "%ANTHROPIC_API_KEY%"=="" (
    if not exist ".env" (
        echo.
        echo [ERROR] ANTHROPIC_API_KEY is not set and no .env file found.
        echo.
        echo Set it with one of these methods:
        echo   1. Create a .env file: echo ANTHROPIC_API_KEY=sk-ant-your-key-here ^> .env
        echo   2. Set environment variable: set ANTHROPIC_API_KEY=sk-ant-your-key-here
        echo.
        pause
        exit /b 1
    )
)

echo Starting Streamlit application...
echo.
streamlit run app.py
