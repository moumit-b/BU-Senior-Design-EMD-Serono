@echo off
REM Quick start script for Windows

echo Starting Streamlit MCP Agent...
echo.
echo Make sure:
echo 1. Ollama is running (ollama serve)
echo 2. Python virtual environment is activated
echo 3. PubChem MCP server is built
echo.

streamlit run app.py
