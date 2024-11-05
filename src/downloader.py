from tqdm import tqdm
import os
from typing import Optional
import yt_dlp
import time
from . import config
from . import utils

class BaseDownloader:
    def __init__(self, url: str, output_path: Optional[str] = None, 
                 resolution: Optional[str] = None, audio_only: bool = False,
                 audio_quality: Optional[str] = None, audio_format: Optional[str] = None):
        self.url = url
        self.output_path = output_path or config.DEFAULT_DOWNLOAD_PATH
        self.resolution = resolution or config.DEFAULT_RESOLUTION
        self.audio_only = audio_only
        self.audio_quality = audio_quality or config.DEFAULT_AUDIO_QUALITY
        self.audio_format = audio_format or config.DEFAULT_AUDIO_FORMAT
        self.is_running = True
        self.is_paused = False
        self.progress_callback = None
        self.downloaded_files = set()
        self.current_process = None

        # Configure format selection
        if self.audio_only:
            format_str = 'bestaudio/best'
        else:
            res_number = self.resolution[:-1]
            format_str = f'bestvideo[height<=?{res_number}]+bestaudio/best[height<=?{res_number}]/best'

        self.ydl_opts = {
            'format': format_str,
            'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self._progress_hook],
            'postprocessor_hooks': [self._post_hook],
            'writethumbnail': False,
            'noplaylist': True,
            'ignoreerrors': True,
            'extract_flat': False,
            'concurrent_fragment_downloads': 1,  # Reduced for stability
            'retries': 3,
            'file_access_retries': 3,
            'fragment_retries': 3,
            'skip_unavailable_fragments': True,
            'no_color': True,
            'socket_timeout': 30,
            'max_sleep_interval': 3,
            'sleep_interval': 1,
            'overwrites': True,
            'continue': True,
            'merge_output_format': 'mp4'
        }

        if audio_only:
            self.ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': self.audio_format.lower(),
                'preferredquality': self.audio_quality.replace('kbps', ''),
                'nopostoverwrites': False,
            }]

    def _progress_hook(self, d):
        try:
            if not self.is_running:
                raise Exception("Download stopped by user")
                
            while self.is_paused:
                time.sleep(0.1)
                if not self.is_running:
                    raise Exception("Download stopped by user")

            if d['status'] == 'downloading' and self.progress_callback:
                filename = d.get('filename', '')
                if filename not in self.downloaded_files:
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    if total > 0:
                        percentage = min(100, int((downloaded / total) * 100))
                        self.progress_callback(percentage, d.get('info_dict', {}).get('title', ''), 
                                            d.get('info_dict', {}).get('thumbnail', ''))
        except Exception as e:
            print(f"Progress hook error: {str(e)}")

    def _post_hook(self, d):
        if d['status'] == 'finished':
            self.downloaded_files.add(d.get('filename', ''))
            if self.progress_callback:
                self.progress_callback(100, '', '')

    def stop(self):
        try:
            self.is_running = False
            # Allow time for cleanup
            time.sleep(0.5)
        except Exception as e:
            print(f"Error stopping downloader: {str(e)}")

    def toggle_pause(self):
        self.is_paused = not self.is_paused

    def _format_selection_callback(self, ctx):
        formats = ctx.get('formats', [])
        if formats and self.progress_callback:
            selected_format = next((f for f in formats if f.get('selected')), None)
            if selected_format:
                quality = selected_format.get('height', 'unknown')
                format_note = selected_format.get('format_note', '')
                self.progress_callback(-1, f"Selected quality: {quality}p {format_note}", "")

class VideoDownloader(BaseDownloader):
    def download(self):
        if not utils.validate_url(self.url):
            raise ValueError("Invalid YouTube URL")
            
        utils.create_download_directory(self.output_path)
        
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                if self.progress_callback:
                    self.progress_callback(0, info.get('title', ''), info.get('thumbnail', ''))
                ydl.download([self.url])
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")

class PlaylistDownloader(BaseDownloader):
    def download_playlist(self):
        if not utils.validate_url(self.url):
            raise ValueError("Invalid YouTube playlist URL")
            
        utils.create_download_directory(self.output_path)
        
        try:
            with yt_dlp.YoutubeDL({**self.ydl_opts, 'extract_flat': True}) as ydl:
                playlist_info = ydl.extract_info(self.url, download=False)
                if not playlist_info or not playlist_info.get('entries'):
                    raise ValueError("No videos found in playlist")

                entries = [entry for entry in playlist_info['entries'] if entry is not None]
                total_videos = len(entries)
                
                if self.progress_callback:
                    self.progress_callback(0, f"Found {total_videos} videos in playlist", "")

                for index, entry in enumerate(entries, 1):
                    if not self.is_running:
                        break
                        
                    if not entry or not entry.get('id'):
                        continue

                    video_url = f"https://youtube.com/watch?v={entry['id']}"
                    try:
                        if self.progress_callback:
                            self.progress_callback(0, f"[{index}/{total_videos}] {entry.get('title', 'Unknown')}", 
                                                entry.get('thumbnail', ''))
                        
                        with yt_dlp.YoutubeDL(self.ydl_opts) as video_ydl:
                            video_ydl.download([video_url])
                            
                        time.sleep(2)  # Increased delay between videos
                        
                    except Exception as e:
                        print(f"Error downloading video {index}: {str(e)}")
                        if self.progress_callback:
                            self.progress_callback(-1, f"Skipped video {index} due to error", "")
                        time.sleep(1)
                        continue

        except Exception as e:
            raise Exception(f"Playlist download failed: {str(e)}")