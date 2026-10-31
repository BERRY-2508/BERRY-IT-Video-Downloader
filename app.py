"""BERRY IT Video Downloader — local desktop application."""
import queue
import base64
import io
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from urllib.parse import urlparse, parse_qs

import yt_dlp
from PIL import Image, ImageTk
from brand_logo import LOGO_WEBP_BASE64

BG = "#0b0b0e"
PANEL = "#202025"
SURFACE = "#141417"
TEXT = "#F4F4F4"
MUTED = "#acaab2"
RED = "#ff3c3c"
LINE = "#393039"
HEADING_FONT = "Orbitron"
BODY_FONT = "Inter"


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
        # Size the window to the actual usable desktop, allowing space for the
        # Windows title bar/taskbar and higher display scaling.
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = min(850, max(450, screen_width - 80))
        height = min(760, max(400, screen_height - 120))
        self.minsize(min(675, width), min(600, height))
        self.geometry(f"{width}x{height}+{max(0, (screen_width-width)//2)}+{max(0, (screen_height-height)//2)}")
        self.configure(bg=BG)
        self.events = queue.Queue()
        self.running = False
        self.url = tk.StringVar()
        self.output = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.kind = tk.StringVar(value="MP4 video")
        self.quality = tk.StringVar(value="1080p")
        self.scope = tk.StringVar(value="Single video")
        self.status = tk.StringVar(value="Ready to download")
        self.details = tk.StringVar(value="Downloads are saved on this computer.")
        self.percent = tk.DoubleVar(value=0)
        self.build_ui()
        self.after(100, self.drain_events)

    def label(self, parent, text, fg=MUTED, size=11, bold=False, family=BODY_FONT, **kwargs):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=fg,
                        font=(family, size, "bold" if bold else "normal"), **kwargs)

    def section_label(self, parent, text):
        self.label(parent, text.upper(), fg="#dedbe0", size=9,
                   bold=True, family=HEADING_FONT).pack(anchor="w", pady=(0, 7))

    def build_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Berry.TCombobox", foreground=TEXT, fieldbackground=PANEL,
                        background=PANEL, arrowcolor=TEXT, bordercolor="#48464e",
                        padding=10)
        style.map("Berry.TCombobox", fieldbackground=[("readonly", PANEL)],
                  foreground=[("readonly", TEXT)])
        style.configure("Berry.Horizontal.TProgressbar", troughcolor="#35333a",
                        background=RED, bordercolor=BG, lightcolor=RED,
                        darkcolor=RED, thickness=7)

        outer = tk.Frame(self, bg=BG, padx=20, pady=18)
        outer.pack(fill="both", expand=True)
        shell = tk.Frame(outer, bg=SURFACE, padx=27, pady=20,
                         highlightbackground=LINE, highlightthickness=1)
        shell.pack(fill="both", expand=True)

        # Embed the original website logo; do not depend on a network request.
        raw_logo = base64.b64decode(LOGO_WEBP_BASE64)
        image = Image.open(io.BytesIO(raw_logo)).convert("RGBA")
        image.thumbnail((640, 158), Image.Resampling.LANCZOS)
        self.brand_image = ImageTk.PhotoImage(image)
        tk.Label(shell, image=self.brand_image, bg=SURFACE).pack(pady=(0, 4))
        self.label(shell, "VIDEO DOWNLOADER", fg=RED, size=18, bold=True,
                   family=HEADING_FONT).pack(pady=(0, 4))
        self.label(shell, "Download your media directly to your computer.",
                   size=10).pack(pady=(0, 17))

        form = tk.Frame(shell, bg=SURFACE)
        form.pack(fill="x")
        self.section_label(form, "Video or playlist URL")
        tk.Entry(form, textvariable=self.url, bg=PANEL, fg=TEXT,
                 insertbackground=TEXT, highlightbackground="#48464e",
                 highlightcolor=RED, highlightthickness=1, relief="flat",
                 font=(BODY_FONT, 11)).pack(fill="x", ipady=11, pady=(0, 17))

        self.section_label(form, "Download mode")
        modes = tk.Frame(form, bg=SURFACE)
        modes.pack(fill="x", pady=(0, 18))
        for mode in ("Single video", "Entire playlist"):
            tk.Radiobutton(
                modes, text=mode.title(), variable=self.scope, value=mode,
                bg=SURFACE, fg=TEXT, activebackground=SURFACE,
                activeforeground=RED, selectcolor=PANEL,
                font=(BODY_FONT, 11), indicatoron=True
            ).pack(side="left", padx=(0, 24))

        options = tk.Frame(form, bg=SURFACE)
        options.pack(fill="x")
        left = tk.Frame(options, bg=SURFACE)
        right = tk.Frame(options, bg=SURFACE)
        left.pack(side="left", fill="x", expand=True, padx=(0, 12))
        right.pack(side="left", fill="x", expand=True)
        self.section_label(left, "Format")
        self.section_label(right, "Quality")
        self.format_combo = ttk.Combobox(
            left, state="readonly", textvariable=self.kind,
            values=["MP4 video", "MP3 audio"], style="Berry.TCombobox")
        self.format_combo.pack(fill="x", pady=(0, 18))
        self.format_combo.bind("<<ComboboxSelected>>", self.sync_quality)
        self.quality_combo = ttk.Combobox(
            right, state="readonly", textvariable=self.quality,
            values=["Best available", "1080p", "720p", "480p"],
            style="Berry.TCombobox")
        self.quality_combo.pack(fill="x", pady=(0, 18))

        self.section_label(form, "Save location")
        folder_line = tk.Frame(form, bg=SURFACE)
        folder_line.pack(fill="x", pady=(0, 18))
        tk.Entry(folder_line, textvariable=self.output, bg=PANEL, fg=TEXT,
                 insertbackground=TEXT, relief="flat", highlightbackground="#48464e",
                 highlightthickness=1, font=(BODY_FONT, 10)).pack(
                     side="left", fill="x", expand=True, ipady=10)
        tk.Button(folder_line, text="Browse", command=self.browse, bg="#303037",
                  fg=TEXT, activebackground="#44434b", activeforeground=TEXT,
                  relief="flat", font=(BODY_FONT, 10), cursor="hand2",
                  padx=15, pady=10).pack(side="left", padx=(8, 0))
        self.download_button = tk.Button(
            form, text="↓   DOWNLOAD VIDEO", command=self.start_download,
            bg="#d00023", fg="white", activebackground=RED,
            activeforeground="white", relief="flat", cursor="hand2",
            font=(HEADING_FONT, 12, "bold"), pady=15)
        self.download_button.pack(fill="x")

        status_line = tk.Frame(form, bg=SURFACE)
        status_line.pack(fill="x", pady=(15, 4))
        self.label(status_line, "", fg=TEXT, size=10,
                   textvariable=self.status).pack(side="left")
        self.progress_label = tk.StringVar(value="0%")
        self.label(status_line, "", fg=MUTED, size=10,
                   textvariable=self.progress_label).pack(side="right")
        ttk.Progressbar(form, maximum=100, variable=self.percent,
                        style="Berry.Horizontal.TProgressbar").pack(fill="x", pady=(0, 9))
        self.label(form, "", fg=MUTED, size=9, textvariable=self.details,
                   wraplength=690, justify="left").pack(anchor="w")
        tk.Frame(shell, bg=LINE, height=1).pack(fill="x", pady=(18, 10))
        self.label(shell, "BERRY IT  |  THE RIPE CHOICE FOR YOUR IT SOLUTIONS",
                   size=8, fg="#93909b").pack(anchor="w")

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
        playlist_mode = self.scope.get() == "Entire playlist"
        parsed = urlparse(url)
        has_list = bool(parse_qs(parsed.query).get("list"))
        if playlist_mode and not has_list:
            messagebox.showerror("Playlist URL required",
                                 "This mode requires a YouTube URL containing list=.")
            return
        if not playlist_mode and parsed.path.rstrip("/") == "/playlist":
            messagebox.showerror("Video URL required",
                                 "Select Entire playlist for playlist-only URLs.")
            return
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
        self.progress_label.set("0%")
        self.status.set("Connecting…")
        self.details.set("Preparing download…")
        self.download_button.configure(state="disabled", text="DOWNLOADING…")
        threading.Thread(target=self.download_worker,
                         args=(url, folder, self.kind.get(), self.quality.get(), playlist_mode),
                         daemon=True).start()

    def download_worker(self, url, folder, kind, quality, playlist_mode):
        current_item = {"index": 1, "total": 1}

        def item_counts(info):
            try:
                index = max(1, int(info.get("playlist_index") or current_item["index"]))
            except (TypeError, ValueError):
                index = current_item["index"]
            try:
                total = max(index, int(info.get("n_entries") or info.get("playlist_count")
                                       or current_item["total"]))
            except (TypeError, ValueError):
                total = max(index, current_item["total"])
            current_item.update(index=index, total=total)
            return index, total

        def progress(data):
            index, count = item_counts(data.get("info_dict") or {})
            prefix = f"Video {index} of {count}" if playlist_mode else "Video"
            if data.get("status") == "finished":
                self.events.put(("status", prefix + " — processing…"))
                return
            if data.get("status") != "downloading":
                return
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            current = data.get("downloaded_bytes", 0)
            if total:
                fraction = min(current / total, 1)
                progress_total = ((index - 1 + fraction) / count * 100
                                  if playlist_mode else fraction * 100)
                self.events.put(("progress", min(progress_total, 99.9)))
            self.events.put(("status", prefix + " — downloading…"))
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
            "outtmpl": (
                str(folder / "%(playlist_title|Playlist)s" /
                    "%(playlist_index)03d - %(title).180B [%(id)s].%(ext)s")
                if playlist_mode else
                str(folder / "%(title).180B [%(id)s].%(ext)s")
            ),
            "noplaylist": not playlist_mode,
            "download_archive": str(folder / (".berry-it-mp3-archive.txt" if kind == "MP3 audio" else ".berry-it-mp4-archive.txt")),
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
                    self.progress_label.set(f"{data:.0f}%")
                elif action == "status":
                    self.status.set(data)
                elif action == "details":
                    self.details.set(data)
                elif action == "done":
                    self.percent.set(100)
                    self.progress_label.set("100%")
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
