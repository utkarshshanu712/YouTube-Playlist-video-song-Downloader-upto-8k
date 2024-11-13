@echo off
echo Cleaning and building application...

REM Install required packages
python -m pip install -r requirements.txt --upgrade

REM Kill any running instances
taskkill /F /IM "YouTube Playlist Downloader.exe" 2>nul
timeout /t 2 /nobreak >nul

REM Clean everything
python -c "from src.build_exe import clean_builds; clean_builds()"
timeout /t 2 /nobreak >nul

REM Build optimized executable
python -OO src/build_exe.py

if exist "dist\YouTube Playlist Downloader.exe" (
    echo Build successful!
) else (
    echo Build failed!
    pause
    exit /b 1
) 