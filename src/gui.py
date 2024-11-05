from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLineEdit, QPushButton, QComboBox, 
                           QProgressBar, QLabel, QFileDialog, QTextEdit, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QIcon, QPalette, QColor, QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from . import config
from .downloader import PlaylistDownloader, VideoDownloader
import sys
import os
import urllib.request
import time
from . import utils
import traceback

class DownloaderThread(QThread):
    progress_updated = pyqtSignal(int, str, str)
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
            downloader_class = PlaylistDownloader if self.is_playlist else VideoDownloader
            self.downloader = downloader_class(
                self.url,
                self.output_path,
                self.resolution,
                self.audio_only,
                self.audio_quality,
                self.audio_format
            )
            self.downloader.progress_callback = self._on_progress
            
            try:
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
                time.sleep(0.5)
            self.wait(2000)
            if self.isRunning():
                self.terminate()
                self.wait(1000)
        except Exception as e:
            print(f"Error stopping thread: {str(e)}")
        finally:
            if self.isRunning():
                self.terminate()

    def _on_progress(self, percentage, title, thumbnail):
        if self.is_running:
            self.progress_updated.emit(percentage, title, thumbnail)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)  # Memory cleanup
        self.setWindowTitle("YouTube Playlist Downloader")
        self.setMinimumSize(800, 600)
        
        # Cache commonly used widgets
        self._setup_cache()
        self.setup_ui()
        
    def _setup_cache(self):
        self._progress_bars = {}
        self._labels = {}

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLineEdit, QComboBox, QTextEdit {
                background-color: #3b3b3b;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0a3d91;
            }
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #1565c0;
            }
        """)
        additional_style = """
            QCheckBox {
                color: #ffffff;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #555555;
                border-radius: 3px;
                background-color: #2b2b2b;
            }
            QCheckBox::indicator:checked {
                background-color: #1565c0;
                border-color: #1565c0;
            }
            QCheckBox::indicator:hover {
                border-color: #1565c0;
            }
        """
        self.setStyleSheet(self.styleSheet() + additional_style)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # URL Input
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter YouTube playlist URL")
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)

        # Output Path
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setText(config.DEFAULT_DOWNLOAD_PATH)
        self.path_input.setReadOnly(True)
        path_layout.addWidget(self.path_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_output_path)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        # Resolution Selection
        res_layout = QHBoxLayout()
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(config.SUPPORTED_RESOLUTIONS)
        self.resolution_combo.setCurrentText(config.DEFAULT_RESOLUTION)
        res_layout.addWidget(QLabel("Resolution:"))
        res_layout.addWidget(self.resolution_combo)
        res_layout.addStretch()
        layout.addLayout(res_layout)

        # Audio Options
        audio_layout = QHBoxLayout()
        
        self.audio_only_check = QCheckBox("Convert to MP3")
        self.audio_only_check.stateChanged.connect(self.toggle_audio_options)
        audio_layout.addWidget(self.audio_only_check)
        
        self.audio_quality_combo = QComboBox()
        self.audio_quality_combo.addItems(config.SUPPORTED_AUDIO_QUALITIES.keys())
        self.audio_quality_combo.setCurrentText(config.DEFAULT_AUDIO_QUALITY)
        self.audio_quality_combo.setEnabled(False)
        audio_layout.addWidget(QLabel("Audio Quality:"))
        audio_layout.addWidget(self.audio_quality_combo)

        # Add audio format selection
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(config.SUPPORTED_AUDIO_FORMATS.keys())
        self.audio_format_combo.setCurrentText(config.DEFAULT_AUDIO_FORMAT)
        self.audio_format_combo.setEnabled(False)
        audio_layout.addWidget(QLabel("Format:"))
        audio_layout.addWidget(self.audio_format_combo)

        audio_layout.addStretch()
        layout.addLayout(audio_layout)

        # Button Layout
        button_layout = QHBoxLayout()
        
        # Download Button
        self.download_btn = QPushButton("Start Download")
        self.download_btn.clicked.connect(self.start_download)
        button_layout.addWidget(self.download_btn)
        
        # Pause Button
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)
        button_layout.addWidget(self.pause_btn)
        
        # Stop Button
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_download)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        layout.addLayout(button_layout)

        # Progress Bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Thumbnail Label
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(160, 90)  # 16:9 ratio
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                background-color: #1e1e1e;
                border: 1px solid #555555;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.thumbnail_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Current Video Label
        self.current_video_label = QLabel("Current video: None")
        self.current_video_label.setStyleSheet("color: #1565c0; font-weight: bold;")
        layout.addWidget(self.current_video_label)

        # Status Log
        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        layout.addWidget(self.status_log)

        # Update the button styling section
        button_style = """
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 100px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #0a3d91;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
            QPushButton#stopBtn {
                background-color: #c62828;
            }
            QPushButton#stopBtn:hover {
                background-color: #d32f2f;
            }
            QPushButton#stopBtn:pressed {
                background-color: #b71c1c;
            }
            QPushButton#pauseBtn {
                background-color: #f57c00;
            }
            QPushButton#pauseBtn:hover {
                background-color: #fb8c00;
            }
            QPushButton#pauseBtn:pressed {
                background-color: #ef6c00;
            }
        """
        self.setStyleSheet(self.styleSheet() + button_style)

        # Update button creation
        self.download_btn.setObjectName("downloadBtn")
        self.pause_btn.setObjectName("pauseBtn")
        self.stop_btn.setObjectName("stopBtn")

        # Add to MainWindow class setup_ui method after URL input:
        url_type_layout = QHBoxLayout()
        self.url_type_label = QLabel("URL Type:")
        self.url_type_combo = QComboBox()
        self.url_type_combo.addItems(["Single Video", "Playlist"])
        url_type_layout.addWidget(self.url_type_label)
        url_type_layout.addWidget(self.url_type_combo)
        url_type_layout.addStretch()
        layout.addLayout(url_type_layout)

    def browse_output_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.path_input.setText(folder)

    def toggle_pause(self):
        if not hasattr(self, 'downloader_thread') or not self.downloader_thread.isRunning():
            return
            
        if self.downloader_thread.downloader:
            self.downloader_thread.downloader.toggle_pause()
            is_paused = self.downloader_thread.downloader.is_paused
            self.pause_btn.setText("Resume" if is_paused else "Pause")
            self.log_status(f"Download {'paused' if is_paused else 'resumed'}")

    def start_download(self):
        if hasattr(self, 'downloader_thread') and self.downloader_thread.isRunning():
            self.stop_download()
            time.sleep(0.5)
        
        url = self.url_input.text()
        output_path = self.path_input.text()
        resolution = self.resolution_combo.currentText()

        if not url:
            self.log_status("Please enter a URL")
            return

        # Auto-detect URL type
        url_type = utils.get_url_type(url)
        if url_type == "invalid":
            self.log_status("Invalid YouTube URL")
            return

        self.download_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.pause_btn.setText("Pause")
        self.progress_bar.setValue(0)
        self.current_video_label.setText("Current video: None")
        self.thumbnail_label.clear()
        
        is_playlist = url_type == "playlist"
        
        self.downloader_thread = DownloaderThread(
            url=url,
            output_path=output_path,
            resolution=resolution,
            audio_only=self.audio_only_check.isChecked(),
            audio_quality=self.audio_quality_combo.currentText(),
            audio_format=self.audio_format_combo.currentText(),
            is_playlist=is_playlist
        )
        self.downloader_thread.progress_updated.connect(self.update_progress)
        self.downloader_thread.status_updated.connect(self.log_status)
        self.downloader_thread.download_complete.connect(self.download_finished)
        self.downloader_thread.error_occurred.connect(self.handle_error)
        self.downloader_thread.start()

    def handle_error(self, error_msg):
        self.log_status(f"Error: {error_msg}")
        self.download_finished()
        QMessageBox.critical(self, "Error", str(error_msg))

    def update_progress(self, value, video_title, thumbnail_url):
        try:
            if value == -1:  # Quality information
                self.log_status(video_title)  # video_title contains quality info
                return
                
            self.progress_bar.setValue(value)
            if video_title:
                if "[" in video_title:  # Playlist progress
                    self.current_video_label.setText(f"Current: {video_title}")
                else:
                    self.current_video_label.setText(f"Current video: {video_title}")
                self.log_status(f"Downloading: {video_title} - {value}%")
            
            if thumbnail_url and value == 0:
                try:
                    data = urllib.request.urlopen(thumbnail_url).read()
                    pixmap = QPixmap()
                    pixmap.loadFromData(data)
                    scaled_pixmap = pixmap.scaled(
                        self.thumbnail_label.size(), 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.thumbnail_label.setPixmap(scaled_pixmap)
                except Exception as e:
                    self.log_status(f"Failed to load thumbnail: {str(e)}")
                    self.thumbnail_label.clear()
        except Exception as e:
            self.log_status(f"Error updating progress: {str(e)}")

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
        try:
            if hasattr(self, 'downloader_thread'):
                if self.downloader_thread.isRunning():
                    self.downloader_thread.stop()
                    self.downloader_thread.wait(2000)  # Wait up to 2 seconds
                    if self.downloader_thread.isRunning():
                        self.downloader_thread.terminate()
                        self.downloader_thread.wait()
                self.log_status("Download stopped by user")
                self.download_finished()
        except Exception as e:
            self.log_status(f"Error stopping download: {str(e)}")
            self.download_finished()

    def toggle_audio_options(self, state):
        is_audio = state == Qt.CheckState.Checked.value
        self.audio_quality_combo.setEnabled(is_audio)
        self.audio_format_combo.setEnabled(is_audio)
        self.resolution_combo.setEnabled(not is_audio)

    def closeEvent(self, event):
        try:
            if hasattr(self, 'downloader_thread'):
                if self.downloader_thread.isRunning():
                    self.stop_download()
            event.accept()
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 