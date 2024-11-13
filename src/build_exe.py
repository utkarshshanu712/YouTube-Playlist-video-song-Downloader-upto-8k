import PyInstaller.__main__
import os
import shutil
import platform
import requests
import zipfile
import glob
import stat
import time
import psutil

def download_ffmpeg():
    """Download FFmpeg for bundling"""
    ffmpeg_dir = os.path.join('src', 'ffmpeg')
    os.makedirs(ffmpeg_dir, exist_ok=True)
    
    if platform.system().lower() == 'windows':
        url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        zip_path = os.path.join(ffmpeg_dir, "ffmpeg.zip")
        
        print("Downloading FFmpeg...")
        response = requests.get(url, stream=True)
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("Extracting FFmpeg...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith('ffmpeg.exe'):
                    zip_ref.extract(file, ffmpeg_dir)
                    src = os.path.join(ffmpeg_dir, file)
                    dst = os.path.join(ffmpeg_dir, 'ffmpeg.exe')
                    if os.path.exists(dst):
                        os.remove(dst)
                    shutil.move(src, dst)
                    break
        
        os.remove(zip_path)
        print("FFmpeg downloaded successfully")

def clean_builds():
    """Clean previous build directories and cache"""
    # First kill any running instances
    PROCNAME = "YouTube Playlist Downloader.exe"
    for proc in psutil.process_iter():
        try:
            if proc.name() == PROCNAME:
                proc.kill()
                time.sleep(1)  # Wait for process to terminate
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    directories_to_clean = ['build', 'dist', '__pycache__', 'src/ffmpeg']
    files_to_clean = ['*.spec', '*.pyc']
    
    # Clean directories with retry mechanism
    for dir_name in directories_to_clean:
        if os.path.exists(dir_name):
            for _ in range(3):  # Try 3 times
                try:
                    def on_rm_error(func, path, exc_info):
                        # Try to change permissions and retry
                        os.chmod(path, stat.S_IWRITE)
                        func(path)
                    
                    shutil.rmtree(dir_name, onerror=on_rm_error)
                    print(f"Cleaned {dir_name} directory")
                    break
                except Exception as e:
                    print(f"Retrying to clean {dir_name}: {e}")
                    time.sleep(1)
    
    # Clean files
    for pattern in files_to_clean:
        for file in glob.glob(pattern):
            try:
                if os.path.exists(file):
                    os.chmod(file, stat.S_IWRITE)
                    os.remove(file)
                    print(f"Removed {file}")
            except Exception as e:
                print(f"Error removing {file}: {e}")

def build_exe():
    """Build the executable with FFmpeg bundled"""
    clean_builds()
    download_ffmpeg()
    
    # Create resource directory
    os.makedirs('src/resources', exist_ok=True)
    
    # Ensure FFmpeg exists
    if not os.path.exists('src/ffmpeg/ffmpeg.exe'):
        print("FFmpeg not found, downloading...")
        download_ffmpeg()
    
    opts = [
        'main.py',
        '--name=YouTube Playlist Downloader',
        '--onefile',
        '--windowed',
        '--icon=src/resources/icon.ico',
        '--add-binary=src/ffmpeg/ffmpeg.exe;ffmpeg',
        '--add-data=src/resources;resources',
        '--hidden-import=PyQt6.sip',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=yt_dlp',
        '--collect-data=yt_dlp',
        '--collect-data=certifi',
        '--clean',
        '--noconfirm',
        # Additional optimizations
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=PIL',
        '--exclude-module=pandas',
        '--exclude-module=tkinter',
        '--exclude-module=scipy',
        '--exclude-module=PyQt6.QtWebEngineWidgets',
        '--exclude-module=PyQt6.QtWebEngine',
        '--exclude-module=PyQt6.QtLocation',
        '--exclude-module=PyQt6.QtMultimedia',
        '--exclude-module=PyQt6.QtBluetooth',
        '--exclude-module=PyQt6.QtPositioning',
        '--exclude-module=PyQt6.QtDesigner',
        '--exclude-module=PyQt6.QtQuick',
        '--exclude-module=PyQt6.QtQml',
        '--exclude-module=PyQt6.QtNetwork',
        '--exclude-module=PyQt6.QtSql',
        '--exclude-module=PyQt6.QtTest',
        '--exclude-module=PyQt6.QtXml',
        '--optimize=2'
    ]
    
    PyInstaller.__main__.run(opts)

if __name__ == "__main__":
    build_exe() 