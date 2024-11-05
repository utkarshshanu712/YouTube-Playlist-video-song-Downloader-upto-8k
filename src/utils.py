import os
from typing import Optional
from . import config

def clean_filename(filename: str) -> str:
    """Clean filename to remove invalid characters."""
    return "".join(char for char in filename if char.isalnum() or char in (' ', '-', '_', '.'))

def create_download_directory(path: str) -> None:
    """Create download directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)

def format_size(bytes: int) -> str:
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} GB"

def validate_url(url: str) -> bool:
    """Basic validation for YouTube URL."""
    url = url.lower()
    return "youtube.com/playlist" in url or "youtube.com/watch" in url or "youtu.be/" in url

def get_resolution_choice() -> str:
    """Get user's preferred video resolution."""
    print("\nAvailable resolutions:")
    for i, res in enumerate(config.SUPPORTED_RESOLUTIONS, 1):
        print(f"{i}. {res}")
    
    while True:
        try:
            choice = int(input("\nSelect resolution (number): "))
            if 1 <= choice <= len(config.SUPPORTED_RESOLUTIONS):
                return config.SUPPORTED_RESOLUTIONS[choice-1]
        except ValueError:
            pass
        print("Invalid choice. Please try again.") 

def get_url_type(url: str) -> str:
    """Detect if URL is playlist or single video."""
    url = url.lower()
    if "youtube.com/playlist" in url:
        return "playlist"
    elif "youtube.com/watch" in url or "youtu.be/" in url:
        return "video"
    return "invalid"