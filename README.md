# IKUMPlay 🎤

IKUMPlay is a **terminal-based karaoke machine** built with Python.  
It lets you search, download, and play karaoke tracks directly from YouTube — complete with synchronized lyrics display.

---

## ✨ Features
- 🔎 **Search YouTube** for karaoke tracks automatically.
- 🎶 **Download & Convert** audio to MP3 format.
- 🎤 **Vocal Remover**: separates vocals from instrumentals for karaoke-style playback.
- 📜 **Lyrics Support** (via synced lyrics API).
- 🖥️ **Terminal UI** powered by [Rich](https://github.com/Textualize/rich).
- 🗑️ **Auto Cleanup**: downloaded files are deleted after playback.

---

## 📦 Requirements
Make sure you have the following installed:

- Python 3.8+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [pygame](https://www.pygame.org/)
- [scipy](https://scipy.org/)
- [rich](https://github.com/Textualize/rich)
- [spleeter](https://github.com/deezer/spleeter) (for vocal removal)
- [syncedlyrics](https://pypi.org/project/syncedlyrics/)
- [spotipy](https://spotipy.readthedocs.io/en/2.23.0/)

Install all dependencies:
```bash
pip install -r requirements.txt
```

---

## 🚀 Usage
Run the main script from your terminal:

```bash
python main.py
```

You will be prompted to enter the **song name**. IKUMPlay will:
1. Search Spotify to extract the song details.
2. Search YouTube for a karaoke version.
3. Download the track as MP3.
4. Remove vocals (if necessary).
5. Display lyrics in sync.
6. Play the accompaniment through your speakers.

---

## 🗂️ Project Structure
```
IKUMPlay/
│── main.py               # Entry point
│── downloads/            # Temporary downloaded files
│── requirements.txt      # Python dependencies
│── README.md             # This file
```

---

## 🧹 Cleanup
All temporary files in `downloads/` are automatically deleted after playback.  
You can also manually clear the folder if needed:
```bash
rm -rf downloads/*
```

---

## 📜 Credits
Designed and Developed by Tsetsegchimeg, 최종우 and Prithwis Das

---

## 🙌 Acknowledgements
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for downloading YouTube audio.
- [Spleeter](https://github.com/deezer/spleeter) for source separation.
- [Rich](https://github.com/Textualize/rich) for terminal UI.
- [SyncedLyrics](https://pypi.org/project/syncedlyrics/) for lyric fetching.
- [Spotipy](https://spotipy.readthedocs.io/) for Spotify API integration.

Enjoy your karaoke night! 🎉
