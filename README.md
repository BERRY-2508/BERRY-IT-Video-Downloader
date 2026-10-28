# BERRY IT Video Downloader

Windows-first local desktop application for saving video/audio you own or have permission to download, powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp) and FFmpeg.

## Download Windows build

Go to **Actions → Build Windows app → Run workflow**. Once the build succeeds, download the executable from the **Artifacts** section of the run. This is an early prototype and has not yet been tested end-to-end on Windows or against live YouTube downloads.

For best YouTube compatibility, install [Deno](https://deno.com/) and make sure `deno` is on PATH. The GitHub-produced executable is not code-signed, so Windows SmartScreen may warn when launching it.

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
