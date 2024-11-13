from tqdm import tqdm
import os
from typing import Optional
import yt_dlp
import time
from . import config
from . import utils

class BaseDownloader:
    SUPPORTED_AUDIO_FORMATS = ['m4a', 'mp3', 'wav', 'aac']
    
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
        self.download_speed = 0
        self.last_downloaded = 0
        self.speed_update_time = time.time()

        # Configure format selection based on FFmpeg availability
        ffmpeg_path = utils.get_ffmpeg_path()
        if not ffmpeg_path:
            raise RuntimeError("FFmpeg not found")
        
        # Base configuration
        self.ydl_opts = {
            'format_sort': ['res', 'codec:h264', 'size', 'br', 'fps'],
            'format_sort_force': True,
            'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self._progress_hook],
            'postprocessor_hooks': [self._post_hook],
            'ffmpeg_location': ffmpeg_path,
            'prefer_ffmpeg': True,
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
            'format_selection': self._format_selection_callback,
            'concurrent_fragment_downloads': 5,
            'buffersize': 1024 * 1024,
            'http_chunk_size': 10485760,
            'retries': 10,
            'fragment_retries': 10,
            'skip_unavailable_fragments': True,
            'keep_fragments': False,
            'overwrites': True
        }

    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                # Calculate progress
                if 'total_bytes' in d:
                    progress = d.get('downloaded_bytes', 0) / d['total_bytes'] * 100
                elif 'total_bytes_estimate' in d:
                    progress = d.get('downloaded_bytes', 0) / d['total_bytes_estimate'] * 100
                else:
                    progress = 0
                
                # Calculate speed
                speed = d.get('speed', 0)
                speed = speed / (1024 * 1024) if speed else 0.0  # Convert to MB/s
                
                # Get status
                status = d.get('filename', '').split('/')[-1]
                if self.audio_only:
                    status = f"Downloading audio: {status}"
                
                if self.progress_callback:
                    self.progress_callback(int(progress), status, d.get('thumbnail', ''), speed)
                    
            except Exception:
                pass
        elif d['status'] == 'finished':
            if self.progress_callback:
                self.progress_callback(-1, "Processing...", '', 0)

    def _post_hook(self, d):
        if d['status'] == 'finished':
            self.downloaded_files.add(d.get('filename', ''))
            if self.progress_callback:
                self.progress_callback(100, '', '', 0)

    def stop(self):
        self.is_running = False
        if self.progress_callback:
            self.progress_callback(-1, "Download stopped", "", 0)
        time.sleep(0.5)  # Allow time for cleanup

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.progress_callback:
            self.progress_callback(-1, 
                "Download paused" if self.is_paused else "Download resumed", 
                "", 0)
        return self.is_paused

    def _format_selection_callback(self, ctx):
        formats = ctx.get('formats', [])
        if formats and self.progress_callback:
            selected_format = next((f for f in formats if f.get('selected')), None)
            if selected_format:
                quality = selected_format.get('height', 'unknown')
                format_note = selected_format.get('format_note', '')
                self.progress_callback(-1, f"Selected quality: {quality}p {format_note}", "", 0)

    def get_available_formats(self):
        try:
            if self.is_playlist_url():
                # For playlists, check first video's formats
                with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                    playlist_info = ydl.extract_info(self.url, download=False)
                    if playlist_info and 'entries' in playlist_info:
                        first_video = next((e for e in playlist_info['entries'] if e), None)
                        if first_video:
                            video_url = f"https://youtube.com/watch?v={first_video['id']}"
                            return self._get_formats_for_url(video_url)
            else:
                return self._get_formats_for_url(self.url)
                    
        except Exception as e:
            raise Exception(f"Failed to detect formats: {str(e)}")

    def _get_formats_for_url(self, url):
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            # Get video formats
            video_formats = set()
            for f in formats:
                if f.get('height'):
                    video_formats.add(f"{f['height']}p")
            
            # Get audio formats
            audio_formats = []
            audio_qualities = ['64kbps', '96kbps', '128kbps', '192kbps', '256kbps', '320kbps']
            
            for fmt in self.SUPPORTED_AUDIO_FORMATS:
                for quality in audio_qualities:
                    audio_formats.append({
                        'format': fmt,
                        'quality': quality
                    })
            
            return sorted(video_formats, key=lambda x: int(x[:-1]), reverse=True), audio_formats

    def _select_format(self, info: dict) -> str:
        formats = info.get('formats', [])
        if not formats:
            raise ValueError("No formats available")

        target_height = int(self.resolution[:-1])
        
        # Get all video formats
        video_formats = []
        for f in formats:
            if (f.get('vcodec', 'none') != 'none' and 
                f.get('acodec', 'none') == 'none'):  # Video-only formats
                height = f.get('height', 0)
                if height == target_height:  # Exact match
                    video_formats.append(f)
                elif not video_formats and height < target_height:  # Fallback
                    video_formats.append(f)
        
        # Get audio formats
        audio_formats = [
            f for f in formats
            if (f.get('acodec', 'none') != 'none' and 
                f.get('vcodec', 'none') == 'none')
        ]
        
        if not video_formats or not audio_formats:
            # Try combined formats if separate streams aren't available
            combined_formats = [
                f for f in formats
                if (f.get('vcodec', 'none') != 'none' and 
                    f.get('acodec', 'none') != 'none')
            ]
            if combined_formats:
                # Sort by height and return best format
                combined_formats.sort(
                    key=lambda x: (x.get('height', 0), x.get('tbr', 0)),
                    reverse=True
                )
                return combined_formats[0]['format_id']
            raise ValueError(f"No suitable formats found for {self.resolution}")
        
        # Sort video formats by quality
        video_formats.sort(
            key=lambda x: (
                x.get('height', 0),
                x.get('fps', 0),
                x.get('tbr', 0),
                1 if x.get('vcodec', '').startswith('avc') else 0
            ),
            reverse=True
        )
        
        # Sort audio formats by quality
        audio_formats.sort(
            key=lambda x: (
                x.get('tbr', 0),
                1 if x.get('acodec', '') in ['mp4a', 'aac'] else 0
            ),
            reverse=True
        )
        
        best_video = video_formats[0]
        best_audio = audio_formats[0]
        
        return f"{best_video['format_id']}+{best_audio['format_id']}"

    def is_playlist_url(self):
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(self.url, download=False)
                return bool(info and info.get('_type') == 'playlist')
        except:
            return False

    def _get_best_formats(self, formats, target_height):
        # Get best video format
        video_formats = [
            f for f in formats 
            if (f.get('height') == target_height and
                f.get('vcodec') != 'none' and 
                f.get('acodec') == 'none')
        ]
        
        # Get best audio format
        audio_formats = [
            f for f in formats
            if (f.get('acodec') != 'none' and 
                f.get('vcodec') == 'none')
        ]
        
        if not video_formats:
            raise ValueError(f"No {target_height}p video format available")
        
        if not audio_formats:
            raise ValueError("No suitable audio format available")
            
        # Sort by quality
        video_formats.sort(
            key=lambda x: (
                x.get('tbr', 0),
                1 if x.get('vcodec', '').startswith('avc') else 0
            ),
            reverse=True
        )
        
        audio_formats.sort(
            key=lambda x: (
                x.get('asr', 0),
                x.get('tbr', 0),
                1 if x.get('acodec', '').startswith('mp4a') else 0
            ),
            reverse=True
        )
        
        return video_formats[0], audio_formats[0]

    def _get_ydl_opts(self):
        """Get yt-dlp options based on download settings"""
        ydl_opts = {
            'format': 'bestaudio' if self.audio_only else None,
            'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self._progress_hook],
            'format_selection_callback': self._format_selection_callback,
            'quiet': True,
            'no_warnings': True
        }
        
        if self.audio_only:
            ydl_opts.update({
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': self.audio_format.lower(),
                    'preferredquality': self.audio_quality.replace('kbps', '')
                }],
                'format': 'bestaudio/best',
                'postprocessor_args': [
                    '-ar', '44100'
                ]
            })
        else:
            target_height = int(self.resolution[:-1])
            ydl_opts['format'] = f'bestvideo[height={target_height}]+bestaudio/best[height<={target_height}]'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegVideoRemuxer',
                'preferedformat': 'mp4',
            }]
        
        return ydl_opts

class VideoDownloader(BaseDownloader):
    def download(self):
        if not utils.validate_url(self.url):
            raise ValueError("Invalid YouTube URL")
            
        utils.create_download_directory(self.output_path)
        
        try:
            if self.audio_only:
                # Audio-only configuration
                self.ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': self.audio_format.lower(),
                        'preferredquality': self.audio_quality.replace('kbps', '')
                    }],
                    'postprocessor_args': [
                        '-ar', '44100',
                        '-ac', '2',
                        '-b:a', f"{self.audio_quality.replace('kbps', '')}k"
                    ]
                })
            else:
                # Video configuration (existing code)
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(self.url, download=False)
                    formats = info.get('formats', [])
                    target_height = int(self.resolution[:-1])
                    video_format, audio_format = self._get_best_formats(formats, target_height)
                    self.ydl_opts.update({
                        'format': f"{video_format['format_id']}+{audio_format['format_id']}",
                        'postprocessors': [{
                            'key': 'FFmpegVideoRemuxer',
                            'preferedformat': 'mp4',
                        }]
                    })
            
            # Download with selected format
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                if self.progress_callback:
                    self.progress_callback(0, info.get('title', ''), info.get('thumbnail', ''), 0)
                ydl.download([self.url])
            
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")

class PlaylistDownloader(BaseDownloader):
    def download_playlist(self):
        if not utils.validate_url(self.url):
            raise ValueError("Invalid YouTube playlist URL")
        
        utils.create_download_directory(self.output_path)
        ffmpeg_path = utils.get_ffmpeg_path()
        
        try:
            # Configure format selection based on audio/video mode
            if self.audio_only:
                self.ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': self.audio_format.lower(),
                        'preferredquality': self.audio_quality.replace('kbps', '')
                    }],
                    'postprocessor_args': [
                        '-ar', '44100',
                        '-ac', '2',
                        '-b:a', f"{self.audio_quality.replace('kbps', '')}k"
                    ]
                })
            else:
                target_height = int(self.resolution[:-1])
                self.ydl_opts.update({
                    'format': f'bestvideo[height={target_height}]+bestaudio/best[height<={target_height}]',
                    'postprocessors': [{
                        'key': 'FFmpegVideoRemuxer',
                        'preferedformat': 'mp4',
                    }]
                })

            # Rest of the playlist download code remains the same
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                playlist_info = ydl.extract_info(self.url, download=False)
                if not playlist_info or 'entries' not in playlist_info:
                    raise ValueError("No videos found in playlist")
                
                entries = [entry for entry in playlist_info['entries'] if entry and entry.get('id')]
                total_videos = len(entries)
                
                if total_videos == 0:
                    raise ValueError("Playlist is empty")
                
                # Download videos
                for index, entry in enumerate(entries, 1):
                    if not self.is_running:
                        break
                    
                    try:
                        video_url = f"https://youtube.com/watch?v={entry['id']}"
                        
                        # Get video info for progress display
                        with yt_dlp.YoutubeDL({'quiet': True}) as info_ydl:
                            video_info = info_ydl.extract_info(video_url, download=False)
                            title = video_info.get('title', 'Unknown')
                        
                        if self.progress_callback:
                            self.progress_callback(
                                ((index-1) * 100) // total_videos,
                                f"[{index}/{total_videos}] {title}", 
                                video_info.get('thumbnail', ''),
                                0
                            )
                        
                        # Update output template
                        self.ydl_opts['outtmpl'] = os.path.join(
                            self.output_path,
                            f"{index:03d}_%(title)s.%(ext)s"
                        )
                        
                        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                            ydl.download([video_url])
                        
                    except Exception as e:
                        print(f"Error downloading video {index}: {str(e)}")
                        continue
                
                if self.progress_callback:
                    self.progress_callback(100, "Playlist download complete", "", 0)
                    
        except Exception as e:
            raise Exception(f"Playlist download failed: {str(e)}")