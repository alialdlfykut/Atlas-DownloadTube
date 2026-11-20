import os
import sys
import math
import time
import shutil
import re
import json
import urllib.parse
import threading
import subprocess
import ctypes
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import requests
import yt_dlp

SAVE_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
PORT = 9876

CURRENT_STATUS = {
    "is_downloading": False,
    "title": "",
    "progress": 0,
    "percent": 0,
    "percent_str": "0%",
    "speed": "0.00 MB/s",
    "eta": "--:--",
    "size": "0 MB",
    "status_text": "جاهز",
    "last_finished_file": "",
    "error": ""
}

def sanitize_name(name):
    clean = re.sub(r'[<>:"/\\|?*]', '_', name or "").strip()
    clean = re.sub(r'\s+', ' ', clean)
    if len(clean) > 80:
        clean = clean[:80].strip()
    return clean or f"video_{int(time.time())}"

def download_worker(url, quality, custom_title=""):
    global CURRENT_STATUS
    CURRENT_STATUS["is_downloading"] = True
    CURRENT_STATUS["progress"] = 0.01
    CURRENT_STATUS["percent"] = 1
    CURRENT_STATUS["percent_str"] = "1%"
    CURRENT_STATUS["status_text"] = "جاري الاتصال وسحب التدفق..."
    CURRENT_STATUS["error"] = ""

    try:
        ydl_opts_info = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'no_playlist': True,
            'socket_timeout': 10
        }
        
        info = None
        try:
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            if any(ext in url.lower() for ext in ['.mp4', '.webm', '.m3u8', '.mov', '.ts']):
                direct_download(url)
                return
            raise e

        title = custom_title.strip() if custom_title and custom_title != "فيديو فيسبوك" else ""
        if not title and info:
            title = info.get('title', '')
        if not title or title.lower() in ['facebook post', 'facebook watch', 'video', 'watch', 'reel']:
            if info:
                desc = info.get('description') or ''
                if desc.strip():
                    title = desc.strip().split('\n')[0][:80]
                else:
                    title = info.get('uploader', '') or 'فيديو فيسبوك'
            else:
                title = 'فيديو فيسبوك'

        safe_title = sanitize_name(title)
        CURRENT_STATUS["title"] = title

        out_template = os.path.join(SAVE_DIR, f"{safe_title}.%(ext)s")
        postprocessors = []

        if "Audio" in quality or "صوت" in quality:
            ydl_format = 'bestaudio/best'
            if "WAV" in quality:
                postprocessors = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav'}]
            elif "M4A" in quality:
                postprocessors = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'm4a'}]
            else:
                bitrate = "192"
                if "320" in quality: bitrate = "320"
                elif "256" in quality: bitrate = "256"
                elif "128" in quality: bitrate = "128"
                postprocessors = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': bitrate,
                }]
        elif "p" in quality:
            res_match = re.search(r'(\d+)p', quality)
            height = res_match.group(1) if res_match else "1080"
            ydl_format = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
        else:
            ydl_format = "bestvideo+bestaudio/best"

        stream_index = [0]
        has_multiple_streams = '+' in ydl_format

        def ytdl_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0) or 0
                downloaded = d.get('downloaded_bytes', 0) or 0
                speed = d.get('speed', 0) or 0
                eta = d.get('eta', 0) or 0

                raw_pct = None
                pct_str = d.get('_percent_str', '')
                if pct_str:
                    clean_str = re.sub(r'\x1b\[[0-9;]*m', '', pct_str)
                    m = re.search(r'([\d.]+)\s*%', clean_str)
                    if m:
                        try:
                            raw_pct = float(m.group(1))
                        except Exception:
                            pass

                if raw_pct is None and total > 0 and downloaded > 0:
                    raw_pct = (downloaded / total) * 100.0

                if raw_pct is None:
                    frag_idx = d.get('fragment_index')
                    frag_cnt = d.get('fragment_count')
                    if frag_idx and frag_cnt and frag_cnt > 0:
                        raw_pct = (frag_idx / frag_cnt) * 100.0

                if raw_pct is not None:
                    raw_pct = max(1.0, min(100.0, raw_pct))
                    if has_multiple_streams:
                        if stream_index[0] == 0:
                            calc_pct = raw_pct * 0.85
                        else:
                            calc_pct = 85.0 + (raw_pct * 0.13)
                    else:
                        calc_pct = raw_pct * 0.98

                    calc_pct = max(1.0, min(99.0, calc_pct))
                    CURRENT_STATUS["progress"] = round(calc_pct / 100.0, 3)
                    CURRENT_STATUS["percent"] = int(round(calc_pct))
                    CURRENT_STATUS["percent_str"] = f"{int(round(calc_pct))}%"

                if total > 0:
                    CURRENT_STATUS["size"] = f"{downloaded/(1024*1024):.1f} MB / {total/(1024*1024):.1f} MB"
                elif downloaded > 0:
                    CURRENT_STATUS["size"] = f"{downloaded/(1024*1024):.1f} MB"

                if speed > 0:
                    CURRENT_STATUS["speed"] = f"{speed/(1024*1024):.2f} MB/s"
                if eta > 0:
                    CURRENT_STATUS["eta"] = time.strftime('%M:%S', time.gmtime(eta))
                CURRENT_STATUS["status_text"] = "جاري التحميل..."

            elif d['status'] == 'finished':
                stream_index[0] += 1
                if has_multiple_streams and stream_index[0] == 1:
                    CURRENT_STATUS["progress"] = 0.85
                    CURRENT_STATUS["percent"] = 85
                    CURRENT_STATUS["percent_str"] = "85%"
                    CURRENT_STATUS["status_text"] = "جاري تحميل مسار الصوت..."
                else:
                    CURRENT_STATUS["progress"] = 0.98
                    CURRENT_STATUS["percent"] = 98
                    CURRENT_STATUS["percent_str"] = "98%"
                    CURRENT_STATUS["status_text"] = "جاري دمج الملفات وتجهيز الفيديو..."

        ydl_opts = {
            'format': ydl_format,
            'outtmpl': out_template,
            'merge_output_format': 'mp4',
            'progress_hooks': [ytdl_hook],
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 15,
        }
        if postprocessors:
            ydl_opts['postprocessors'] = postprocessors

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # العثور على الملف الحقيقي الناتج بدقة
        actual_file = None
        for f in os.listdir(SAVE_DIR):
            if f.startswith(safe_title) and not f.endswith('.part') and not f.endswith('.ytdl'):
                actual_file = f
                break
        if not actual_file:
            media_files = [
                f for f in os.listdir(SAVE_DIR)
                if os.path.isfile(os.path.join(SAVE_DIR, f))
                and not f.endswith('.part') and not f.endswith('.ytdl')
                and any(f.lower().endswith(ext) for ext in ['.mp4', '.mp3', '.m4a', '.webm', '.wav', '.mkv'])
            ]
            if media_files:
                media_files.sort(key=lambda x: os.path.getmtime(os.path.join(SAVE_DIR, x)), reverse=True)
                actual_file = media_files[0]
            else:
                actual_file = safe_title + ".mp4"

        CURRENT_STATUS["progress"] = 1.0
        CURRENT_STATUS["percent"] = 100
        CURRENT_STATUS["percent_str"] = "100%"
        CURRENT_STATUS["status_text"] = "اكتمل التحميل بنجاح!"
        CURRENT_STATUS["last_finished_file"] = actual_file
    except Exception as e:
        CURRENT_STATUS["error"] = str(e)
        CURRENT_STATUS["status_text"] = f"خطأ: {str(e)}"
    finally:
        CURRENT_STATUS["is_downloading"] = False

def direct_download(url):
    global CURRENT_STATUS
    try:
        CURRENT_STATUS["status_text"] = "جاري التحميل المباشر..."
        filename = f"video_{int(time.time())}.mp4"
        save_path = os.path.join(SAVE_DIR, filename)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        with requests.get(url, headers=headers, stream=True, timeout=20) as r:
            total = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*128):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = (downloaded / total) * 100.0
                            pct = max(1.0, min(99.0, pct))
                            CURRENT_STATUS["progress"] = round(pct / 100.0, 3)
                            CURRENT_STATUS["percent"] = int(round(pct))
                            CURRENT_STATUS["percent_str"] = f"{int(round(pct))}%"
                            CURRENT_STATUS["size"] = f"{downloaded/(1024*1024):.1f} MB / {total/(1024*1024):.1f} MB"
                        else:
                            CURRENT_STATUS["size"] = f"{downloaded/(1024*1024):.1f} MB"
                            
        CURRENT_STATUS["progress"] = 1.0
        CURRENT_STATUS["percent"] = 100
        CURRENT_STATUS["percent_str"] = "100%"
        CURRENT_STATUS["status_text"] = "اكتمل التحميل بنجاح!"
        CURRENT_STATUS["last_finished_file"] = filename
    except Exception as e:
        CURRENT_STATUS["error"] = str(e)
        CURRENT_STATUS["status_text"] = f"خطأ: {str(e)}"
    finally:
        CURRENT_STATUS["is_downloading"] = False


def open_downloads_and_select(file_name=""):
    try:
        try:
            user32 = ctypes.windll.user32
            WINSTA_ALL = 0x37F
            DESKTOP_ALL = 0x1FF
            hwinsta = user32.OpenWindowStationW("WinSta0", False, WINSTA_ALL)
            if hwinsta: user32.SetProcessWindowStation(hwinsta)
            hdesk = user32.OpenDesktopW("Default", 0, False, DESKTOP_ALL)
            if hdesk: user32.SetThreadDesktop(hdesk)
            user32.AllowSetForegroundWindow(-1)
        except Exception:
            pass

        norm_save_dir = os.path.normpath(SAVE_DIR)
        target_file_path = None

        if file_name:
            cand = os.path.join(SAVE_DIR, file_name)
            if os.path.isfile(cand):
                target_file_path = cand
            else:
                base_cand = os.path.splitext(file_name)[0]
                for f in os.listdir(SAVE_DIR):
                    if f == file_name or os.path.splitext(f)[0] == base_cand or base_cand in f:
                        target_file_path = os.path.join(SAVE_DIR, f)
                        break

        if not target_file_path and CURRENT_STATUS.get("last_finished_file"):
            last_f = CURRENT_STATUS["last_finished_file"]
            cand = os.path.join(SAVE_DIR, last_f)
            if os.path.isfile(cand):
                target_file_path = cand
            else:
                base_cand = os.path.splitext(last_f)[0]
                for f in os.listdir(SAVE_DIR):
                    if f.startswith(base_cand):
                        target_file_path = os.path.join(SAVE_DIR, f)
                        break

        if not target_file_path:
            try:
                media_files = [
                    os.path.join(SAVE_DIR, f) for f in os.listdir(SAVE_DIR)
                    if os.path.isfile(os.path.join(SAVE_DIR, f)) and any(f.lower().endswith(ext) for ext in ['.mp4', '.mp3', '.m4a', '.webm', '.wav', '.mkv'])
                ]
                if media_files:
                    media_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                    target_file_path = media_files[0]
            except Exception:
                pass

        exact_file_name = os.path.basename(target_file_path) if target_file_path else ""

        ps_code = f"""
$saveDir = "{norm_save_dir.replace('"', '`"')}"
$targetFile = "{exact_file_name.replace('"', '`"')}"

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinSnap {{
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern int GetSystemMetrics(int nIndex);
    [DllImport("user32.dll")] public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, UIntPtr dwExtraInfo);

    public static void Snap(IntPtr hWnd) {{
        int screenW = GetSystemMetrics(0);
        int screenH = GetSystemMetrics(1);
        int halfW = screenW / 2;
        int targetW = screenW - halfW;
        int targetH = Math.Max(600, screenH - 55);
        ShowWindow(hWnd, 9);
        SetWindowPos(hWnd, IntPtr.Zero, halfW, 0, targetW, targetH, 0x0040);
        BringWindowToTop(hWnd);
        SetForegroundWindow(hWnd);
    }}

    public static void ClickTaskbarFolder() {{
        uint nx = (uint)(405 * 65535 / 1920);
        uint ny = (uint)(1056 * 65535 / 1080);
        mouse_event(0x8000 | 0x0001, nx, ny, 0, UIntPtr.Zero);
        mouse_event(0x0002, 0, 0, 0, UIntPtr.Zero);
        mouse_event(0x0004, 0, 0, 0, UIntPtr.Zero);
    }}
}}
"@

$sh = New-Object -ComObject Shell.Application
$targetWin = $null

foreach ($w in $sh.Windows()) {{
    if ($w.HWND -gt 0) {{
        $targetWin = $w
        break
    }}
}}

if (-not $targetWin) {{
    [WinSnap]::ClickTaskbarFolder()
    Start-Sleep -Milliseconds 1200
    foreach ($w in $sh.Windows()) {{
        if ($w.HWND -gt 0) {{
            $targetWin = $w
            break
        }}
    }}
}}

if ($targetWin) {{
    $targetWin.Visible = $true
    $targetWin.Navigate($saveDir)
    Start-Sleep -Milliseconds 400
    if ($targetFile) {{
        $folder = $sh.NameSpace($saveDir)
        if ($folder) {{
            $item = $folder.ParseName($targetFile)
            if ($item) {{
                try {{
                    $targetWin.Document.SelectItem($item, 29)
                }} catch {{}}
            }}
        }}
    }}
    [WinSnap]::Snap([IntPtr]$targetWin.HWND)
}} else {{
    Start-Process explorer.exe -ArgumentList $saveDir
}}
"""
        def run_ps():
            try:
                subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_code], capture_output=True)
            except Exception:
                try:
                    if target_file_path:
                        subprocess.Popen(['explorer.exe', f'/select,{os.path.normpath(target_file_path)}'])
                    else:
                        subprocess.Popen(['explorer.exe', norm_save_dir])
                except Exception:
                    pass

        threading.Thread(target=run_ps, daemon=True).start()
        return True, exact_file_name or norm_save_dir
    except Exception as e:
        return False, str(e)


class SilentApiHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        try:
            sys.stderr.write(f"[{time.strftime('%X')}] {format % args}\n")
            sys.stderr.flush()
        except Exception:
            pass

    def send_json(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == '/ping':
            self.send_json({"status": "ok", "app": "Atlas DownloadTube Service", "version": "6.0"})

        elif path == '/status':
            self.send_json(CURRENT_STATUS)

        elif path == '/open_downloads':
            file_param = query.get('file', [''])[0].strip()
            ok, target = open_downloads_and_select(file_param)
            self.send_json({"status": "opened" if ok else "error", "target": target})

        elif path == '/get_file':
            filename = query.get('file', [''])[0]
            target_path = None
            
            candidate = os.path.join(SAVE_DIR, filename)
            if os.path.isfile(candidate):
                target_path = candidate
            else:
                base_query = os.path.splitext(filename)[0]
                for f in os.listdir(SAVE_DIR):
                    base_f = os.path.splitext(f)[0]
                    if f == filename or base_f == base_query or base_f == filename:
                        target_path = os.path.join(SAVE_DIR, f)
                        break
            
            if target_path and os.path.isfile(target_path):
                file_name = os.path.basename(target_path)
                file_size = os.path.getsize(target_path)
                self.send_response(200)
                self.send_header('Content-Type', 'application/octet-stream')
                safe_ascii_name = re.sub(r'[^\x20-\x7E]', '_', file_name)
                encoded_name = urllib.parse.quote(file_name)
                self.send_header('Content-Disposition', f'attachment; filename="{safe_ascii_name}"; filename*=UTF-8\'\'{encoded_name}')
                self.send_header('Content-Length', str(file_size))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(target_path, 'rb') as f:
                    shutil.copyfileobj(f, self.wfile, length=1024 * 1024)
            else:
                self.send_response(404)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b"File not found")

        elif path == '/analyze':
            url = query.get('url', [''])[0]
            custom_title = query.get('title', [''])[0]
            if not url or url.startswith('chrome://') or url.endswith('facebook.com/?_fb_noscript=1') or url == 'https://www.facebook.com/' or url == 'https://www.youtube.com/':
                self.send_json({
                    "status": "error",
                    "message": "يرجى فتح صفحة الفيديو أو النقر عليه لتشغيله أولاً ليتم التقاط رابطه الدقيق."
                })
                return

            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'skip_download': True,
                    'no_playlist': True,
                    'socket_timeout': 8
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                
                title = custom_title.strip() if custom_title and custom_title != "فيديو فيسبوك" else ""
                if not title:
                    title = info.get('title', '')
                if not title or title.lower() in ['facebook post', 'facebook watch', 'video', 'watch', 'reel']:
                    desc = info.get('description') or ''
                    if desc.strip():
                        title = desc.strip().split('\n')[0][:80]
                    else:
                        title = info.get('uploader', '') or 'فيديو فيسبوك'
                
                resolutions = set()
                for f in info.get('formats', []):
                    h = f.get('height')
                    if h and f.get('vcodec') != 'none':
                        resolutions.add(h)
                
                sorted_res = sorted(list(resolutions), reverse=True)
                video_opts = []
                for r in sorted_res:
                    if r >= 2160: video_opts.append(f"🎬 Video - {r}p (4K Ultra HD)")
                    elif r >= 1440: video_opts.append(f"🎬 Video - {r}p (2K QHD)")
                    elif r >= 1080: video_opts.append(f"🎬 Video - {r}p (Full HD)")
                    elif r >= 720: video_opts.append(f"🎬 Video - {r}p (HD)")
                    else: video_opts.append(f"🎬 Video - {r}p (SD)")

                if not video_opts:
                    video_opts.append("🎬 Video - 1080p (Full HD)")
                    video_opts.append("🎬 Video - 720p (HD)")
                    video_opts.append("🎬 Video - جودة قياسية (SD)")

                audio_opts = [
                    "🎵 Audio MP3 - 320 kbps (أعلى جودة Studio)",
                    "🎵 Audio MP3 - 256 kbps (عالية)",
                    "🎵 Audio MP3 - 192 kbps (قياسية)",
                    "🎵 Audio MP3 - 128 kbps (متوسطة)",
                    "🎵 Audio M4A - المسار الأصلي"
                ]

                resp = {
                    "status": "success",
                    "title": title,
                    "video_options": video_opts,
                    "audio_options": audio_opts
                }
                self.send_json(resp)
            except Exception as e:
                title = custom_title if custom_title else "فيديو مباشر"
                if any(ext in url.lower() for ext in ['.mp4', '.webm', '.m3u8', '.mov', 'fbcdn.net']):
                    resp = {
                        "status": "success",
                        "title": title,
                        "video_options": ["🎬 Video - MP4 Direct Stream (أفضل جودة)", "🎬 Video - 720p (HD)"],
                        "audio_options": ["🎵 Audio MP3 - 320 kbps (أعلى جودة)", "🎵 Audio MP3 - 192 kbps"]
                    }
                    self.send_json(resp)
                else:
                    self.send_json({"status": "error", "message": str(e)})

        elif path == '/download':
            url = query.get('url', [''])[0]
            quality = query.get('quality', [''])[0]
            title = query.get('title', [''])[0]
            if url:
                threading.Thread(target=download_worker, args=(url, quality, title), daemon=True).start()
                self.send_json({"status": "success", "message": "Download started"})
            else:
                self.send_json({"status": "error", "message": "Missing URL"})

        else:
            self.send_json({"status": "unknown"})

def main():
    server = ThreadingHTTPServer(('127.0.0.1', PORT), SilentApiHandler)
    server.serve_forever()

if __name__ == "__main__":
    main()
