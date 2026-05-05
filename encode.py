#!/usr/bin/env python3
"""
encode.py – Advanced encode comparison & upload tool.

Usage (flag mode):
    python encode.py -s source.mkv -c comparison.mkv -e encoded.mkv

Usage (interactive mode – no flags):
    python encode.py
    → shows hierarchical file listing; enter: source_key,encoded_key,comparison_key
      e.g. "1,2A,3AA"

Roles
------
-s / source     : used for full description (filename, mediainfo, video/audio info)
-c / comparison : 5 frames at 20/40/50/60/80% → served locally via web server
-e / encoded    : 5 frames at same positions   → uploaded to image host + shown in description

Torrent is created for the SOURCE file.
Generated files are deleted on exit (pre-existing files are never touched).
"""

from __future__ import annotations

import argparse
import atexit
import concurrent.futures
import json
import os
import re
import shutil
import string
import subprocess
import sys
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from math import gcd
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

import requests


# ========================= CONFIGURATION =========================

# --- API Keys ---
IMGBB_API_KEY     = "c68b06c4f7daabb90d696eafa1f25a5c"   # https://api.imgbb.com/
FREEIMAGE_API_KEY = "6d207e02198a847aa98d0a2a901485a5"

# --- Image host ---
IMAGE_HOST = "imgbb"   # "imgbb" or "freeimage"

# --- Screenshot settings ---
LOSSLESS_SCREENSHOT = True                             # PNG when True, JPEG when False
FRAME_PERCENTS      = [0.20, 0.40, 0.50, 0.60, 0.80]  # 5 frames at these %s

# --- Torrent settings ---
CREATE_TORRENT_FILE = True
TRACKER_ANNOUNCE    = "https://tracker.torrentbd.net/announce"
PRIVATE_TORRENT     = True

# --- Torrent comment settings (new) ---
ADD_TORRENT_COMMENT = False   # Set True to embed a comment in the torrent
TORRENT_COMMENT     = ""      # The comment text (used when ADD_TORRENT_COMMENT is True)

# --- Output ---
SKIP_TXT          = True    # Do not save description to a .txt file
COPY_TO_CLIPBOARD = True    # Copy description to system clipboard

# --- Upload concurrency ---
MAX_CONCURRENT_UPLOADS = 16
MIN_IO_WORKERS         = 4
IO_WORKER_MULTIPLIER   = 2
UPLOAD_TIMEOUT         = 90  # seconds per upload

# --- Auto-delete: delete only files *this script* created ---
AUTO_DELETE_CREATED_FILES = True

# --- Web server ---
START_HTTP_SERVER = True
HTTP_PORT         = 40453   # different port from main.py

# =================================================================

VIDEO_EXTS = {
    ".mkv", ".mp4", ".avi", ".mov", ".m4v", ".webm",
    ".flv", ".wmv", ".mpg", ".mpeg", ".ts", ".m2ts",
}

_FILENAME_SERVICES = [
    "AMZN", "NF", "VIKI", "AHA", "SNXT", "KCW", "DSNP", "ATV", "JHS", "WTV",
    "HULU", "ATVP", "HMAX", "PCOK", "PMTP", "STAN", "CRAV", "MUBI", "CC",
    "CR", "FUNI", "HTSR", "HS", "iP", "ALL4", "iT", "BBC", "NOW",
]


# ========================= CONSOLE COLOURS =========================

class c:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    PURPLE = "\033[95m"
    CYAN   = "\033[96m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    GRAY   = "\033[90m"
    WHITE  = "\033[97m"


# ========================= GLOBAL STATE =========================

# Track every file this script creates so we can delete them on exit
_GENERATED_FILES:   list[Path] = []
_GENERATED_TORRENT: Path | None = None
_COMPARISON_SS:     list[Path] = []   # local comparison screenshots
_ENCODED_SS:        list[Path] = []   # encoded screenshots (also uploaded)

# Shared web-server state (set after processing)
_WEBAPP_HTML:             str        = ""
_UPLOADED_ENCODED_URLS:   list[str]  = []
_COMPARISON_SS_PATHS:     list[Path] = []

_SERVER_READY      = threading.Event()
_HTTP_STARTED      = False
_HTTP_STARTED_LOCK = threading.Lock()

_log_lock = threading.Lock()


# ========================= LOGGING =========================

def log(msg: str, icon: str = "•", color: str = c.CYAN) -> None:
    t = datetime.now().strftime("%H:%M:%S")
    with _log_lock:
        print(f"{color}[{t}] {icon} {msg}{c.RESET}", flush=True)


def success(msg: str) -> None:
    log(msg, "✓", c.GREEN)


def error(msg: str) -> None:
    log(msg, "✗", c.RED)


def banner() -> None:
    os.system("cls" if os.name == "nt" else "clear")
    print(
        f"{c.PURPLE}{c.BOLD}"
        "╔══════════════════════════════════════════════════════════════════╗\n"
        "║          Encode Comparison & Upload Tool  (encode.py)           ║\n"
        "║    By fahimbyte (https://github.com/mazidulmahim)               ║\n"
        "╚══════════════════════════════════════════════════════════════════╝"
        f"{c.RESET}"
    )


def copy_to_clipboard(text: str) -> None:
    if not COPY_TO_CLIPBOARD:
        return
    try:
        if os.name == "nt":
            subprocess.run("clip", input=text.encode("utf-8"), check=True, capture_output=True)
        elif sys.platform == "darwin":
            subprocess.run("pbcopy", input=text.encode("utf-8"), check=True, capture_output=True)
        else:
            subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=text.encode("utf-8"), check=True, capture_output=True,
            )
        success("Description copied to clipboard!")
    except Exception:
        pass


def hide_window():
    if os.name == "nt":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        return si
    return None


# ========================= OWN STRIP / TITLE LOGIC =========================
# (No import from title.py – all logic is self-contained.)

_TECH_TAGS_PAT = (
    r"2160p|1080p|720p|480p"
    r"|WEB-DL|WEBRip|BluRay|REMUX|HDTV"
    + "|" + "|".join(re.escape(s) for s in _FILENAME_SERVICES)
    + r"|x264|x265|H\.264|H\.265|HEVC|AVC|AV1|VP9"
    r"|DD\+\d|DDP\d|DD\d|DDP|TrueHD|DTS|AAC|FLAC|Opus"
    r"|HDR10\+|HDR10|HDR|HLG|DV"
    r"|REPACK|PROPER|INTERNAL|UHD"
)
_FIRST_TECH_TAG_RE = re.compile(
    rf"(?:^|[.\-_\s])({_TECH_TAGS_PAT})(?:[.\-_\s]|$)", re.I
)


def _strip_leading_site(name: str) -> str:
    return re.sub(
        r"^\s*(?:https?://)?www\.(?:[A-Za-z0-9-]+\.)+[A-Za-z]{{2,}}\s*[-–—:|]\s*",
        "",
        name, count=1, flags=re.I,
    )


def strip_p2p_name(filename: str) -> str:
    """
    Strip the show/movie name from a P2P release filename, keeping only
    the technical part (resolution, source, codec, audio, group).

    Examples
    --------
    "Show.Name.S01E01.1080p.AMZN.WEB-DL.DDP5.1.H.264-Group.mkv"
        → "1080p.AMZN.WEB-DL.DDP5.1.H.264-Group"
    "1080p.AMZN.WEB-DL.DDP5.1.H.264-Group.mkv"
        → "1080p.AMZN.WEB-DL.DDP5.1.H.264-Group"  (unchanged)
    """
    stem = Path(filename).stem
    stem = re.sub(
        r"^\s*(?:https?://)?www\.(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}\s*[-–—:|]\s*",
        "",
        stem, count=1, flags=re.I,
    )
    m = _FIRST_TECH_TAG_RE.search(stem)
    if not m:
        return stem
    start = m.start(1)
    return stem[start:].strip(".-_ ")


# ========================= MEDIAINFO =========================

def get_mediainfo_text(path: Path) -> str:
    """Return plain-text mediainfo output."""
    cmd = ["mediainfo", str(path)]
    if not shutil.which("mediainfo"):
        exe = Path(__file__).parent / "MediaInfo.exe"
        if exe.exists():
            cmd = [str(exe), str(path)]
        else:
            return "MediaInfo not available"
    try:
        result = subprocess.run(
            cmd, capture_output=True, startupinfo=hide_window(), timeout=300,
        )
        if result.returncode == 0:
            return result.stdout.decode("utf-8", errors="replace")
        return ""
    except Exception as exc:
        error(f"MediaInfo error: {exc}")
        return ""


def get_mediainfo_json(path: Path) -> dict:
    """Return parsed JSON from `mediainfo --Output=JSON`."""
    try:
        r = subprocess.run(
            ["mediainfo", "--Output=JSON", str(path)],
            capture_output=True, text=True, timeout=120,
        )
        if r.stdout:
            return json.loads(r.stdout)
    except Exception as exc:
        error(f"MediaInfo JSON error: {exc}")
    return {}


def trim_mediainfo_path(text: str, base_dir: Path) -> str:
    """Remove the absolute path prefix from 'Complete name' lines."""
    pfx_posix   = str(base_dir).replace("\\", "/").rstrip("/") + "/"
    pfx_windows = str(base_dir).replace("/", "\\").rstrip("\\") + "\\"

    def _replace(m: re.Match) -> str:
        label, full = m.group(1), m.group(2).strip()
        if full.startswith(pfx_posix):
            return label + full[len(pfx_posix):]
        if full.startswith(pfx_windows):
            return label + full[len(pfx_windows):]
        return m.group(0)

    return re.sub(
        r"(^\s*Complete name\s*:\s*)([^\r\n]+)",
        _replace, text or "", flags=re.MULTILINE,
    )


# ========================= VALUE FORMATTERS =========================

def _safe_int(val, default: int = 0) -> int:
    try:
        m = re.search(r"-?\d+", str(val).split("/")[0].strip())
        return int(m.group(0)) if m else default
    except (ValueError, TypeError):
        return default


def _safe_float(val, default: float = 0.0) -> float:
    try:
        return float(str(val).split("/")[0].strip())
    except (ValueError, TypeError):
        return default


def fmt_filesize(size_bytes: int) -> str:
    if size_bytes >= 1 << 30:
        return f"{size_bytes / (1 << 30):.2f} GiB  ({size_bytes:,} bytes)"
    if size_bytes >= 1 << 20:
        return f"{size_bytes / (1 << 20):.2f} MiB  ({size_bytes:,} bytes)"
    if size_bytes >= 1 << 10:
        return f"{size_bytes / (1 << 10):.2f} KiB  ({size_bytes:,} bytes)"
    return f"{size_bytes} bytes"


def fmt_duration(seconds: float) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s   = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    return f"{m}m {s:02d}s"


def fmt_bitrate(bps: float) -> str:
    if bps >= 1_000_000:
        return f"{bps / 1_000_000:.2f} Mbps"
    if bps >= 1_000:
        return f"{bps / 1_000:.0f} Kbps"
    return f"{bps:.0f} bps"


def resolution_label(width: int, height: int) -> str:
    if width >= 3800 or height >= 2100:
        return "2160p"
    if width >= 1900 or height >= 1000:
        return "1080p"
    if width >= 1200 or height >= 700:
        return "720p"
    if width >= 640 or height >= 470:
        return "480p"
    return f"{height}p" if height else "N/A"


def aspect_ratio(width: int, height: int) -> str:
    if not width or not height:
        return ""
    r = width / height
    for label, ref, tol in [
        ("16:9",   16 / 9,  0.05),
        ("4:3",    4 / 3,   0.05),
        ("21:9",   21 / 9,  0.07),
        ("1.85:1", 1.85,    0.03),
        ("2.35:1", 2.35,    0.03),
        ("2.39:1", 2.39,    0.03),
    ]:
        if abs(r - ref) < tol:
            return label
    g = gcd(width, height)
    return f"{width // g}:{height // g}"


def video_codec_display(fmt: str) -> str:
    u = fmt.upper()
    if "AVC"   in u or "H.264" in u: return "H.264 (AVC)"
    if "HEVC"  in u or "H.265" in u: return "H.265 (HEVC)"
    if "AV1"   in u:                 return "AV1"
    if "VP9"   in u:                 return "VP9"
    if "VC-1"  in u:                 return "VC-1"
    return fmt


def audio_codec_display(fmt: str, profile: str = "", commercial: str = "") -> str:
    u = fmt.upper()
    if u.startswith("E-AC-3") or u.startswith("EAC3"):
        return "DDP (E-AC-3)"
    if u.startswith("AC-3") or u == "AC3":
        return "DD (AC-3)"
    if u == "MLP FBA" or "TRUEHD" in u:
        return "TrueHD"
    if u.startswith("DTS"):
        p, com = profile.upper(), commercial.upper()
        if "X" in p or "DTS:X" in com:
            return "DTS-X"
        if "MA" in p or ("DTS-HD" in com and "MASTER" in com):
            return "DTS-HD MA"
        if "HRA" in p:
            return "DTS-HD HRA"
        return "DTS"
    if u == "AAC":   return "AAC"
    if u == "FLAC":  return "FLAC"
    if "OPUS" in u:  return "Opus"
    if "PCM"  in u:  return "LPCM"
    return fmt


def channels_display(ch: int) -> str:
    if ch >= 8: return "7.1"
    if ch >= 6: return "5.1"
    if ch >= 2: return "2.0"
    if ch == 1: return "1.0"
    return str(ch)


# ========================= HIERARCHICAL FILE LISTING =========================

def _idx_to_letters(n: int) -> str:
    """
    Convert a 0-based index to an uppercase letter sequence.
    0 → 'A', 1 → 'B', …, 25 → 'Z', 26 → 'AA', 27 → 'AB', …
    """
    n += 1
    letters = ""
    while n > 0:
        n -= 1
        letters = chr(ord("A") + (n % 26)) + letters
        n //= 26
    return letters


def list_files_hierarchical(base_dir: Path, max_depth: int = 3) -> list[dict]:
    """
    Return a flat list of dicts representing the hierarchical file/folder
    structure up to *max_depth* levels deep.

    Each dict:
        key    – hierarchical label, e.g. "1", "2A", "3AA"
        path   – Path object
        is_dir – bool
        depth  – 1-based nesting depth
    """
    items: list[dict] = []
    top_counter = [0]

    def _scan(directory: Path, parent_key: str | None, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            raw = [
                e for e in directory.iterdir()
                if not e.name.startswith(".") and e.name != "__pycache__"
            ]
            entries = sorted(raw, key=lambda p: (p.stat().st_mtime, p.name.lower()))
        except (PermissionError, OSError):
            return

        visible = [
            e for e in entries
            if e.is_dir() or (e.is_file() and e.suffix.lower() in VIDEO_EXTS)
        ]

        for idx, entry in enumerate(visible):
            if depth == 1:
                top_counter[0] += 1
                key = str(top_counter[0])
            else:
                key = (parent_key or "") + _idx_to_letters(idx)

            items.append({
                "key":    key,
                "path":   entry,
                "is_dir": entry.is_dir(),
                "depth":  depth,
            })

            if entry.is_dir():
                _scan(entry, key, depth + 1)

    _scan(base_dir, None, 1)
    return items


def display_hierarchical_list(items: list[dict]) -> None:
    """Pretty-print the hierarchical file listing."""
    for item in items:
        indent  = "  " * (item["depth"] - 1)
        typ     = (f"{c.PURPLE}Dir{c.RESET}"  if item["is_dir"]
                   else f"{c.CYAN}File{c.RESET}")
        name    = item["path"].name + ("/" if item["is_dir"] else "")
        key_str = f"{c.WHITE}{item['key']}{c.RESET}"
        print(f"  {indent}{key_str}. {name} ({typ})")


# ========================= INTERACTIVE FILE SELECTION =========================

def select_files_interactive() -> tuple[Path | None, Path | None, Path | None]:
    """
    Show a hierarchical file listing and ask the user to enter
    three keys: Source, Encoded, Comparison (e.g. "1,2A,3AA").

    Returns (source_path, encoded_path, comparison_path).
    Allows folder navigation by entering a single folder key.
    """
    base_dir = Path.cwd()

    while True:
        banner()
        print(f"{c.BOLD}{c.CYAN}Directory: {base_dir}{c.RESET}\n")
        items = list_files_hierarchical(base_dir)

        if not items:
            print(f"  {c.YELLOW}No video files or sub-folders found here.{c.RESET}")
        else:
            display_hierarchical_list(items)

        print()
        print(f"  {c.DIM}Enter folder key to navigate into it.{c.RESET}")
        print(f"  {c.DIM}Enter Source,Encoded,Comparison keys to select"
              f" (e.g. 1,2A,3AA).{c.RESET}")
        print(f"  {c.WHITE}0{c.RESET} / {c.WHITE}..{c.RESET} = go up  "
              f"  {c.WHITE}q{c.RESET} = quit")

        raw = input(f"\n{c.BOLD}> {c.RESET}").strip()

        if not raw:
            continue
        if raw.lower() == "q":
            sys.exit(0)
        if raw in ("0", ".."):
            parent = base_dir.parent
            if parent != base_dir:
                base_dir = parent
            continue

        item_map = {item["key"].upper(): item for item in items}

        # Single key → navigate into folder
        if raw.upper() in item_map and item_map[raw.upper()]["is_dir"]:
            base_dir = item_map[raw.upper()]["path"]
            continue

        # Try parsing as three comma-separated keys
        parts = [p.strip().upper() for p in raw.split(",")]
        if len(parts) != 3:
            print(f"\n  {c.RED}✗ Enter exactly 3 keys separated by commas, "
                  f"or a single folder key to navigate.{c.RESET}")
            input("  Press Enter to continue…")
            continue

        source_key, encoded_key, comp_key = parts
        errs:  list[str]             = []
        paths: dict[str, Path | None] = {
            "source": None, "encoded": None, "comparison": None,
        }

        for key, role in [
            (source_key, "source"),
            (encoded_key, "encoded"),
            (comp_key, "comparison"),
        ]:
            item = item_map.get(key)
            if item is None:
                errs.append(f"Key '{key}' not found in listing")
            elif item["is_dir"]:
                errs.append(f"Key '{key}' is a folder – select a video file")
            else:
                paths[role] = item["path"]

        if errs:
            for msg in errs:
                print(f"\n  {c.RED}✗ {msg}{c.RESET}")
            input("  Press Enter to try again…")
            continue

        return paths["source"], paths["encoded"], paths["comparison"]


# ========================= SCREENSHOT EXTRACTION =========================

def take_frames(
    video: Path,
    name_prefix: str,
    percents: list[float] = FRAME_PERCENTS,
    label: str = "screenshots",
) -> list[Path]:
    """
    Extract one frame per entry in *percents* (each 0–1 fraction of duration).

    Output filename format:  {name_prefix}{serial:03d}.{ext}
    e.g.  "ShowName.S01E01.1080p.AMZN.WEB-DL.DDP5.1.H.264-Group001.png"

    Returns the list of Path objects that were actually created.
    """
    try:
        raw = subprocess.check_output(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video),
            ],
            startupinfo=hide_window(),
        ).decode().strip()
        duration = float(raw)
    except Exception:
        error(f"Could not get duration for {video.name}")
        return []

    if duration <= 0:
        error(f"Invalid duration ({duration}s) for {video.name}")
        return []

    ext    = "png" if LOSSLESS_SCREENSHOT else "jpg"
    max_mb = 32 if IMAGE_HOST.lower() == "imgbb" else 64
    files: list[Path] = []

    log(f"Taking {len(percents)} {label} from {c.BOLD}{video.name}{c.RESET}…", "📷")

    for serial, pct in enumerate(percents, 1):
        timestamp = duration * pct
        out = Path(f"{name_prefix}{serial:03d}.{ext}")

        cmd = [
            "ffmpeg", "-ss", f"{timestamp:.3f}", "-i", str(video),
            "-vframes", "1", "-q:v", "1", "-y", str(out),
        ]
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            startupinfo=hide_window(),
        )

        if not out.exists():
            error(f"Frame {serial}/{len(percents)} failed for {video.name}")
            continue

        # Fall back to JPEG if PNG is too large for the host
        size_mb = out.stat().st_size / (1 << 20)
        if LOSSLESS_SCREENSHOT and ext == "png" and size_mb > max_mb:
            out.unlink()
            out = Path(f"{name_prefix}{serial:03d}.jpg")
            cmd[-1] = str(out)
            subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=hide_window(),
            )
            if not out.exists():
                error(f"Frame {serial} JPEG fallback failed for {video.name}")
                continue

        files.append(out)
        _GENERATED_FILES.append(out)

    success(f"{len(files)}/{len(percents)} {label} captured.")
    return files


# ========================= IMAGE UPLOAD =========================

def _bounded_workers(n: int) -> int:
    cpu = os.cpu_count() or 1
    return max(1, min(
        MAX_CONCURRENT_UPLOADS,
        n,
        max(MIN_IO_WORKERS, cpu * IO_WORKER_MULTIPLIER),
    ))


def _parse_upload_error(data: dict) -> str:
    err = data.get("error")
    if isinstance(err, dict):
        return str(err.get("message") or err.get("info") or err)
    return str(err) if err else "unknown error"


def _upload_via_host(img: Path, host: str) -> tuple[str | None, bool]:
    """Returns (url, is_fatal_error)."""
    filename = img.name
    try:
        if host == "imgbb":
            if not IMGBB_API_KEY:
                return None, False
            with img.open("rb") as fh:
                r = requests.post(
                    "https://api.imgbb.com/1/upload",
                    params={"key": IMGBB_API_KEY},
                    data={"name": quote(filename, safe="")},
                    files={"image": fh},
                    timeout=UPLOAD_TIMEOUT,
                )
            if r.status_code == 200:
                data     = r.json()
                img_data = data.get("data") or {}
                url      = img_data.get("url") or img_data.get("display_url")
                if data.get("success") and url:
                    return url, False
                error(f"imgbb upload failed ({filename}): {_parse_upload_error(data)}")

        elif host == "freeimage":
            with img.open("rb") as fh:
                r = requests.post(
                    "https://freeimage.host/api/1/upload",
                    params={"key": FREEIMAGE_API_KEY},
                    files={"source": fh},
                    data={"format": "json", "name": quote(filename, safe="")},
                    timeout=UPLOAD_TIMEOUT,
                )
            if r.status_code == 200:
                data = r.json()
                if data.get("status_code") == 200 and data.get("image", {}).get("url"):
                    return data["image"]["url"], False
                error(f"freeimage upload failed ({filename}): {_parse_upload_error(data)}")

    except json.JSONDecodeError as exc:
        error(f"{host} invalid JSON response ({filename}): {exc}")
    except requests.RequestException as exc:
        error(f"{host} network error ({filename}): {exc}")
    except OSError as exc:
        error(f"{host} file error ({filename}): {exc}")
        return None, True

    return None, False


def upload_image(img: Path) -> str | None:
    primary = IMAGE_HOST.lower()
    hosts   = [primary] + [h for h in ("imgbb", "freeimage") if h != primary]
    for host in hosts:
        url, fatal = _upload_via_host(img, host)
        if url:
            return url
        if fatal:
            break
    return None


def upload_images_concurrent(images: list[Path]) -> list[str]:
    """
    Upload *images* concurrently.
    Returns a list of URLs in the same order as *images*
    (empty string where upload failed).
    """
    if not images:
        return []

    total  = len(images)
    done   = [0]
    result_map: dict[int, str] = {}

    log(f"Uploading {total} encoded screenshot(s)…", "⬆")

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=_bounded_workers(total)
    ) as executor:
        future_map = {executor.submit(upload_image, img): i
                      for i, img in enumerate(images)}
        for future in concurrent.futures.as_completed(future_map):
            i = future_map[future]
            try:
                url = future.result()
            except Exception as exc:
                error(f"Upload exception (image {i + 1}): {exc}")
                url = None
            if url:
                result_map[i] = url
            done[0] += 1
            log(f"  uploaded {done[0]}/{total}", "⬆", c.CYAN)

    urls = [result_map.get(i, "") for i in range(total)]
    success(f"Uploaded {sum(1 for u in urls if u)}/{total} encoded screenshots.")
    return urls


# ========================= TORRENT CREATION =========================

def create_torrent(target: Path, include_srt: bool | None = None) -> bool:
    global _GENERATED_TORRENT

    if not CREATE_TORRENT_FILE:
        log("Torrent creation disabled.", "Skip")
        return True

    if not shutil.which("mkbrr"):
        error("mkbrr not found! → https://github.com/autobrr/mkbrr")
        return False

    out = target.parent / f"{target.name}.torrent"

    # Do NOT overwrite a torrent that already existed before this script ran
    if out.exists():
        log(f"Torrent already exists: {out.name} – skipping.", "Skip", c.YELLOW)
        return True

    # ---- build exclude list ----
    exclude: list[str] = []
    if target.is_dir():
        exclude.extend(["*.nfo", "*.txt", "*.srr"])
        _skip_dirs = {
            "screens", "screen", "proof", "screenshots", "screenshot",
            "sample", "samples",
        }
        for item in target.rglob("*"):
            ln = item.name.lower()
            try:
                rel = item.relative_to(target).as_posix()
            except ValueError:
                continue
            if item.is_dir() and ln in _skip_dirs:
                pattern = f"{rel}/**"
                if pattern not in exclude:
                    exclude.append(pattern)
            elif item.is_file() and ln in _skip_dirs:
                if rel not in exclude:
                    exclude.append(rel)

        srt_files = list(target.rglob("*.srt"))
        if srt_files:
            if include_srt is None:
                ans = input(
                    f"\n{c.BOLD}Include .srt files in torrent? [y/N]: {c.RESET}"
                ).strip().lower()
                include_srt = ans == "y"
            if not include_srt:
                exclude.append("*.srt")

    # ---- build command ----
    cmd = [
        "mkbrr", "create",
        "-t", TRACKER_ANNOUNCE,
        f"--private={'true' if PRIVATE_TORRENT else 'false'}",
        "-o", str(out),
    ]

    # NEW: optional torrent comment
    if ADD_TORRENT_COMMENT and TORRENT_COMMENT.strip():
        cmd.extend(["--comment", TORRENT_COMMENT.strip()])

    for pattern in exclude:
        cmd.extend(["--exclude", pattern])
    cmd.append(str(target))

    # ---- run with progress bar ----
    log("Creating torrent…", "🔒")
    _pct_re = re.compile(r"(\d+)\s*%")
    _last   = [-1]
    bar_len = 12

    def _bar(pct: int) -> str:
        filled = int(bar_len * pct // 100)
        return (
            f"{c.CYAN}Torrent: "
            f"[{'█' * filled}{'▒' * (bar_len - filled)}] {pct}%{c.RESET}"
        )

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
        startupinfo=hide_window(),
    )

    try:
        sys.stdout.write(f"\r\033[K{_bar(0)}\n")
        sys.stdout.flush()
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                m = _pct_re.search(line.strip())
                if m:
                    pct = min(int(m.group(1)), 100)
                    if pct != _last[0]:
                        sys.stdout.write(f"\033[A\r\033[K{_bar(pct)}\n")
                        sys.stdout.flush()
                        _last[0] = pct
                elif "Wrote" in line:
                    sys.stdout.write(f"\033[A\r\033[K{_bar(100)}\n")
                    sys.stdout.flush()
    finally:
        sys.stdout.write("\033[A\r\033[K")
        sys.stdout.flush()

    rc = process.wait()
    if rc == 0 and out.exists():
        _GENERATED_TORRENT = out
        _GENERATED_FILES.append(out)
        success(f"Torrent created: {out.name}")
        return True

    error("Torrent creation failed!")
    return False


# ========================= DESCRIPTION GENERATION =========================

def _bb(label: str, value: str) -> str:
    """Return one BBCode field line in the required colour scheme."""
    return (
        f"[color=#7EC544][font=Segoe UI][b][size=5]{label}[/b][/font][/color]"
        f"[color=#037E8C]{value}[/color][/size]"
    )


def _extract_tracks(mi_json: dict) -> dict:
    tracks = mi_json.get("media", {}).get("track", [])
    result: dict = {
        "general": None, "video": None, "audio": [], "text": [], "menu": None,
    }
    for t in tracks:
        tt = t.get("@type", "")
        if   tt == "General"                           : result["general"] = t
        elif tt == "Video"  and result["video"] is None: result["video"]   = t
        elif tt == "Audio"                             : result["audio"].append(t)
        elif tt == "Text"                              : result["text"].append(t)
        elif tt == "Menu"                              : result["menu"] = t
    return result


def generate_description(
    source_path:      Path,
    comparison_path:  Path | None,
    encoded_path:     Path | None,
    mediainfo_text:   str,
    encoded_ss_urls:  list[str],
) -> str:
    """
    Build the full BBCode description using the template from the spec:

    File name / File size / Duration / Video / Audio / Subtitle(s) / Chapters /
    Source(1) / Source(2) / Logs / Frame Comparison / MediaInfo / Screenshots
    """
    mi_json = get_mediainfo_json(source_path)
    tracks  = _extract_tracks(mi_json)
    g       = tracks["general"] or {}
    v       = tracks["video"]
    audios  = tracks["audio"]
    texts   = tracks["text"]
    menu    = tracks["menu"]

    lines: list[str] = []

    # ---- File name ----
    lines.append(_bb("File name:", source_path.name))

    # ---- File size ----
    file_size = _safe_int(g.get("FileSize", 0))
    if not file_size and source_path.is_file():
        file_size = source_path.stat().st_size
    lines.append(_bb("File size:", fmt_filesize(file_size) if file_size else "N/A"))

    # ---- Duration ----
    dur_s = _safe_float(g.get("Duration", 0))
    lines.append(_bb("Duration:", fmt_duration(dur_s) if dur_s else "N/A"))

    # ---- Video ----
    if v:
        codec   = video_codec_display(v.get("Format", ""))
        vbr     = _safe_float(v.get("BitRate") or v.get("BitRate_Nominal", 0))
        width   = _safe_int(v.get("Width",  0))
        height  = _safe_int(v.get("Height", 0))
        res_lbl = resolution_label(width, height)
        fps     = _safe_float(v.get("FrameRate", 0))
        fps_str = f"{fps:.3f} fps" if fps else "N/A"
        res_str = f"{width}x{height}" if (width and height) else "N/A"
        ratio   = aspect_ratio(width, height)
        bdepth  = _safe_int(v.get("BitDepth", 0))
        bits    = f" | {bdepth}-bit" if bdepth else ""
        vid_val = (
            f"{codec} | {fmt_bitrate(vbr) if vbr else 'N/A'} | {res_lbl}"
            f" | {fps_str} | {res_str} | {ratio}{bits}"
        )
        lines.append(_bb("Video:", vid_val))
    else:
        lines.append(_bb("Video:", "N/A"))

    # ---- Audio ----
    def _audio_line(a: dict) -> str:
        lang = (a.get("Language") or "").strip() or "und"
        aco  = audio_codec_display(
            a.get("Format", ""),
            a.get("Format_Profile", ""),
            a.get("Format_Commercial_IfAny", ""),
        )
        ch  = _safe_int(
            str(a.get("Channels") or a.get("Channel(s)", "0")).split("/")[0]
        )
        abr = _safe_float(a.get("BitRate") or a.get("BitRate_Nominal", 0))
        return f"{lang} | {aco} | {channels_display(ch)} | {fmt_bitrate(abr) if abr else 'N/A'}"

    if not audios:
        lines.append(_bb("Audio:", "N/A"))
    elif len(audios) == 1:
        lines.append(_bb("Audio:", _audio_line(audios[0])))
    else:
        for idx, a in enumerate(audios, 1):
            lines.append(_bb(f"Audio Track {idx}:", _audio_line(a)))

    # ---- Subtitles ----
    if texts:
        sub_parts = []
        for t in texts:
            lang  = (t.get("Language") or "").strip()
            title = (t.get("Title")    or "").strip()
            sub_parts.append(lang or title or "Unknown")
        lines.append(_bb("Subtitle(s):", ", ".join(sub_parts)))
    else:
        lines.append(_bb("Subtitle(s):", "N/A"))

    # ---- Chapters ----
    if menu:
        ch_keys = [k for k in menu if not k.startswith("@") and k != "extra"]
        lines.append(_bb("Chapters:", f"{len(ch_keys)} chapters" if ch_keys else "No"))
    else:
        lines.append(_bb("Chapters:", "No"))

    # ---- Source(1) ----
    src1 = strip_p2p_name(source_path.name)
    lines.append(_bb("Source(1):", src1))

    # ---- Source(2) – comparison ----
    if comparison_path:
        src2 = strip_p2p_name(comparison_path.name)
        lines.append(_bb("Source(2):", f"{src2} (For comparison)"))

    # ---- Logs placeholder ----
    lines.append(
        "Logs:[spoiler][b]{logs_keep it as it is i will fill it myself}[/b][/spoiler]"
    )

    # ---- Frame comparison link ----
    lines.append("[url=https://slow.pics/c/SMfy6mje]Frame Comparison[/url]")

    # ---- MediaInfo ----
    lines.append(
        "[center][b][size=5][color=#59E817][font=Oswald]MediaInfo"
        "[/color][/size][/b][/center][b][/font]"
        "[spoiler][mediainfo]" + mediainfo_text + "[/mediainfo][/spoiler]"
    )

    # ---- Screenshots (encoded, uploaded) ----
    ss_bb = (
        "\n".join(f"[img]{u}[/img]" for u in encoded_ss_urls if u)
        if encoded_ss_urls else ""
    )
    lines.append(
        "[color=#59E817][font=Oswald]Screenshots[/color][/size][/b][/center]\n"
        + ss_bb
        + "\n[center][/center][/font]"
    )

    return "\n".join(lines)


# ========================= WEB SERVER HTML =========================

def _build_html(
    description:          str,
    title_str:            str,
    torrent_filename:     str,
    encoded_urls:         list[str],
    comparison_filenames: list[str],
) -> str:
    """Build the full single-page HTML for the encode web UI."""

    # ---- encoded screenshots grid ----
    enc_grid = ""
    for i, url in enumerate(encoded_urls, 1):
        if url:
            enc_grid += (
                f'<div class="ss-item">'
                f'<span class="ss-lbl">Encoded {i:02d}</span>'
                f'<img src="{url}" alt="Encoded {i}" '
                f'style="max-width:100%;border-radius:4px;margin-top:4px">'
                f'</div>\n'
            )

    # ---- comparison screenshots grid ----
    comp_grid = ""
    for i, fname in enumerate(comparison_filenames, 1):
        safe = quote(fname)
        comp_grid += (
            f'<div class="ss-item">'
            f'<span class="ss-lbl">Comparison {i:02d}</span>'
            f'<a class="dl-link" href="/api/comparison/{safe}" download="{fname}">'
            f'⬇ {fname}</a>'
            f'</div>\n'
        )

    comp_names_json  = json.dumps(comparison_filenames)
    # JS for "Download All 10": comparison via fetch+blob, encoded via window.open
    enc_urls_json    = json.dumps([u for u in encoded_urls if u])
    desc_escaped     = (
        description.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Encode Upload Tool</title>
<style>
:root{{--bg:#0e0e10;--sur:#18181c;--brd:#2c2c34;--txt:#e2e2e8;--mut:#6a6a7a;
  --acc:#7c6ff7;--grn:#4ade80;--yel:#facc15;--r:10px}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--txt);
  font-family:'Segoe UI',system-ui,sans-serif;
  min-height:100vh;padding:16px;max-width:960px;margin:0 auto}}
header{{text-align:center;padding-bottom:14px;
  border-bottom:1px solid var(--brd);margin-bottom:18px}}
.logo{{font-size:1.05rem;font-weight:700;color:var(--yel)}}
.card{{background:var(--sur);border:1px solid var(--brd);
  border-radius:var(--r);padding:14px;margin-bottom:14px}}
.lbl{{font-size:.66rem;font-weight:700;text-transform:uppercase;
  letter-spacing:1px;color:var(--mut);margin-bottom:8px}}
.desc{{font-family:'Courier New',monospace;font-size:.73rem;line-height:1.5;
  white-space:pre-wrap;word-break:break-word;max-height:280px;overflow-y:auto;
  padding:8px 10px;background:var(--bg);border:1px solid var(--brd);
  border-radius:6px;margin-bottom:10px;color:#b0bac6}}
.btns{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:6px}}
button{{padding:5px 12px;border-radius:6px;border:1px solid var(--brd);
  background:#22222a;color:var(--txt);cursor:pointer;font-size:.78rem;
  font-weight:500;transition:background .12s}}
button:hover{{background:#2a2a36}}
button.dl{{border-color:#4a8fc0;color:#80b8e0;background:#0a1828}}
button.ok{{border-color:var(--grn);color:var(--grn);background:#0a1f10}}
.tor-name{{font-size:.77rem;color:var(--mut);margin-bottom:8px;word-break:break-all}}
.ss-grid{{display:grid;
  grid-template-columns:repeat(auto-fill,minmax(200px,1fr));
  gap:10px;margin-top:8px}}
.ss-item{{background:var(--bg);border:1px solid var(--brd);
  border-radius:6px;padding:8px}}
.ss-lbl{{font-size:.68rem;color:var(--mut);display:block;margin-bottom:4px}}
.dl-link{{color:#7ab4f0;font-size:.76rem;word-break:break-all;
  text-decoration:none}}
.dl-link:hover{{text-decoration:underline}}
.toast{{position:fixed;bottom:16px;right:16px;background:#22222a;
  border:1px solid var(--brd);border-radius:8px;padding:7px 14px;
  font-size:.80rem;color:var(--grn);opacity:0;transform:translateY(5px);
  transition:opacity .17s,transform .17s;pointer-events:none;z-index:9999}}
.toast.show{{opacity:1;transform:translateY(0)}}
</style>
</head>
<body>
<header>
  <div class="logo">⚡ Encode Comparison &amp; Upload Tool</div>
</header>

<div class="card">
  <div class="lbl">Title</div>
  <div style="padding:8px;background:var(--bg);border:1px solid var(--brd);
    border-radius:6px;font-size:.85rem">{title_str}</div>
</div>

<div class="card">
  <div class="lbl">Description · BBCode</div>
  <pre class="desc" id="desc-box">{desc_escaped}</pre>
  <div class="btns">
    <button onclick="copyDesc()">📋 Copy Description</button>
  </div>
</div>

<div class="card">
  <div class="lbl">Torrent File</div>
  <div class="tor-name">{torrent_filename}</div>
  <div class="btns">
    <button class="dl"
      onclick="window.location.href='/api/torrent'">⬇ Download Torrent</button>
  </div>
</div>

<div class="card">
  <div class="lbl">Encoded Screenshots · uploaded to image host</div>
  <div class="ss-grid">
    {enc_grid or '<span style="color:var(--mut);font-size:.8rem">No encoded screenshots uploaded.</span>'}
  </div>
</div>

<div class="card">
  <div class="lbl">
    Comparison Screenshots · served locally
    &nbsp;
    <button class="dl"
      style="font-size:.70rem;padding:3px 8px"
      onclick="downloadComparison()">⬇ Download All {len(comparison_filenames)} Comparison Screenshots</button>
    {f'<button class="dl" style="font-size:.70rem;padding:3px 8px;margin-left:4px" onclick="downloadAllTen()">⬇ Download All 10</button>' if comparison_filenames and encoded_urls else ''}
  </div>
  <div class="ss-grid">
    {comp_grid or '<span style="color:var(--mut);font-size:.8rem">No comparison screenshots.</span>'}
  </div>
</div>

<div class="toast" id="toast"></div>
<script>
const COMP = {comp_names_json};
const ENC  = {enc_urls_json};
const DESC = document.getElementById('desc-box').textContent;

let _toastTimer = null;
function toast(m) {{
  const t = document.getElementById('toast');
  t.textContent = m;
  t.classList.add('show');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => t.classList.remove('show'), 2500);
}}

async function cpText(s) {{
  try {{ await navigator.clipboard.writeText(s); }}
  catch(e) {{
    const a = document.createElement('textarea');
    a.value = s;
    a.style.cssText = 'position:fixed;opacity:0';
    document.body.appendChild(a);
    a.select();
    document.execCommand('copy');
    document.body.removeChild(a);
  }}
}}

function copyDesc() {{
  cpText(DESC).then(() => toast('✓ Description copied'));
}}

function _dlFile(url, filename, delay) {{
  setTimeout(() => {{
    const a = document.createElement('a');
    a.href     = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }}, delay);
}}

function downloadComparison() {{
  if (!COMP.length) {{ toast('No comparison screenshots.'); return; }}
  COMP.forEach((fname, i) => {{
    _dlFile('/api/comparison/' + encodeURIComponent(fname), fname, i * 650);
  }});
  toast('⬇ Downloading ' + COMP.length + ' comparison screenshot(s)…');
}}

function downloadAllTen() {{
  // Comparison files: local download
  COMP.forEach((fname, i) => {{
    _dlFile('/api/comparison/' + encodeURIComponent(fname), fname, i * 650);
  }});
  // Encoded files: open in new tab (they are already on the image host)
  ENC.forEach((url, i) => {{
    setTimeout(() => window.open(url, '_blank'), (COMP.length + i) * 650);
  }});
  toast('⬇ Downloading all 10 screenshots…');
}}
</script>
</body>
</html>"""


# ========================= WEB SERVER =========================

class _EncodeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        route  = parsed.path

        if route in ("/", "/index.html"):
            self._serve_html()
        elif route == "/api/torrent":
            self._serve_torrent()
        elif route.startswith("/api/comparison/"):
            fname = unquote(route[len("/api/comparison/"):])
            self._serve_comparison(fname)
        else:
            self.send_response(404)
            self.end_headers()

    def _hdr(self, ct: str, length: int | None = None):
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Cache-Control", "no-store, no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        if length is not None:
            self.send_header("Content-Length", str(length))
        self.end_headers()

    def _serve_html(self):
        body = _WEBAPP_HTML.encode("utf-8")
        self._hdr("text/html; charset=utf-8", len(body))
        self.wfile.write(body)

    def _serve_torrent(self):
        if _GENERATED_TORRENT and _GENERATED_TORRENT.exists():
            body  = _GENERATED_TORRENT.read_bytes()
            fname = _GENERATED_TORRENT.name
            self.send_response(200)
            self.send_header("Content-Type", "application/x-bittorrent")
            self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    @staticmethod
    def _safe_filename(name: str) -> str:
        """Strip CR/LF and other control characters to prevent header injection."""
        return re.sub(r"[\r\n\x00-\x1f\x7f]", "", name)

    def _serve_comparison(self, filename: str):
        # Only serve files that this script created as comparison screenshots
        for p in _COMPARISON_SS_PATHS:
            if p.name == filename and p.exists():
                ext  = p.suffix.lower()
                ct   = "image/png" if ext == ".png" else "image/jpeg"
                body = p.read_bytes()
                safe = self._safe_filename(filename)
                self.send_response(200)
                self.send_header("Content-Type", ct)
                self.send_header(
                    "Content-Disposition", f'attachment; filename="{safe}"'
                )
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
        self.send_response(404)
        self.end_headers()

    def log_message(self, *_):
        return

    def handle_error(self, request, client_address):
        if sys.exc_info()[0] in (
            ConnectionResetError, BrokenPipeError, ConnectionAbortedError
        ):
            return
        super().handle_error(request, client_address)


def _kill_port(port: int) -> None:
    import socket as _socket
    import time as _time
    try:
        with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return
    except OSError:
        return
    if sys.platform == "linux":
        try:
            subprocess.run(
                ["fuser", "-k", f"{port}/tcp"],
                capture_output=True, check=False, timeout=5,
            )
            _time.sleep(0.5)
        except Exception:
            pass


def start_server(port: int) -> None:
    global _HTTP_STARTED
    with _HTTP_STARTED_LOCK:
        if _HTTP_STARTED:
            _SERVER_READY.set()
            return
        _HTTP_STARTED = True

    _kill_port(port)

    def _run():
        import time as _t
        global _HTTP_STARTED
        for attempt in range(1, 4):
            try:
                httpd = HTTPServer(("", port), _EncodeHandler)
                log(f"Web UI → http://localhost:{port}", "⚡", c.GREEN)
                _SERVER_READY.set()
                httpd.serve_forever()
                return
            except OSError:
                if attempt < 3:
                    _t.sleep(0.5 * attempt)
                    _kill_port(port)
                else:
                    error(f"Port {port} is busy.")
                    _SERVER_READY.set()
            except Exception as exc:
                error(f"Server error: {exc}")
                _SERVER_READY.set()
                return
        with _HTTP_STARTED_LOCK:
            _HTTP_STARTED = False
        _SERVER_READY.set()

    threading.Thread(target=_run, daemon=True, name="encode-server").start()


# ========================= CLEANUP ON EXIT =========================

def _cleanup() -> None:
    """Delete only the files that this script created."""
    if not AUTO_DELETE_CREATED_FILES:
        return
    deleted: list[str] = []
    for path in list(_GENERATED_FILES):
        if path.exists():
            try:
                path.unlink()
                deleted.append(path.name)
            except OSError:
                pass
    if deleted:
        print(
            f"\n{c.YELLOW}Auto-deleted ({len(deleted)} file(s)): "
            f"{', '.join(deleted)}{c.RESET}"
        )


atexit.register(_cleanup)


# ========================= MAIN =========================

def main() -> None:
    global _WEBAPP_HTML, _COMPARISON_SS_PATHS, _UPLOADED_ENCODED_URLS

    # ---- CLI argument parsing ----
    parser = argparse.ArgumentParser(
        description="Encode comparison & upload tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Flag mode:\n"
            "  python encode.py -s source.mkv -c comparison.mkv -e encoded.mkv\n\n"
            "Interactive mode (no flags):\n"
            "  python encode.py\n"
            "  → hierarchical file picker; enter Source,Encoded,Comparison keys\n"
            "    e.g. '1,2A,3AA'"
        ),
    )
    parser.add_argument("-s", "--source",     metavar="FILE",
                        help="Source file (used for description & torrent)")
    parser.add_argument("-c", "--comparison", metavar="FILE",
                        help="Comparison source file (frames served locally)")
    parser.add_argument("-e", "--encoded",    metavar="FILE",
                        help="Encoded file (frames uploaded to image host)")
    args = parser.parse_args()

    # ---- resolve paths ----
    if args.source or args.comparison or args.encoded:
        # Flag mode
        source_path     = Path(args.source).resolve()     if args.source     else None
        comparison_path = Path(args.comparison).resolve() if args.comparison else None
        encoded_path    = Path(args.encoded).resolve()    if args.encoded    else None

        for label, p in [
            ("source",     source_path),
            ("comparison", comparison_path),
            ("encoded",    encoded_path),
        ]:
            if p is not None and not p.exists():
                error(f"{label} file not found: {p}")
                sys.exit(1)
    else:
        # Interactive mode
        source_path, encoded_path, comparison_path = select_files_interactive()

    if source_path is None:
        error("Source file is required.")
        sys.exit(1)

    banner()
    print(f"  {c.BOLD}{c.PURPLE}Source     → {source_path.name}{c.RESET}")
    if encoded_path:
        print(f"  {c.BOLD}{c.PURPLE}Encoded    → {encoded_path.name}{c.RESET}")
    if comparison_path:
        print(f"  {c.BOLD}{c.PURPLE}Comparison → {comparison_path.name}{c.RESET}")
    print()

    work_dir = source_path.parent

    # ---- MediaInfo for source ----
    log("Getting MediaInfo for source…", "ℹ")
    mediainfo_text = get_mediainfo_text(source_path)
    mediainfo_text = trim_mediainfo_path(mediainfo_text, work_dir)

    # ---- Start torrent creation concurrently ----
    _torrent_ok = [False]

    def _torrent_worker():
        _torrent_ok[0] = create_torrent(source_path)

    torrent_thread = threading.Thread(
        target=_torrent_worker, daemon=True, name="torrent"
    )
    torrent_thread.start()

    # ---- Take comparison & encoded screenshots concurrently ----
    comp_ss: list[Path] = []
    enc_ss:  list[Path] = []

    def _comp_worker():
        nonlocal comp_ss
        prefix = comparison_path.stem   # full stem, NOT stripped
        comp_ss = take_frames(comparison_path, prefix, label="comparison frames")

    def _enc_worker():
        nonlocal enc_ss
        prefix = encoded_path.stem      # full stem, NOT stripped
        enc_ss = take_frames(encoded_path, prefix, label="encoded frames")

    threads: list[threading.Thread] = []
    if comparison_path:
        t = threading.Thread(target=_comp_worker, daemon=True, name="comp-ss")
        threads.append(t)
        t.start()
    if encoded_path:
        t = threading.Thread(target=_enc_worker, daemon=True, name="enc-ss")
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    _COMPARISON_SS_PATHS = list(comp_ss)

    # ---- Upload encoded screenshots concurrently ----
    encoded_urls: list[str] = []
    if enc_ss:
        encoded_urls = upload_images_concurrent(enc_ss)
    _UPLOADED_ENCODED_URLS = encoded_urls

    # ---- Generate description ----
    log("Generating description…", "📝")
    description = generate_description(
        source_path,
        comparison_path,
        encoded_path,
        mediainfo_text,
        encoded_urls,
    )

    # ---- Save .txt (optional) ----
    if not SKIP_TXT:
        txt_path = work_dir / f"{source_path.stem}_encode_description.txt"
        if not txt_path.exists():          # never overwrite pre-existing files
            txt_path.write_text(description, encoding="utf-8")
            _GENERATED_FILES.append(txt_path)
            success(f"Saved description → {txt_path.name}")

    copy_to_clipboard(description)

    # ---- Build the title string (stripped tech tags from source name) ----
    title_str = strip_p2p_name(source_path.name)

    # ---- Wait for torrent thread ----
    torrent_thread.join()
    if not _torrent_ok[0] and CREATE_TORRENT_FILE:
        error("Torrent creation failed!")

    torrent_filename = (
        _GENERATED_TORRENT.name if _GENERATED_TORRENT else f"{source_path.name}.torrent"
    )

    # ---- Build web UI HTML ----
    _WEBAPP_HTML = _build_html(
        description          = description,
        title_str            = title_str,
        torrent_filename     = torrent_filename,
        encoded_urls         = encoded_urls,
        comparison_filenames = [p.name for p in comp_ss],
    )

    # ---- Start web server ----
    if START_HTTP_SERVER:
        start_server(HTTP_PORT)
        _SERVER_READY.wait(timeout=5)

    print(f"\n{c.BOLD}{c.GREEN}ALL DONE!{c.RESET}")
    if START_HTTP_SERVER:
        print(
            f"{c.DIM}Web UI → http://localhost:{HTTP_PORT}  "
            f"(open in browser){c.RESET}"
        )
    print(f"{c.DIM}Generated files will be deleted on exit.{c.RESET}")
    input(f"\nPress {c.BOLD}Enter{c.RESET} to exit…")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{c.YELLOW}Cancelled.{c.RESET}")
