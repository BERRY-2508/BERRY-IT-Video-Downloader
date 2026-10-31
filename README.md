# BERRY IT Video Downloader

The Windows and Linux desktop interface uses BERRY IT's charcoal/red styling and embeds the original full logo from the `BERRY.IT.WEB` GitHub repository for offline display. The app uses Orbitron and Inter when those fonts are installed, with system-font fallbacks otherwise.

Local desktop application for Windows and Linux for saving video/audio you own or have permission to download, powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp) and FFmpeg.

## Video and playlist downloads

Paste a YouTube video URL or a playlist URL, then choose **Download mode**:
- **Single video:** download just the video in the link, even when it has a playlist context.
- **Entire playlist:** download all entries from a YouTube URL containing a `list=` identifier.

Both modes support MP4 and MP3. Playlist files are placed inside a folder named after the playlist, numbered in playlist order. An archive file in the selected download directory tracks successful downloads so future attempts can skip those entries. MP4 and MP3 each have their own archive. Note that the progress display is an approximation based on the current playlist item; unavailable entries and skipped downloads can make it jump.

The application is intended for material you own or are permitted to download. Large playlists can require substantial disk space and time.

## Public direct downloads

The website's Windows and Linux buttons point to the **latest GitHub Release assets**, not GitHub Actions artifacts. They work without a GitHub login once a release has been published.

To publish the first release, open **Actions → Publish Windows and Linux downloads → Run workflow** on `main`, keep version `v0.2.0`, and run it. The workflow builds both binaries and publishes them in one release. Future versions should use a newer version value such as `v0.2.1`.

- Windows: `BERRY-IT-Video-Downloader-Windows-x64.exe`
- Linux: `BERRY-IT-Video-Downloader-Linux-x86_64.tar.gz`

These builds have not yet been verified end-to-end. The stable website download links return an error until that first release succeeds.

## Download Windows build

Go to **Actions → Build Windows app → Run workflow**. Once the build succeeds, download the executable from the **Artifacts** section of the run. This is an early prototype and has not yet been tested end-to-end on Windows or against live YouTube downloads.

For best YouTube compatibility, install [Deno](https://deno.com/) and make sure `deno` is on PATH. The GitHub-produced executable is not code-signed, so Windows SmartScreen may warn when launching it.

## Linux (x86_64)

Go to **Actions → Build Linux app → Run workflow** on the `main` branch. After the run succeeds, download the `Berry-IT-Video-Downloader-Linux-x86_64` artifact, unzip the Actions artifact, and extract the included `.tar.gz`:

```bash
tar -xzf Berry-IT-Video-Downloader-Linux-x86_64.tar.gz
chmod +x Berry-IT-Video-Downloader
./Berry-IT-Video-Downloader
```

This build targets **64-bit Intel/AMD Linux (x86_64)**. It does not run on ARM Raspberry Pi systems. It requires a graphical desktop and compatible system libraries. Install Deno separately for improved YouTube compatibility. The packaged application has not yet been tested on a user's Linux desktop.

## Run from source

Install Python 3.11+ (3.12 recommended):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

On Linux also install tkinter (`sudo apt install python3-tk`). FFmpeg is provided via `imageio-ffmpeg`; for FFprobe-related errors install a full FFmpeg distribution.

## GitHub release

Push a tag like `v0.1.0` to trigger the Windows build and GitHub Release workflow. Do this after testing the downloaded artifact.

## Disclaimer

Only download content you are authorized to save. Follow applicable platform terms and copyright rules. This project is not affiliated with YouTube.

Dependencies: yt-dlp and FFmpeg; review their licenses when redistributing compiled binaries.
