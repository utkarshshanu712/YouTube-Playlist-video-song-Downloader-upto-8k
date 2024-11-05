@echo off
echo Cleaning and rebuilding application...

REM Clean previous builds
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Install requirements
python -m pip install -r requirements.txt

REM Run PyInstaller
python build_exe.py

if exist "dist\YouTube Playlist Downloader.exe" (
    echo Build successful!
    echo Starting application...
    start "" "dist\YouTube Playlist Downloader.exe"
) else (
    echo Build failed!
    pause
) 