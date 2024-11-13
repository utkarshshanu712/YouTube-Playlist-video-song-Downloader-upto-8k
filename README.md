# YouTube Playlist & Video Downloader Pro

A powerful desktop application for downloading YouTube videos and playlists with support for up to 8K quality and various audio formats.

## Latest Version: 1.1.0 (March 2024)

## Author
- **Utkarsh Kumar**
- GitHub: [@utkarshshanu712](https://github.com/utkarshshanu712)
- Project: [YouTube-Playlist-Downloader](https://github.com/utkarshshanu712/YouTube-Playlist-Downloader)
- Email: utkarshshanu712@gmail.com

## Features
 **High-Quality Video Downloads**: Support for up to 8K (4320p) resolution
- **Smart Playlist Management**: Download entire playlists with progress tracking
- **Advanced Audio Options**: 
  - Multiple formats: MP3, M4A, WAV, FLAC, AAC
  - High-quality audio: 64kbps to 320kbps
  - Audio extraction from videos
- **Modern Interface**:
  - Real-time progress tracking
  - Video thumbnail previews
  - Download speed monitoring
  - Pause/Resume functionality
- **Customization**:
  - Flexible save location
  - Format selection
  - Quality preferences
- **Reliability**:
  - Auto-retry on failure
  - Network error handling
  - Format validation
![Screenshot 2024-11-13 232621](https://github.com/user-attachments/assets/5126e708-e09d-4917-9b9c-4871c5e59357)

## Installation![Screenshot 2024-11-13 232559](https://github.com/user-attachments/assets/6d037a39-7c4a-4c6f-bd52-15eeb35bc5e7)


### Prerequisites
- Python 3.8 or higher
- Windows OS (tested on Windows 10/11)
- FFmpeg (required for video/audio processing)

### Installing FFmpeg
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract the ZIP file
3. Add the `bin` folder to your system PATH
   - Open System Properties → Advanced → Environment Variables
   - Under System Variables, select "Path" and click "Edit"
   - Click "New" and add the path to FFmpeg's bin folder
   - Click "OK" to save changes

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
