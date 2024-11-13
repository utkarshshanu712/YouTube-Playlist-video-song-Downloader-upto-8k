from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLineEdit, QPushButton, QComboBox, 
                           QProgressBar, QLabel, QFileDialog, QTextEdit, QCheckBox, QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPalette, QColor, QPixmap
import sys
import os
import urllib.request
import time
from . import config
from .downloader import PlaylistDownloader, VideoDownloader
from . import utils

class DownloaderThread(QThread):
    progress_updated = pyqtSignal(int, str, str, float)
    download_complete = pyqtSignal()
    status_updated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, url, output_path, resolution, audio_only, audio_quality, audio_format, is_playlist=False):
        super().__init__()
        self.url = url
        self.output_path = output_path
        self.resolution = resolution
        self.audio_only = audio_only
        self.audio_quality = audio_quality
        self.audio_format = audio_format
        self.is_playlist = is_playlist
        self.downloader = None
        self.is_running = True
        
    def run(self):
        try:
            # Create appropriate downloader
            downloader_class = PlaylistDownloader if self.is_playlist else VideoDownloader
            self.downloader = downloader_class(
                self.url,
                self.output_path,
                self.resolution,
                self.audio_only,
                self.audio_quality,
                self.audio_format
            )
            
            # Set progress callback
            self.downloader.progress_callback = self._on_progress
            
            try:
                # Start download
                if self.is_playlist:
                    self.downloader.download_playlist()
                else:
                    self.downloader.download()
                    
                if self.is_running:
                    self.download_complete.emit()
                    
            except Exception as e:
                self.error_occurred.emit(str(e))
                
        except Exception as e:
            self.error_occurred.emit(f"Failed to initialize downloader: {str(e)}")

    def stop(self):
        try:
            self.is_running = False
            if self.downloader:
                self.downloader.stop()
            self.wait(2000)  # Wait up to 2 seconds
            if self.isRunning():
                self.terminate()
        except Exception as e:
            print(f"Error stopping thread: {str(e)}")

    def _on_progress(self, progress: int, status: str, thumbnail: str, speed: float):
        if not self.is_running:
            return
        
        # Format speed to show only 1 decimal place
        formatted_speed = f"{speed:.1f}" if speed > 0 else "0.0"
        self.progress_updated.emit(progress, status, thumbnail, float(formatted_speed))

    def toggle_pause(self):
        if self.downloader:
            self.downloader.toggle_pause()
            return self.downloader.is_paused
        return False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Playlist Downloader")
        self.setMinimumSize(900, 700)
        self.downloader_thread = None
        
        # Setup UI without FFmpeg checks
        self.setup_ui()
        self.apply_styles()

    def apply_styles(self):
        button_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """
        self.setStyleSheet(button_style)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # URL Section
        url_group = QGroupBox("Video URL")
        url_layout = QVBoxLayout()
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter YouTube URL...")
        self.url_input.textChanged.connect(self.url_changed)
        url_layout.addWidget(self.url_input)
        
        # Format Detection Button
        self.detect_formats_btn = QPushButton("Detect Available Formats")
        self.detect_formats_btn.setEnabled(False)
        self.detect_formats_btn.clicked.connect(self.detect_formats)
        url_layout.addWidget(self.detect_formats_btn)
        
        url_group.setLayout(url_layout)
        layout.addWidget(url_group)

        # Options Section
        options_group = QGroupBox("Download Options")
        options_layout = QHBoxLayout()
        
        # Video Quality
        video_layout = QVBoxLayout()
        video_layout.addWidget(QLabel("Video Quality:"))
        self.video_quality_combo = QComboBox()
        self.video_quality_combo.setEnabled(False)
        video_layout.addWidget(self.video_quality_combo)
        options_layout.addLayout(video_layout)

        # Audio Options
        audio_layout = QVBoxLayout()
        self.audio_only_check = QCheckBox("Audio Only")
        self.audio_only_check.stateChanged.connect(self.toggle_audio_options)
        audio_layout.addWidget(self.audio_only_check)
        
        audio_quality_layout = QVBoxLayout()
        audio_quality_layout.addWidget(QLabel("Audio Quality:"))
        self.audio_quality_combo = QComboBox()
        self.audio_quality_combo.setEnabled(False)
        audio_quality_layout.addWidget(self.audio_quality_combo)
        
        audio_format_layout = QVBoxLayout()
        audio_format_layout.addWidget(QLabel("Audio Format:"))
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.setEnabled(False)
        audio_format_layout.addWidget(self.audio_format_combo)
        
        audio_layout.addLayout(audio_quality_layout)
        audio_layout.addLayout(audio_format_layout)
        options_layout.addLayout(audio_layout)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Progress Section
        progress_group = QGroupBox("Download Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)
        
        self.speed_label = QLabel("Speed: 0 MB/s")
        progress_layout.addWidget(self.speed_label)
        
        self.current_video_label = QLabel("Current video: None")
        progress_layout.addWidget(self.current_video_label)
        
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(320, 180)
        self.thumbnail_label.setScaledContents(True)
        progress_layout.addWidget(self.thumbnail_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Control Buttons
        controls_layout = QHBoxLayout()
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setEnabled(False)
        
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_download)
        self.stop_btn.setEnabled(False)
        
        controls_layout.addWidget(self.download_btn)
        controls_layout.addWidget(self.pause_btn)
        controls_layout.addWidget(self.stop_btn)
        layout.addLayout(controls_layout)

        # Status Log
        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setMaximumHeight(150)
        layout.addWidget(self.status_log)

        # Initialize other properties
        self.downloader_thread = None
        self.is_paused = False

        # Add download location section
        location_group = QGroupBox("Download Location")
        location_layout = QHBoxLayout()
        
        self.path_input = QLineEdit()
        self.path_input.setText(config.DEFAULT_DOWNLOAD_PATH)
        location_layout.addWidget(self.path_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_location)
        location_layout.addWidget(browse_btn)
        
        location_group.setLayout(location_layout)
        layout.addWidget(location_group)

        # Audio format options
        self.audio_format_combo.addItems(['m4a', 'mp3', 'wav', 'aac'])
        self.audio_format_combo.setCurrentText('m4a')  # Set M4A as default
        
        # Audio quality options
        self.audio_quality_combo.addItems(['64kbps', '96kbps', '128kbps', '192kbps', '256kbps', '320kbps'])
        self.audio_quality_combo.setCurrentText('192kbps')  # Default quality

        # Add GitHub link at the bottom
        github_link = QLabel()
        github_link.setText('<a href="https://github.com/utkarshshanu712">GitHub: @utkarshshanu712</a>')
        github_link.setOpenExternalLinks(True)
        github_link.setAlignment(Qt.AlignmentFlag.AlignRight)
        github_link.setStyleSheet("color: #0366d6; margin: 5px;")
        
        # Add to layout
        layout.addWidget(github_link)

    def browse_location(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Download Location",
            self.path_input.text() or os.path.expanduser("~")
        )
        if directory:
            self.path_input.setText(directory)

    def browse_output_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.path_input.setText(folder)

    def toggle_pause(self):
        if self.downloader_thread and self.downloader_thread.isRunning():
            try:
                is_paused = self.downloader_thread.toggle_pause()
                self.pause_btn.setText("Resume" if is_paused else "Pause")
                self.pause_btn.setStyleSheet(
                    "background-color: #4CAF50;" if not is_paused else "background-color: #FFA000;"
                )
                self.log_status("Download paused" if is_paused else "Download resumed")
            except Exception as e:
                self.log_status(f"Error toggling pause: {str(e)}")

    def start_download(self):
        try:
            url = self.url_input.text().strip()
            output_path = self.path_input.text().strip()
            
            if not url or not output_path:
                self.log_status("Please enter both URL and output path")
                return
            
            utils.create_download_directory(output_path)
            
            self.downloader_thread = DownloaderThread(
                url=url,
                output_path=output_path,
                resolution=self.video_quality_combo.currentText(),
                audio_only=self.audio_only_check.isChecked(),
                audio_quality=self.audio_quality_combo.currentText(),
                audio_format=self.audio_format_combo.currentText(),
                is_playlist=utils.get_url_type(url) == "playlist"
            )
            
            self.downloader_thread.progress_updated.connect(self.update_progress)
            self.downloader_thread.download_complete.connect(self.download_finished)
            self.downloader_thread.error_occurred.connect(self.handle_error)
            self.downloader_thread.status_updated.connect(self.log_status)
            
            # Enable control buttons
            self.download_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.pause_btn.setText("Pause")
            
            self.downloader_thread.start()
            
        except Exception as e:
            self.log_status(f"Error starting download: {str(e)}")
            self.download_finished()

    def handle_error(self, error_msg):
        self.log_status(f"Error: {error_msg}")
        self.download_finished()
        QMessageBox.critical(self, "Error", str(error_msg))

    def update_progress(self, progress: int, status: str, thumbnail: str, speed: float):
        if progress >= 0:
            self.progress_bar.setValue(int(progress))
        
        if status:
            self.current_video_label.setText(f"Current video: {status}")
        
        if speed < 0.01:
            self.speed_label.setText("Speed: 0 MB/s")
        else:
            self.speed_label.setText(f"Speed: {speed:.2f} MB/s")
        
        # Simplified thumbnail loading
        if thumbnail and thumbnail.startswith('http'):
            try:
                data = urllib.request.urlopen(thumbnail).read()
                pixmap = QPixmap()
                pixmap.loadFromData(data)
                scaled_pixmap = pixmap.scaled(320, 180, Qt.AspectRatioMode.KeepAspectRatio)
                self.thumbnail_label.setPixmap(scaled_pixmap)
            except:
                pass

    def log_status(self, status):
        self.status_log.append(status)

    def download_finished(self):
        self.download_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        self.current_video_label.setText("Current video: None")
        self.log_status("Download completed!")
        self.thumbnail_label.clear()

    def stop_download(self):
        if self.downloader_thread and self.downloader_thread.isRunning():
            try:
                self.stop_btn.setEnabled(False)  # Prevent multiple clicks
                self.stop_btn.setText("Stopping...")
                self.downloader_thread.stop()
                self.log_status("Download stopped")
                self.download_finished()
            except Exception as e:
                self.log_status(f"Error stopping download: {str(e)}")

    def toggle_audio_options(self, state):
        is_audio = state == Qt.CheckState.Checked.value
        self.audio_quality_combo.setEnabled(is_audio)
        self.audio_format_combo.setEnabled(is_audio)
        self.video_quality_combo.setEnabled(not is_audio)

    def closeEvent(self, event):
        try:
            if hasattr(self, 'downloader_thread'):
                if self.downloader_thread.isRunning():
                    self.stop_download()
            event.accept()
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
            event.accept()

    def url_changed(self, text):
        is_valid = utils.validate_url(text)
        self.detect_formats_btn.setEnabled(is_valid)
        self.download_btn.setEnabled(False)
        self.audio_only_check.setEnabled(is_valid)
        
    def detect_formats(self):
        if not self.url_input.text().strip():
            self.log_status("Please enter a URL first")
            return
        
        self.log_status("Detecting formats...")
        self.detect_formats_btn.setEnabled(False)
        self.download_btn.setEnabled(False)
        
        # Create format detection thread
        class FormatDetectionThread(QThread):
            formats_detected = pyqtSignal(list, list)
            error_occurred = pyqtSignal(str)
            
            def __init__(self, url):
                super().__init__()
                self.url = url
                
            def run(self):
                try:
                    downloader = VideoDownloader(self.url)
                    video_formats, audio_formats = downloader.get_available_formats()
                    self.formats_detected.emit(video_formats, audio_formats)
                except Exception as e:
                    self.error_occurred.emit(str(e))
        
        # Initialize and connect thread
        self.format_thread = FormatDetectionThread(self.url_input.text().strip())
        self.format_thread.formats_detected.connect(self._update_formats)
        self.format_thread.error_occurred.connect(self.handle_error)
        self.format_thread.start()

    def _update_formats(self, video_formats, audio_formats):
        # Update video qualities
        self.video_quality_combo.clear()
        self.video_quality_combo.addItems(video_formats)
        self.video_quality_combo.setEnabled(True)
        
        # Update audio options
        audio_qualities = {f['quality'] for f in audio_formats}
        audio_formats_list = {f['format'].upper() for f in audio_formats}
        
        self.audio_quality_combo.clear()
        self.audio_format_combo.clear()
        
        self.audio_quality_combo.addItems(sorted(audio_qualities, key=lambda x: int(x[:-4]), reverse=True))
        self.audio_format_combo.addItems(sorted(audio_formats_list))
        
        self.detect_formats_btn.setEnabled(True)
        self.download_btn.setEnabled(True)

    def download_audio(self):
        self.audio_only = True
        self.start_download()

    def check_ffmpeg(self):
        if not utils.check_ffmpeg():
            reply = QMessageBox.question(
                self,
                "FFmpeg Required",
                "FFmpeg is required for proper video/audio quality selection.\n"
                "Would you like to download and install FFmpeg now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.log_status("Downloading FFmpeg...")
                if utils.download_ffmpeg():
                    self.log_status("FFmpeg installed successfully")
                else:
                    self.log_status("Failed to install FFmpeg. Some features may not work properly.")

    def show_about(self):
        about_text = """
        <h2>YouTube Playlist Downloader</h2>
        <p>Version 1.0.0</p>
        <p>A powerful YouTube video and playlist downloader with support for high-quality downloads.</p>
        <p>Created by Utkarsh Kumar</p>
        <p><a href="https://github.com/utkarshshanu712">GitHub: @utkarshshanu712</a></p>
        <p>Copyright © 2024 All rights reserved.</p>
        """
        
        QMessageBox.about(self, "About", about_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 