import sys, os, time
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
from syncedlyrics import *
import subprocess
import shutil

#Detect platform
ON_WINDOWS = os.name == "nt"

if ON_WINDOWS:
    import msvcrt
else:
    import curses
    import threading

CLIENT_ID = "ab196aede1bc4799ae649981432632d0"
CLIENT_SECRET = "e631f38732ba4c608f2982bdb41f9cb4"
PITCH_LEVELS = [-2, -1, 0, 1, 2]  # semitone shifts
current_pitch_index = 2           #always starting at 0 semitone

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))

console = Console()

def spectrogram(data, width=40, height=None):
    """Turn audio data into ASCII spectrogram bars."""  
    if len(data) == 0:
        return ""
    if height is None:
        height = max(5, console.size.height - 10)
    chunk = np.abs(data[:width])
    chunk = (chunk / np.max(chunk)) * height
    lines = []
    for level in range(height, 0, -1):
        line = "".join("█" if c >= level else " " for c in chunk)
        lines.append(line)
    return "\n".join(lines)


def build_layout(song_name, lyrics, spectro_text, disc_frame):
    layout = Layout()

    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="controls", size=3),
        Layout(name="footer", size=3),
    )

    # header
    layout["header"].update(
        Panel(Align.center(f"[bold green]♪ Now Playing: {song_name} ♪"))
    )

    # main split
    layout["main"].split_row(
        Layout(name="ascii-disc", ratio=1),
        Layout(name="lyrics", ratio=1),
        Layout(name="spectro", ratio=1),
    )

    layout["spectro"].update(
        Panel(Align.center(spectro_text), title="Waveform", border_style="cyan")
    )
    layout["lyrics"].update(
        Panel("\n".join(lyrics), title="Lyrics", border_style="magenta")
    )
    layout["ascii-disc"].update(
        Panel(Align.center(disc_frame), title="", border_style="green")
    )

    # controls
    layout["controls"].update(
        Panel(Align.center("[bold yellow]Controls: [P] Play/Pause  [R] Reset  [Q] Quit"))
    )
    # footer
    layout["footer"].update(
        Panel(Align.center("[yellow]Built with ❤️  by SUNSET-Sejong University")))
    
    return layout


def init_input():
    if not ON_WINDOWS:
        import termios, tty, sys
        import fcntl
    
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setcbreak(fd)

        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        return (fd, old_settings, fl)
    return None


def cleanup_input(stdscr):
    if not ON_WINDOWS and stdscr:
        import termios, fcntl
        fd, old_settings, fl = stdscr
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl)


def get_key(stdscr=None):
    if ON_WINDOWS:
        if msvcrt.kbhit():
            try:
                return msvcrt.getch().decode("utf-8").lower()
            except UnicodeDecodeError:
                return None
    else:
        try:
            ch = sys.stdin.read(1)
            if ch:
                return ch.lower()
        except (IOError, OSError):
            pass
    return None


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


def remove_vocals(input_file, output_dir="downloads"):
    os.makedirs(output_dir, exist_ok=True)
    song_basename = os.path.splitext(os.path.basename(input_file)[0])
    output_name = f"{song_basename}_instrumental.wav"

    #Run Spleeter via Docker (2 stems: vocal + accompaniment)
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{os.path.abspath(input_file)}:/input/song.mp3",
        "-v", f"{os.path.abspath(output_dir)}:/output",
        "researchdeezer/spleeter",
        "separate", "-i", "/input/song.mp3",
        "-p", "spleeter:2stems",
        "-o", "/output"
    ]
    print("🎶 Running Spleeter vocal remover...")
    subprocess.run(cmd, check=True)

    # Spleeter creates /output/song/accompaniment.wav
    original_instrumental = os.path.join(output_dir, "song", "accompaniment.wav")
    if os.path.exists(original_instrumental):
        return original_instrumental
    else:
        raise FileNotFoundError("Spleeter did not produce the accompaniment file.")


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
        print(f"🔎 Searching karaoke version: {query}")
        info = ydl.extract_info(f"ytsearch1:{query} karaoke", download=True)
        entry = info['entries'][0]
        title = entry.get('title', '').lower()
        filename = ydl.prepare_filename(entry)
        mp3_file = os.path.splitext(filename)[0] + ".mp3"

        if "karaoke" in title:
            print("✅ Karaoke version found")
            return mp3_file
        else:
            print("⚠️ Karaoke version not found, downloading original to remove vocals...")
            # Run Spleeter vocal remover
            instrumental = remove_vocals(mp3_file, output_dir=output_dir)
            print("✅ Instrumental created:", instrumental)
        return instrumental
    

def play_song(song_file, lyrics):
    # init mixer
    mixer.init()
    mixer.music.load(song_file)

    # also load wav for analysis
    wav_file = "temp.wav"
    os.system(f'ffmpeg -y -i "{song_file}" -ac 1 -ar 16000 "{wav_file}" >nul 2>&1')

    rate, audio = read(wav_file)
    audio = audio / np.max(np.abs(audio))  # normalize
    step = rate // 10  # ~0.1s per step

    # load disc frames
    with open("ascii_arts.json", "r") as f:
        art_data = json.load(f)
    disc_frames = list(art_data["disk_frames"].values())

    pos = 0
    frame_idx = 0  # index for disc frames
    paused = False
    stopped = False

    stdscr = init_input() 

    try:
        with Live(console=console, refresh_per_second=10) as live:
            #draw initial layout first
            initial_spec = spectrogram(audio[:step], width=40, height=None)
            initial_frame = "\n".join(disc_frames[0])
            initial_layout = build_layout(
                os.path.basename(song_file),
                get_current_lyrics(lyrics, 0),
                initial_spec,
                initial_frame
            )
            live.update(initial_layout)  

            #start playback after UI is ready
            mixer.music.play()

            while not stopped and (mixer.music.get_busy() or paused):
                key = get_key(stdscr)  # get input (msvcrt or curses)
                # === key controls ===
                if key == "p":              # play/pause toggle
                    if paused:
                        mixer.music.unpause()
                        paused = False
                    else:
                        mixer.music.pause()
                        paused = True
                elif key == "r":            # rewind to start
                    mixer.music.stop()
                    mixer.music.play()
                    pos = 0
                    frame_idx = 0
                    paused = False
                elif key == "q":            # quit player
                    mixer.music.stop()
                    stopped = True
                    break

                if paused:
                    time.sleep(0.1)
                    continue
                
                #Update audio chunk and UI
                chunk = audio[pos:pos+step]
                spec = spectrogram(chunk, width=40, height=None)
                    
                curr_ms = mixer.music.get_pos()
                curr_sec = curr_ms / 1000.0
                lyric_window = get_current_lyrics(lyrics, curr_sec)
                
                frame = disc_frames[frame_idx % len(disc_frames)]
                frame_text = "\n".join(frame)   # turn list of strings into proper ASCII art
                frame_idx += 1
                layout = build_layout(
                    os.path.basename(song_file), 
                    lyric_window, 
                    spec,
                    frame_text
                )
                live.update(layout)
                
                pos += step
                time.sleep(0.1)
    finally:
        cleanup_input(stdscr)  # restore terminal on unix

        # delete everything under downloads
        downloads_dir = "downloads"
        temp_file = "temp.wav"
        if (os.path.exists(downloads_dir)):
            try:
                shutil.rmtree(downloads_dir)
                os.remove(temp_file)
                print(f"🗑️ Deleted {downloads_dir} folder")
            except Exception as e:
                print(f"⚠️ Could not delete {downloads_dir}: {e}")


def parse_lrc(lrc_text):
    """Convert raw LRC text into [(timestamp, line)] pairs."""
    lines = []
    for line in lrc_text.splitlines():
        if line.startswith("["):
            try:
                timestamp, text = line.split("]", 1)
                timestamp = timestamp[1:]
                m, s = timestamp.split(":")
                secs = int(m) * 60 + float(s)
                lines.append((secs, text.strip()))
            except:
                continue
    return sorted(lines, key=lambda x: x[0])


def get_current_lyrics(lyrics, current_sec, window=2):
    """Return a few lines around the current lyric."""
    if not lyrics:
        return ["(No synced lyrics available)"]

    current_index = 0
    for i, (ts, _)in enumerate(lyrics):
        if ts <= current_sec:
            current_index = i
        else:
            break
    start = max(0, current_index - window)
    end = min(len(lyrics), current_index + window + 1)

    display_lines = []
    for i in range(start, end):
        ts, line = lyrics[i]
        if i == current_index:
            display_lines.append(f"[bold yellow]> {line} <[/bold yellow]")
        else:
            display_lines.append(line)
    
    return display_lines

if __name__ == "__main__":
    song_name = input("Enter the song name: ")
    results = search_song(song_name)
    if results:
        title, artists = results[0] if results else ("No match found", "", "")
        query = f"{title} by {artists}"
        song_file = download_audio(query)      
        print(f"✅ Downloaded: {song_file}")
        
        #fetch synced lyrics
        try:
            lrc_text = search(f"{title} {artists}", synced_only=True)
            lyrics = parse_lrc(lrc_text) if lrc_text else []
        except Exception as e:
            print(f"⚠️  Could not fetch synced lyrics: {e}")
            lyrics = []
  
        play_song(song_file, lyrics)

    else:
        print("❌ No matching song found!")

