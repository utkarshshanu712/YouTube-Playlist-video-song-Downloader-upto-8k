import os
from typing import Optional
import platform
import subprocess
import sys
import urllib.request
import zipfile
import shutil
from pathlib import Path

def check_ffmpeg() -> bool:
    """Check if FFmpeg is available."""
    return bool(get_ffmpeg_path())

def get_ffmpeg_path() -> Optional[str]:
    """Get FFmpeg path, prioritizing bundled FFmpeg"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Check bundled FFmpeg first
    ffmpeg_exe = os.path.join(base_path, 'ffmpeg', 'ffmpeg.exe')
    if os.path.exists(ffmpeg_exe):
        os.environ['PATH'] = f"{os.path.dirname(ffmpeg_exe)};{os.environ['PATH']}"
        return ffmpeg_exe
    
    # Then check system PATH
    if platform.system().lower() == 'windows':
        system_ffmpeg = shutil.which('ffmpeg.exe')
        if system_ffmpeg:
            return system_ffmpeg
    
    return None

def get_url_type(url: str) -> str:
    """Determine URL type (playlist or video)."""
    url = url.lower()
    if "youtube.com/playlist" in url:
        return "playlist"
    elif "youtube.com/watch" in url or "youtu.be/" in url:
        return "video"
    return "invalid"

def validate_url(url: str) -> bool:
    """Basic validation for YouTube URL."""
    url = url.lower()
    return "youtube.com/playlist" in url or "youtube.com/watch" in url or "youtu.be/" in url

def create_download_directory(path: str) -> None:
    """Create download directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)

def format_size(bytes: int) -> str:
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} GB"

def clean_filename(filename: str) -> str:
    """Clean filename to remove invalid characters."""
    return "".join(char for char in filename if char.isalnum() or char in (' ', '-', '_', '.'))

def setup_ffmpeg() -> Optional[str]:
    """One-time FFmpeg setup"""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    ffmpeg_dir = os.path.join(app_dir, 'ffmpeg')
    ffmpeg_exe = os.path.join(ffmpeg_dir, 'ffmpeg.exe')
    
    try:
        os.makedirs(ffmpeg_dir, exist_ok=True)
        url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        zip_path = os.path.join(ffmpeg_dir, "ffmpeg.zip")
        
        urllib.request.urlretrieve(url, zip_path)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith(('ffmpeg.exe', 'ffprobe.exe')):
                    zip_ref.extract(file, ffmpeg_dir)
                    src = os.path.join(ffmpeg_dir, file)
                    dst = os.path.join(ffmpeg_dir, os.path.basename(file))
                    if os.path.exists(dst):
                        os.remove(dst)
                    shutil.move(src, dst)
        
        os.remove(zip_path)
        os.environ['PATH'] = f"{ffmpeg_dir};{os.environ['PATH']}"
        return ffmpeg_exe
        
    except Exception as e:
        print(f"Error setting up FFmpeg: {str(e)}")
        return None