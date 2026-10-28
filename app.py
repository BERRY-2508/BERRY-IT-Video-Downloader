"""BERRY IT Video Downloader — local desktop application."""
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from urllib.parse import urlparse

import yt_dlp

BG = "#171717"
PANEL = "#222222"
TEXT = "#F4F4F4"
MUTED = "#AAAAAA"
RED = "#FF3C3C"


def valid_youtube_url(value):
    try:
        parsed = urlparse(value.strip())
        return (parsed.scheme in ("http", "https")
                and (parsed.hostname or "").lower() in {
                    "youtube.com", "www.youtube.com", "m.youtube.com",
                    "music.youtube.com", "youtu.be"
                } and bool(parsed.path.strip("/")))
    except ValueError:
        return False


def ffmpeg_location():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


class DownloadWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BERRY IT | Video Downloader")
        self.geometry("740x550")
        self.minsize(630, 520)
        self.configure(bg=BG)
        self.events = queue.Queue()
        self.running = False
        self.url = tk.StringVar()
        self.output = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.kind = tk.StringVar(value="MP4 video")
        self.quality = tk.StringVar(value="1080p")
        self.status = tk.StringVar(value="Ready to download")
        self.details = tk.StringVar(value="Downloads are saved on this computer.")
        self.percent = tk.DoubleVar(value=0)
        self.build_ui()
        self.after(100, self.drain_events)

    def label(self, parent, text, fg=MUTED, size=11, bold=False, **kwargs):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=fg,
                        font=("Segoe UI", size, "bold" if bold else "normal"), **kwargs)

    def build_ui(self):
        shell = tk.Frame(self, bg=BG, padx=38, pady=28)
        shell.pack(fill="both", expand=True)

        self.label(shell, "BERRY IT", fg=RED, size=24, bold=True).pack(anchor="w")
        self.label(shell, "VIDEO DOWNLOADER", fg=TEXT, size=12, bold=True).pack(
            anchor="w", pady=(0, 24))
        self.label(shell, "VIDEO URL", size=10, bold=True).pack(anchor="w")
        tk.Entry(shell, textvariable=self.url, bg=PANEL, fg=TEXT,
                 insertbackground=TEXT, highlightbackground="#484848",
                 highlightcolor=RED, highlightthickness=1, relief="flat",
                 font=("Segoe UI", 11)).pack(fill="x", ipady=11, pady=(7, 17))

        options = tk.Frame(shell, bg=BG)
        options.pack(fill="x")
        left = tk.Frame(options, bg=BG)
        right = tk.Frame(options, bg=BG)
        left.pack(side="left", fill="x", expand=True, padx=(0, 10))
        right.pack(side="left", fill="x", expand=True)
        self.label(left, "FORMAT", size=10, bold=True).pack(anchor="w")
        self.label(right, "VIDEO QUALITY", size=10, bold=True).pack(anchor="w")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Berry.TCombobox", foreground=TEXT, fieldbackground=PANEL,
                        background=PANEL, arrowcolor=TEXT, bordercolor="#484848", padding=7)
        style.map("Berry.TCombobox", fieldbackground=[("readonly", PANEL)],
                  foreground=[("readonly", TEXT)])
        self.format_combo = ttk.Combobox(
            left, state="readonly", textvariable=self.kind,
            values=["MP4 video", "MP3 audio"], style="Berry.TCombobox")
        self.format_combo.pack(fill="x", pady=(7, 17))
        self.format_combo.bind("<<ComboboxSelected>>", self.sync_quality)
        self.quality_combo = ttk.Combobox(
            right, state="readonly", textvariable=self.quality,
            values=["Best available", "1080p", "720p", "480p"],
            style="Berry.TCombobox")
        self.quality_combo.pack(fill="x", pady=(7, 17))

        self.label(shell, "SAVE TO", size=10, bold=True).pack(anchor="w")
        folder_line = tk.Frame(shell, bg=BG)
        folder_line.pack(fill="x", pady=(7, 20))
        tk.Entry(folder_line, textvariable=self.output, bg=PANEL, fg=TEXT,
                 insertbackground=TEXT, relief="flat", highlightbackground="#484848",
                 highlightthickness=1, font=("Segoe UI", 10)).pack(
                     side="left", fill="x", expand=True, ipady=10)
        tk.Button(folder_line, text="Browse", command=self.browse, bg="#3A3A3A",
                  fg=TEXT, activebackground="#4A4A4A", activeforeground=TEXT,
                  relief="flat", font=("Segoe UI", 10), cursor="hand2",
                  padx=14, pady=9).pack(side="left", padx=(8, 0))

        self.download_button = tk.Button(
            shell, text="DOWNLOAD", command=self.start_download, bg="#D00000",
            fg="white", activebackground=RED, activeforeground="white",
            relief="flat", cursor="hand2", font=("Segoe UI", 12, "bold"), pady=12)
        self.download_button.pack(fill="x")
        style.configure("Berry.Horizontal.TProgressbar", troughcolor="#353535",
                        background=RED, bordercolor=BG, lightcolor=RED, darkcolor=RED)
        ttk.Progressbar(shell, maximum=100, variable=self.percent,
                        style="Berry.Horizontal.TProgressbar").pack(
                            fill="x", pady=(22, 10))
        self.label(shell, "", fg=TEXT, size=11,
                   textvariable=self.status).pack(anchor="w")
        self.label(shell, "", size=9, textvariable=self.details,
                   wraplength=620, justify="left").pack(anchor="w", pady=(5, 12))
        self.label(shell, "Save only media you own or are authorized to download.",
                   size=9).pack(side="bottom", anchor="w")

    def sync_quality(self, _event=None):
        self.quality_combo.configure(
            state="disabled" if self.kind.get() == "MP3 audio" else "readonly")

    def browse(self):
        folder = filedialog.askdirectory(initialdir=self.output.get())
        if folder:
            self.output.set(folder)

    def start_download(self):
        url = self.url.get().strip()
        folder = Path(self.output.get()).expanduser()
        if not valid_youtube_url(url):
            messagebox.showerror("Invalid link", "Enter a valid YouTube video URL.")
            return
        if not folder.is_dir():
            messagebox.showerror("Invalid folder", "Choose an existing download folder.")
            return
        if self.running:
            return
        self.running = True
        self.percent.set(0)
        self.status.set("Connecting…")
        self.details.set("Preparing download…")
        self.download_button.configure(state="disabled", text="DOWNLOADING…")
        threading.Thread(target=self.download_worker,
                         args=(url, folder, self.kind.get(), self.quality.get()),
                         daemon=True).start()

    def download_worker(self, url, folder, kind, quality):
        def progress(data):
            if data.get("status") == "finished":
                self.events.put(("status", "Processing downloaded media…"))
                return
            if data.get("status") != "downloading":
                return
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            current = data.get("downloaded_bytes", 0)
            if total:
                self.events.put(("progress", min(current / total * 100, 100)))
            speed = data.get("speed")
            eta = data.get("eta")
            note = f"{speed / 1048576:.1f} MB/s" if speed else "Downloading"
            if eta is not None:
                note += f" • {int(eta)}s remaining"
            self.events.put(("details", note))

        class Logger:
            def debug(self, msg):
                pass
            def info(self, msg):
                pass
            def warning(self, msg):
                self_log("Warning: " + msg)
            def error(self, msg):
                self_log(msg)

        def self_log(msg):
            self.events.put(("details", msg[:240]))

        opts = {
            "outtmpl": str(folder / "%(title).180B [%(id)s].%(ext)s"),
            "noplaylist": True,
            "windowsfilenames": True,
            "quiet": True,
            "logger": Logger(),
            "progress_hooks": [progress],
            "postprocessor_hooks": [
                lambda d: self.events.put(("status", "Converting media…"))
                if d.get("status") == "started" else None
            ],
        }
        ffmpeg = ffmpeg_location()
        if ffmpeg:
            opts["ffmpeg_location"] = ffmpeg
        if kind == "MP3 audio":
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3",
                 "preferredquality": "192"}
            ]
        else:
            height = {"Best available": "", "1080p": "[height<=1080]",
                      "720p": "[height<=720]", "480p": "[height<=480]"}[quality]
            opts["format"] = (
                f"bestvideo{height}[ext=mp4]+bestaudio[ext=m4a]/"
                f"best{height}[ext=mp4]/bestvideo{height}+bestaudio/best"
            )
            opts["merge_output_format"] = "mp4"
            opts["postprocessors"] = [
                {"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}
            ]
        try:
            with yt_dlp.YoutubeDL(opts) as downloader:
                code = downloader.download([url])
            if code != 0:
                raise RuntimeError("Download did not complete successfully.")
            self.events.put(("done", str(folder)))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    def drain_events(self):
        try:
            while True:
                action, data = self.events.get_nowait()
                if action == "progress":
                    self.percent.set(data)
                    self.status.set(f"Downloading… {data:.0f}%")
                elif action == "status":
                    self.status.set(data)
                elif action == "details":
                    self.details.set(data)
                elif action == "done":
                    self.percent.set(100)
                    self.status.set("Download complete")
                    self.details.set("Saved in " + data)
                    self.reset()
                elif action == "error":
                    self.status.set("Download failed")
                    self.details.set(data)
                    self.reset()
                    messagebox.showerror("Download failed", data)
        except queue.Empty:
            pass
        self.after(100, self.drain_events)

    def reset(self):
        self.running = False
        self.download_button.configure(state="normal", text="DOWNLOAD")


if __name__ == "__main__":
    DownloadWindow().mainloop()
