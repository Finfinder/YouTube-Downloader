# YouTube Downloader

Aplikacja do pobierania filmów z YouTube w formatach audio (MP3) i video (MP4) z graficznym interfejsem użytkownika.

## Funkcje

- **Pobieranie audio (MP3)** w różnych jakościach (Najwyższa, Średnia, Najniższa)
- **Pobieranie video (MP4)** w różnych rozdzielczościach (Najwyższa, 720p, 480p lub niższa)
- **Graficzny interfejs użytkownika** oparty na PyQt6
- **Pasek postępu** pobierania
- **Log aktywności** w czasie rzeczywistym
- **Wybór katalogu docelowego** dla pobranych plików

## Wymagania

- Python 3.7+
- PyQt6
- yt-dlp
- FFmpeg (wymagany dla konwersji audio)

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/Finfinder/youtube-downloader.git
cd youtube-downloader
```

2. Zainstaluj wymagane biblioteki:
```bash
pip install PyQt6 yt-dlp
```

3. Zainstaluj FFmpeg:
   - Windows: Pobierz z https://ffmpeg.org/download.html i dodaj do PATH
   - Linux: `sudo apt install ffmpeg`
   - macOS: `brew install ffmpeg`

## Użycie

Uruchom aplikację:
```bash
python youtube_downloader.py
```

1. Wklej URL filmu z YouTube
2. Wybierz katalog docelowy (domyślnie folder Pobrane)
3. Wybierz format (Audio MP3 lub Video MP4) i jakość
4. Kliknij "Pobierz"

## Autor

Rafał Trzepocki
