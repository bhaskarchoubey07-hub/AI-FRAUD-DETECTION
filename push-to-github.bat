@echo off
cd /d "%~dp0"

echo ========================================
echo  Push to GitHub: AI-FRAUD-DETECTION
echo ========================================
echo.

where git >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed or not in PATH.
    echo.
    echo Install Git from: https://git-scm.com/download/win
    echo Then restart this script.
    pause
    exit /b 1
)

if not exist .git (
    git init
    echo Git initialized.
)

git add .
git status
echo.

set /p confirm="Commit and push? (y/n): "
if /i not "%confirm%"=="y" exit /b 0

git commit -m "Initial commit: AI Financial Statement Fraud Detector"
git branch -M main

git remote remove origin 2>nul
git remote add origin https://github.com/bhaskarchoubey07-hub/AI-FRAUD-DETECTION.git

echo.
echo Pushing to GitHub...
git push -u origin main

echo.
echo Done! Check: https://github.com/bhaskarchoubey07-hub/AI-FRAUD-DETECTION
pause
