import PyInstaller.__main__
import os
import shutil

def clean_builds():
    """Clean previous build directories"""
    for dir_name in ['build', 'dist', '__pycache__']:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"Cleaned {dir_name} directory")
            except Exception as e:
                print(f"Error cleaning {dir_name}: {e}")

def build_exe():
    """Build the executable"""
    opts = [
        'main.py',
        '--name=YouTube Playlist Downloader',
        '--onefile',
        '--windowed',
        '--icon=src/resources/icon.ico',
        '--add-data=src;src',
        '--hidden-import=PyQt6.sip',
        '--hidden-import=yt_dlp',
        '--clean',
        '--noconfirm',
        '--noupx',
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=PIL',
        '--exclude-module=pandas',
        '--exclude-module=tkinter',
        '--optimize=2'
    ]
    
    PyInstaller.__main__.run(opts)

if __name__ == "__main__":
    print("Starting build process...")
    clean_builds()
    build_exe() 