@echo off
echo Cleaning build files...

REM Remove build directories
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q __pycache__ 2>nul
rmdir /s /q src\__pycache__ 2>nul
rmdir /s /q src\ffmpeg 2>nul

REM Remove spec files
del /f /q *.spec 2>nul

REM Remove Python cache files
del /s /q *.pyc 2>nul
del /s /q *.pyo 2>nul
del /s /q *.pyd 2>nul

echo Cleaning complete!
pause 