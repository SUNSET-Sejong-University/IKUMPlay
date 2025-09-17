import os, time
import numpy as np
from pygame import mixer
from scipy.io.wavfile import read
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align
from rich.live import Live
import yt_dlp
import re
import spotipy
import json
from spotipy.oauth2 import SpotifyClientCredentials


CLIENT_ID = "ab196aede1bc4799ae649981432632d0"
CLIENT_SECRET = "e631f38732ba4c608f2982bdb41f9cb4"

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))

console = Console()

def spectrogram(data, width=40, height=15):
    """Turn audio data into ASCII spectrogram bars."""
    if len(data) == 0:
        return ""
    chunk = np.abs(data[:width])
    chunk = (chunk / np.max(chunk)) * height
    lines = []
    for level in range(height, 0, -1):
        line = "".join("█" if c >= level else " " for c in chunk)
        lines.append(line)
    return "\n".join(lines)

def build_layout(song_name, lyrics, spectro_text):
    layout = Layout()

    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3),
    )

    # header
    layout["header"].update(
        Panel(Align.center(f"[bold green]♪ Now Playing: {song_name} ♪"))
    )

    # main split
    layout["main"].split_row(
        Layout(name="spectro", ratio=1),
        Layout(name="lyrics", ratio=1),
    )

    layout["spectro"].update(
        Panel(Align.center(spectro_text), title="Waveform", border_style="cyan")
    )
    layout["lyrics"].update(
        Panel("\n".join(lyrics), title="Lyrics", border_style="magenta")
    )

    # footer
    layout["footer"].update(
        Panel(Align.center("[yellow]Built with ❤️ by SUNSET-Sejong University")))
    
    return layout

def play_song(song_file, lyrics):
    # init mixer
    mixer.init()
    mixer.music.load(song_file)
    mixer.music.play()

    # also load wav for analysis
    wav_file = "temp.wav"
    os.system(f'ffmpeg -y -i "{song_file}" -ac 1 -ar 16000 "{wav_file}" >nul 2>&1')

    rate, audio = read(wav_file)
    audio = audio / np.max(np.abs(audio))  # normalize
    step = rate // 10  # ~0.1s per step

    with Live(console=console, refresh_per_second=10, screen=True) as live:
        pos = 0
        while mixer.music.get_busy():
            chunk = audio[pos:pos+step]
            spec = spectrogram(chunk, width=40, height=15)
            layout = build_layout(os.path.basename(song_file), lyrics, spec)
            live.update(layout)
            pos += step
            time.sleep(0.1)
        
def search_song(query):
    pattern = re.compile(query, re.IGNORECASE)

    results = sp.search(q=query, type="track", limit=20)
    tracks = results["tracks"]["items"]

    matches = []
    for track in tracks:
        title = track['name']
        artists = ", ".join(artist['name'] for artist in track['artists'])
        text = f"{title} {artists}"

        if pattern.search(text):
            matches.append((title, artists))
    
    return matches

def download_audio(query, output_dir="downloads"):
    os.makedirs(output_dir, exist_ok=True)
 
    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(f"🔎 Searching and downloading: {query}")
        info = ydl.extract_info(f"ytsearch1:{query} karaoke", download=True)
        filename = ydl.prepare_filename(info['entries'][0])
        mp3_file = os.path.splitext(filename)[0] + ".mp3"
        return mp3_file


if __name__ == "__main__":
    song_name = input("Enter the song name: ")
    results = search_song(song_name)
    if results:
        title, artists = results[0] if results else ("No match found", "", "")
        query = f"{title} by {artists}"
        song_file = download_audio(query)      
        print(f"✅ Downloaded: {song_file}")
        lyrics = [
            "Line 1 of lyrics...",
            "Line 2 of lyrics...",
            "Line 3 of lyrics..."
        ]
        play_song(song_file, lyrics)

    else:
        print("❌ No matching song found!")

