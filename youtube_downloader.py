import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QProgressBar, QTextEdit, 
                             QComboBox, QFileDialog, QGroupBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import yt_dlp
import traceback

class DownloaderThread(QThread):
    progress_signal = pyqtSignal(int)
    complete_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    log_signal = pyqtSignal(str)

    def __init__(self, url, save_path, format_type, quality):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.format_type = format_type  # 'audio' lub 'video'
        self.quality = quality

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            # Czasami brak total_bytes, dlatego sprawdzamy czy istnieje
            if d.get('total_bytes'):
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes', 0)
                if total > 0:
                    percentage = int(downloaded / total * 100)
                    self.progress_signal.emit(percentage)
            elif d.get('total_bytes_estimate'):
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes_estimate', 0)
                if total > 0:
                    percentage = int(downloaded / total * 100)
                    self.progress_signal.emit(percentage)
        
        elif d['status'] == 'finished':
            self.log_signal.emit(f"Pobieranie zakończone, trwa przetwarzanie...")

    def run(self):
        try:
            self.log_signal.emit(f"Łączenie z: {self.url}")
            
            # Podstawowa konfiguracja yt-dlp
            ydl_opts = {
                'progress_hooks': [self.progress_hook],
                'outtmpl': os.path.join(self.save_path, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True
            }
            
            # Konfiguracja w zależności od formatu i jakości
            if self.format_type == "audio":
                self.log_signal.emit(f"Przygotowanie do pobrania audio w jakości: {self.quality}")
                
                # Mapowanie jakości audio na bitrate
                audio_quality = {
                    "Najwyższa": "0",  # Najlepsza dostępna jakość
                    "Średnia": "128",
                    "Najniższa": "64" 
                }
                
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': audio_quality.get(self.quality, "128"),
                    }],
                })
                
            else:  # video
                self.log_signal.emit(f"Przygotowanie do pobrania video w jakości: {self.quality}")
                
                # Poprawione mapowanie jakości video z mniej restrykcyjnymi formatami
                if self.quality == "Najwyższa":
                    format_spec = 'bestvideo+bestaudio/best'
                elif self.quality == "720p":
                    format_spec = 'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
                else:  # 480p lub niższa
                    format_spec = 'bestvideo[height<=480]+bestaudio/best[height<=480]/best'
                
                ydl_opts.update({
                    'format': format_spec,
                    'merge_output_format': 'mp4',
                })
            
            # Pobierz informacje o wideo przed pobraniem
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(self.url, download=False)
                title = info.get('title', 'unknown_title')
                self.log_signal.emit(f"Znaleziono film: {title}")
            
            # Pobierz wideo
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            
            # Ustal prawdziwą ścieżkę pliku (może być trudne ze względu na przetwarzanie)
            if self.format_type == "audio":
                ext = "mp3"
            else:
                ext = "mp4"
                
            expected_filename = os.path.join(self.save_path, f"{title}.{ext}")
            expected_filename = expected_filename.replace('/', '_').replace('\\', '_')
            
            self.complete_signal.emit(f"Plik został pobrany jako: {expected_filename}")
                
        except Exception as e:
            self.error_signal.emit(f"Wystąpił błąd: {str(e)}")
            self.log_signal.emit(traceback.format_exc())


class YouTubeDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pobieracz filmów z YouTube")
        self.setMinimumSize(600, 500)
        
        # Główny widget i layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Sekcja URL
        url_group = QGroupBox("Adres filmu")
        url_layout = QVBoxLayout()
        url_group.setLayout(url_layout)
        
        url_input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Wklej adres URL filmu z YouTube")
        url_input_layout.addWidget(self.url_input)
        
        url_layout.addLayout(url_input_layout)
        main_layout.addWidget(url_group)
        
        # Sekcja katalogu docelowego
        path_group = QGroupBox("Katalog docelowy")
        path_layout = QHBoxLayout()
        path_group.setLayout(path_layout)
        
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        # Domyślna ścieżka do folderu Pobrane (Downloads)
        default_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.path_input.setText(default_path)
        
        self.browse_button = QPushButton("Przeglądaj...")
        self.browse_button.clicked.connect(self.browse_folder)
        
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_button)
        main_layout.addWidget(path_group)
        
        # Sekcja formatu i jakości
        format_group = QGroupBox("Format i jakość")
        format_layout = QHBoxLayout()
        format_group.setLayout(format_layout)
        
        format_left_layout = QVBoxLayout()
        format_right_layout = QVBoxLayout()
        
        # Wybór formatu
        format_label = QLabel("Format:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Audio (MP3)", "Video (MP4)"])
        self.format_combo.currentIndexChanged.connect(self.update_quality_options)
        format_left_layout.addWidget(format_label)
        format_left_layout.addWidget(self.format_combo)
        
        # Wybór jakości
        quality_label = QLabel("Jakość:")
        self.quality_combo = QComboBox()
        # Domyślne opcje dla audio
        self.quality_combo.addItems(["Najwyższa", "Średnia", "Najniższa"])
        format_right_layout.addWidget(quality_label)
        format_right_layout.addWidget(self.quality_combo)
        
        format_layout.addLayout(format_left_layout)
        format_layout.addLayout(format_right_layout)
        main_layout.addWidget(format_group)
        
        # Przycisk pobierania
        self.download_button = QPushButton("Pobierz")
        self.download_button.setMinimumHeight(40)
        self.download_button.clicked.connect(self.start_download)
        main_layout.addWidget(self.download_button)
        
        # Pasek postępu
        progress_group = QGroupBox("Postęp pobierania")
        progress_layout = QVBoxLayout()
        progress_group.setLayout(progress_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        main_layout.addWidget(progress_group)
        
        # Okno logu
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        main_layout.addWidget(log_group)
        
        # Konfiguracja layoutu
        main_layout.setStretch(5, 1)  # Log ma elastyczną wysokość
        
        # Inicjalizacja
        self.downloader = None
        self.log("Aplikacja gotowa do użycia.")
        
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Wybierz katalog docelowy")
        if folder:
            self.path_input.setText(folder)
            self.log(f"Wybrano katalog: {folder}")
    
    def update_quality_options(self):
        self.quality_combo.clear()
        if self.format_combo.currentText() == "Audio (MP3)":
            self.quality_combo.addItems(["Najwyższa", "Średnia", "Najniższa"])
        else:
            self.quality_combo.addItems(["Najwyższa", "720p", "480p lub niższa"])
    
    def log(self, message):
        self.log_output.append(message)
        # Przewiń do końca
        scroll_bar = self.log_output.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())
    
    def start_download(self):
        url = self.url_input.text().strip()
        save_path = self.path_input.text()
        
        if not url:
            self.log("Błąd: Podaj adres URL filmu")
            return
        
        if not save_path or not os.path.exists(save_path):
            self.log("Błąd: Wybierz prawidłowy katalog docelowy")
            return
        
        # Ustal format i jakość
        format_text = self.format_combo.currentText()
        format_type = "audio" if "Audio" in format_text else "video"
        quality = self.quality_combo.currentText()
        
        # Wyłącz przycisk podczas pobierania
        self.download_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Utwórz i uruchom wątek pobierania
        self.downloader = DownloaderThread(url, save_path, format_type, quality)
        self.downloader.progress_signal.connect(self.update_progress)
        self.downloader.complete_signal.connect(self.download_complete)
        self.downloader.error_signal.connect(self.download_error)
        self.downloader.log_signal.connect(self.log)
        self.downloader.start()
    
    def update_progress(self, percentage):
        self.progress_bar.setValue(percentage)
        # Aktualizuj log tylko co 10%
        if percentage % 10 == 0:
            self.log(f"Postęp: {percentage}%")
    
    def download_complete(self, message):
        self.log(message)
        self.log("Pobieranie zakończone pomyślnie!")
        self.download_button.setEnabled(True)
    
    def download_error(self, error_message):
        self.log(f"Błąd: {error_message}")
        self.download_button.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Styl dla lepszego wyglądu na Windows
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec())