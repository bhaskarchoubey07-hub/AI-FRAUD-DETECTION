@echo off
cd /d "%~dp0"
echo Starting AI Fraud Detector...
echo.
echo If Streamlit asks for email, just press Enter to skip.
echo.
echo Opening browser at http://localhost:8501
echo.
python -m streamlit run app.py
pause
