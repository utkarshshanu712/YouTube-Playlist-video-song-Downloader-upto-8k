# YouTube Playlist video song Downloader upto 8k

A powerful desktop application for downloading YouTube videos , song in any format and playlists with customizable quality settings.

## Features

- **Video Downloads**: Download single YouTube videos
- **Playlist Support**: Download entire YouTube playlists
- **Quality Options**: Choose video quality up to 4K (4320p)
- **Audio Extraction**: Download audio-only in multiple formats
  - Supported formats: MP3, M4A, WAV, FLAC, AAC
  - Adjustable audio quality (64kbps to 320kbps)
- **User-Friendly Interface**:
  - Progress tracking
  - Video thumbnail preview
  - Download status log
  - Pause/Resume support
- **Custom Save Location**: Choose where to save your downloads
- **Error Handling**: Robust error management and user feedback![image](https://github.com/user-attachments/assets/d7d28636-b82f-4ee3-8e77-a861a895a9a0)![image](https://github.com/user-attachments/assets/fe3ae27e-3a33-49a1-befc-6fd03767528c)
![image](https://github.com/user-attachments/assets/ac9a4598-d5bc-4aa8-bc12-015770111f87)
![image](https://github.com/user-attachments/assets/d0a7b317-69d9-4651-b43c-012718f7281b)
![image](https://github.com/user-attachments/assets/84644d99-043b-4e2e-9908-9b2bd19caf1b)
![image](https://github.com/user-attachments/assets/f6e7b11d-db7b-4764-aea0-950a4ea5c8ba)



## Installation

### Prerequisites
- Python 3.8 or higher
- Windows OS (tested on Windows 10/11)

### Method 1: Using Pre-built Executable
1. Download the latest release from the releases page
2. Extract the ZIP file
3. Run `YouTube Playlist Downloader.exe`


### Method 2: Running from Source git clone https://github.com/utkarshshanu712/YouTube-Playlist-video-song-Downloader-upto-8k/tree/master
cd youtube-playlist-downloader


2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
python main.py
```


### Method 3: Building from Source

1. Install dependencies:


2. Run the build script:

```bash
python build_exe.py

The executable will be created in the `dist` folder.

## Usage

1. Launch the application
2. Paste a YouTube video or playlist URL
3. Select download options:
   - Choose video quality (for video downloads)
   - Enable audio-only mode if desired
   - Select audio format and quality
4. Choose download location
5. Click "Download" to start

## Configuration

Default settings can be modified in `src/config.py`:
- Default download path
- Default video resolution
- Default audio format and quality

## Project Structure

- `src/`: Source code directory
  - `gui.py`: Main application interface
  - `downloader.py`: Download handling logic
  - `config.py`: Configuration settings
  - `utils.py`: Utility functions
- `resources/`: Application resources
- `build_exe.py`: Build script for creating executable
- `requirements.txt`: Python dependencies

## Dependencies

- yt-dlp: YouTube download engine
- PyQt6: GUI framework
- pyinstaller: Executable builder
- tqdm: Progress bar functionality
- Other dependencies listed in requirements.txt

## License

Copyright (c) 2024 UTKARSH KUMAR. All rights reserved.
Contact: utkarshshanu712@gmail.com

## Troubleshooting

1. **Download Fails**:
   - Check your internet connection
   - Verify the URL is valid
   - Ensure you have write permissions in the download directory

2. **Build Issues**:
   - Clean the build directories
   - Update all dependencies
   - Check Python environment variables

3. **Performance Issues**:
   - Lower video quality for faster downloads
   - Avoid downloading multiple videos simultaneously
   - Check available disk space

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

For issues and feature requests, please create an issue in the repository or contact the developer directly.
I am ready for any suggestions you can give me to utkarshshanu712@gmail.com
```
