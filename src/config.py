import os

# Default configurations
DEFAULT_DOWNLOAD_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")
DEFAULT_RESOLUTION = "720p"

# Video format options
SUPPORTED_RESOLUTIONS = ["144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p", "4320p"]

# Audio format options
SUPPORTED_AUDIO_FORMATS = {
    "M4A": "m4a",
    "MP3": "mp3",
    "WAV": "wav",
    "AAC": "aac"
}

SUPPORTED_AUDIO_QUALITIES = {
    "320kbps": "320",
    "256kbps": "256",
    "192kbps": "192",
    "128kbps": "128",
    "64kbps": "64"
}

DEFAULT_AUDIO_FORMAT = "M4A"
DEFAULT_AUDIO_QUALITY = "192kbps"

# Console colors
class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    ENDC = "\033[0m" 