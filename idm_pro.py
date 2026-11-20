import os
import sys
import math
import time
import shutil
import re
import json
import urllib.parse
import threading
from concurrent.futures import ThreadPoolExecutor
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import customtkinter as ctk
from tkinter import filedialog, messagebox
import yt_dlp

# --- قاموس اللغات (عربي / English) ---
LANGUAGES = {
    "ar": {
        "title": "IDM Ultra Engine - مدير التحميل الذكي والصوتيات المتكامل",
        "header_tag": "النسخة الشاملة v4.0",
        "lang_label": "🌐 اللغة:",
        "theme_label": "🎨 الثيم:",
        "mode_label": "🌓 المظهر:",
        "ext_btn": "🧩 إضافة كروم",
        "url_label": "رابط التحميل:",
        "url_placeholder": "ضع رابط فيديو (YouTube, TikTok, FB...) أو رابط ملف مباشر...",
        "analyze_btn": "🔍 فحص الرابط",
        "analyze_loading": "جاري الفحص...",
        "add_queue": "+ القائمة",
        "video_title_default": "العنوان: [لم يتم فحص رابط بعد]",
        "title_prefix": "العنوان: ",
        "file_prefix": "اسم الملف: ",
        "quality_label": "اختر الدقة أو جودة الصوت:",
        "type_badge_default": "النوع: غير محدد",
        "type_video": "النوع: فيديو عبر الإنترنت (متصل بالمتصفح)",
        "type_direct": "النوع: ملف مباشر (Direct File)",
        "browse_btn": "📁 مجلد الحفظ",
        "open_folder": "فتح المجلد",
        "queue_label": "قائمة المهام والانتظار (Queue):",
        "speed": "السرعة: 0.00 MB/s",
        "speed_prefix": "السرعة: ",
        "eta": "الوقت المتبقي: --:--",
        "eta_prefix": "الوقت المتبقي: ",
        "size": "الحجم: 0 MB / 0 MB",
        "size_prefix": "الحجم: ",
        "status_ready": "الحالة: جاهز للبدء (الخادم الداخلي للمتصفح مفعّل)",
        "status_analyzing": "الحالة: جاري فحص الرابط واستخراج الدقات والجودات...",
        "status_analyzed_ok": "الحالة: تم استخراج الجودات! اختر الدقة المطلوبة واضغط بدء التحميل.",
        "status_direct_ready": "الحالة: ملف مباشر جاهز للتحميل السريع.",
        "status_analyze_fail": "الحالة: تعذر جلب معلومات الرابط، تأكد من صحة الرابط.",
        "status_downloading": "جاري التحميل... ",
        "status_merging": "الحالة: جاري معالجة ودمج الصوت والصورة بأعلى جودة...",
        "status_audio_extract": "الحالة: جاري استخراج وتحويل الصوت بالدقة المختارة...",
        "status_done": "اكتمل التحميل بنجاح!",
        "status_cancelled": "تم إلغاء التحميل.",
        "status_failed": "فشل التحميل.",
        "start_btn": "بدء التحميل",
        "cancel_btn": "إلغاء التحميل",
        "best_video": "أفضل جودة فيديو متاحة (Best Video)",
        "direct_download_opt": "تحميل مباشر متوازي (ملف عادي)",
        "msg_empty_url": "يرجى إدخال رابط للتحميل أولاً!",
        "msg_queue_dup": "الرابط فارغ أو موجود مسبقاً في القائمة.",
        "msg_success_title": "نجاح",
        "msg_success_body": "تم التحميل بنجاح وحفظ الملف في مجلد التنزيلات!",
        "msg_error_title": "خطأ",
        "msg_error_body": "حدث خطأ أثناء التحميل: ",
        "ext_guide_title": "طريقة تثبيت إضافة جوجل كروم",
        "ext_guide_body": "لتثبيت إضافة المتصفح بسهولة:\n1. افتح جوجل كروم واكتب في شريط العنوان: chrome://extensions\n2. فعّل 'وضع مطوّر البرامج' (Developer mode) في أعلى اليمين.\n3. اضغط على 'تحميل حزمة غير مضغوطة' (Load unpacked).\n4. اختر المجلد: chrome_extension الموجود بجانب البرنامج.\n\nسيظهر زر التحميل العائم تلقائياً فوق أي فيديو تتصفحه!"
    },
    "en": {
        "title": "IDM Ultra Engine - Smart Video & Audio Downloader",
        "header_tag": "Ultimate Edition v4.0",
        "lang_label": "🌐 Lang:",
        "theme_label": "🎨 Theme:",
        "mode_label": "🌓 Mode:",
        "ext_btn": "🧩 Chrome Ext",
        "url_label": "Download URL:",
        "url_placeholder": "Paste video link (YouTube, TikTok, FB...) or direct file URL...",
        "analyze_btn": "🔍 Analyze URL",
        "analyze_loading": "Analyzing...",
        "add_queue": "+ Queue",
        "video_title_default": "Title: [No URL analyzed yet]",
        "title_prefix": "Title: ",
        "file_prefix": "Filename: ",
        "quality_label": "Choose Quality or Audio Bitrate:",
        "type_badge_default": "Type: Undetermined",
        "type_video": "Type: Online Streaming Media (Browser Connected)",
        "type_direct": "Type: Direct Download File",
        "browse_btn": "📁 Save Folder",
        "open_folder": "Open Folder",
        "queue_label": "Download Queue (Waiting List):",
        "speed": "Speed: 0.00 MB/s",
        "speed_prefix": "Speed: ",
        "eta": "ETA: --:--",
        "eta_prefix": "ETA: ",
        "size": "Size: 0 MB / 0 MB",
        "size_prefix": "Size: ",
        "status_ready": "Status: Ready (Browser Bridge Server Running on port 9876)",
        "status_analyzing": "Status: Analyzing link and extracting formats...",
        "status_analyzed_ok": "Status: Formats extracted! Select quality and press Start.",
        "status_direct_ready": "Status: Direct file ready for multi-threaded download.",
        "status_analyze_fail": "Status: Failed to inspect URL, please check the link.",
        "status_downloading": "Downloading... ",
        "status_merging": "Status: Merging audio & video streams...",
        "status_audio_extract": "Status: Extracting & converting audio bitrate...",
        "status_done": "Download completed successfully!",
        "status_cancelled": "Download cancelled.",
        "status_failed": "Download failed.",
        "start_btn": "Start Download",
        "cancel_btn": "Cancel Download",
        "best_video": "Best Available Video Quality",
        "direct_download_opt": "Direct Multi-threaded Download",
        "msg_empty_url": "Please enter a download URL first!",
        "msg_queue_dup": "URL is empty or already in the queue.",
        "msg_success_title": "Success",
        "msg_success_body": "Download completed and saved to your folder!",
        "msg_error_title": "Error",
        "msg_error_body": "An error occurred during download: ",
        "ext_guide_title": "How to Install Chrome Extension",
        "ext_guide_body": "To install the Chrome extension:\n1. Open Chrome and navigate to: chrome://extensions\n2. Enable 'Developer mode' in the top right.\n3. Click 'Load unpacked'.\n4. Select the folder: chrome_extension\n\nThe floating download button will now appear on all video pages!"
    }
}

# --- لوحة ألوان الثيمات العصرية ---
COLOR_THEMES = {
    "Cyber Blue (أزرق)": {
        "primary": "#007bff",
        "hover": "#0056b3",
        "accent": "#17a2b8",
        "card_bg": "#1e222d"
    },
    "Emerald Green (أخضر)": {
        "primary": "#28a745",
        "hover": "#218838",
        "accent": "#20c997",
        "card_bg": "#1d2920"
    },
    "Royal Purple (بنفسجي)": {
        "primary": "#6f42c1",
        "hover": "#59359a",
        "accent": "#e83e8c",
        "card_bg": "#251d2f"
    },
    "Sunset Orange (برتقالي)": {
        "primary": "#fd7e14",
        "hover": "#d35400",
        "accent": "#ffc107",
        "card_bg": "#2c221a"
    },
    "Crimson Red (أحمر)": {
        "primary": "#dc3545",
        "hover": "#b02a37",
        "accent": "#e74c3c",
        "card_bg": "#2c1d1e"
    }
}

# --- معالج طلبات إضافة المتصفح (Local HTTP API) ---
class IDMApiHandler(BaseHTTPRequestHandler):
    app_instance = None

    def log_message(self, format, *args):
        pass # كتم سجلات الكونسول الزائدة

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

        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        if path == '/ping':
            resp = {"status": "ok", "app": "IDM Ultra Engine", "version": "4.0"}
            self.wfile.write(json.dumps(resp).encode('utf-8'))

        elif path == '/analyze':
            url = query.get('url', [''])[0]
            if not url:
                self.wfile.write(json.dumps({"status": "error", "message": "Missing URL"}).encode('utf-8'))
                return

            try:
                ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                
                title = info.get('title', 'Video')
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
                
                audio_opts = [
                    "🎵 Audio MP3 - 320 kbps (Studio)",
                    "🎵 Audio MP3 - 256 kbps (Very High)",
                    "🎵 Audio MP3 - 192 kbps (High Quality)",
                    "🎵 Audio MP3 - 128 kbps (Standard)",
                    "🎵 Audio M4A - Original Track",
                    "🎵 Audio WAV - Lossless"
                ]

                resp = {
                    "status": "success",
                    "title": title,
                    "video_options": video_opts,
                    "audio_options": audio_opts
                }
                self.wfile.write(json.dumps(resp).encode('utf-8'))
            except Exception as e:
                resp = {"status": "error", "message": str(e)}
                self.wfile.write(json.dumps(resp).encode('utf-8'))

        elif path == '/download':
            url = query.get('url', [''])[0]
            quality = query.get('quality', [''])[0]
            if url and self.app_instance:
                self.app_instance.trigger_external_download(url, quality)
                self.wfile.write(json.dumps({"status": "success", "message": "Download started"}).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({"status": "error"}).encode('utf-8'))

        else:
            self.wfile.write(json.dumps({"status": "unknown"}).encode('utf-8'))


class UltimateIDMPro(ctk.CTk):
    def __init__(self):
        super().__init__()

        # الإعدادات الافتراضية
        self.current_lang = "ar"
        self.current_theme = "Cyber Blue (أزرق)"
        self.current_mode = "Dark"

        ctk.set_appearance_mode(self.current_mode)
        ctk.set_default_color_theme("blue")

        self.title(LANGUAGES[self.current_lang]["title"])
        self.geometry("900x750")
        self.resizable(False, False)

        # الثوابت
        self.num_threads = 8
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        # المتغيرات الأساسية
        self.download_queue = []
        self.is_downloading = False
        self.is_video_mode = False
        self.cancel_flag = False
        
        self.downloaded_bytes = 0
        self.total_file_size = 0
        self.last_clipboard_text = ""
        self.lock = threading.Lock()
        
        self.save_directory = os.path.join(os.path.expanduser("~"), "Downloads")
        self.current_url = ""
        self.video_info = None

        # تشغيل خادم الربط المحلي لمتصفح كروم
        IDMApiHandler.app_instance = self
        threading.Thread(target=self.start_api_server, daemon=True).start()

        # بناء الواجهة
        self.build_ui()
        self.apply_theme()
        
        # مراقبة الحافظة
        self.after(1000, self.monitor_clipboard_loop)

    def start_api_server(self):
        """خادم خلفي خفيف لاستقبال أوامر إضافة المتصفح فوراً"""
        try:
            server = HTTPServer(('127.0.0.1', 9876), IDMApiHandler)
            server.serve_forever()
        except Exception:
            pass

    def t(self, key):
        return LANGUAGES[self.current_lang].get(key, key)

    def safe_ui(self, func, *args, **kwargs):
        self.after(0, lambda: func(*args, **kwargs))

    def build_ui(self):
        # 1. شريط الإعدادات العلوي
        self.settings_bar = ctk.CTkFrame(self, height=45, corner_radius=8, fg_color="#181a1f")
        self.settings_bar.pack(fill="x", padx=20, pady=(12, 6))

        # عنوان وشعار البرنامج
        self.logo_label = ctk.CTkLabel(self.settings_bar, text="⚡ IDM Ultra Pro", font=("Segoe UI", 13, "bold"), text_color="#00FF7F")
        self.logo_label.pack(side="left", padx=15)

        # زر مساعدة تثبيت إضافة كروم
        self.ext_guide_btn = ctk.CTkButton(self.settings_bar, text=self.t("ext_btn"), width=110, height=28, fg_color="#495057", hover_color="#6c757d", font=("Segoe UI", 11, "bold"), command=self.show_ext_guide)
        self.ext_guide_btn.pack(side="left", padx=5)

        # اختيار المظهر
        self.mode_label = ctk.CTkLabel(self.settings_bar, text=self.t("mode_label"), font=("Segoe UI", 11, "bold"))
        self.mode_label.pack(side="right", padx=(5, 10))

        self.mode_menu = ctk.CTkOptionMenu(self.settings_bar, values=["Dark", "Light", "System"], width=85, height=28, command=self.on_mode_change)
        self.mode_menu.pack(side="right", padx=5)
        self.mode_menu.set(self.current_mode)

        # اختيار الثيم
        self.theme_menu = ctk.CTkOptionMenu(self.settings_bar, values=list(COLOR_THEMES.keys()), width=160, height=28, command=self.on_theme_change)
        self.theme_menu.pack(side="right", padx=5)
        self.theme_menu.set(self.current_theme)

        self.theme_lbl = ctk.CTkLabel(self.settings_bar, text=self.t("theme_label"), font=("Segoe UI", 11, "bold"))
        self.theme_lbl.pack(side="right", padx=(5, 5))

        # اختيار اللغة
        self.lang_menu = ctk.CTkOptionMenu(self.settings_bar, values=["العربية (Arabic)", "English"], width=130, height=28, command=self.on_lang_change)
        self.lang_menu.pack(side="right", padx=5)
        self.lang_menu.set("العربية (Arabic)" if self.current_lang == "ar" else "English")

        self.lang_lbl = ctk.CTkLabel(self.settings_bar, text=self.t("lang_label"), font=("Segoe UI", 11, "bold"))
        self.lang_lbl.pack(side="right", padx=(10, 5))

        # 2. إطار إدخال الرابط وفحصه
        self.top_frame = ctk.CTkFrame(self, corner_radius=10)
        self.top_frame.pack(fill="x", padx=20, pady=6)

        self.url_label = ctk.CTkLabel(self.top_frame, text=self.t("url_label"), font=("Segoe UI", 12, "bold"))
        self.url_label.grid(row=0, column=0, padx=10, pady=12, sticky="w")

        self.url_entry = ctk.CTkEntry(self.top_frame, width=520, placeholder_text=self.t("url_placeholder"))
        self.url_entry.grid(row=0, column=1, padx=5, pady=12)

        self.analyze_btn = ctk.CTkButton(self.top_frame, text=self.t("analyze_btn"), width=115, height=34, font=("Segoe UI", 12, "bold"), command=self.start_analysis_thread)
        self.analyze_btn.grid(row=0, column=2, padx=5, pady=12)

        self.add_queue_btn = ctk.CTkButton(self.top_frame, text=self.t("add_queue"), width=85, height=34, command=self.add_to_queue)
        self.add_queue_btn.grid(row=0, column=3, padx=(0, 10), pady=12)

        # 3. إطار معلومات الفيديو واختيار الدقة / الصوت
        self.media_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=COLOR_THEMES[self.current_theme]["card_bg"])
        self.media_frame.pack(fill="x", padx=20, pady=6)

        self.video_title_label = ctk.CTkLabel(self.media_frame, text=self.t("video_title_default"), font=("Segoe UI", 12, "bold"), text_color="#17a2b8", anchor="w")
        self.video_title_label.pack(fill="x", padx=15, pady=(10, 6))

        self.quality_row = ctk.CTkFrame(self.media_frame, fg_color="transparent")
        self.quality_row.pack(fill="x", padx=15, pady=(0, 10))

        self.quality_label = ctk.CTkLabel(self.quality_row, text=self.t("quality_label"), font=("Segoe UI", 11, "bold"))
        self.quality_label.pack(side="left")

        self.quality_menu = ctk.CTkOptionMenu(self.quality_row, values=[self.t("best_video")], width=360, height=30)
        self.quality_menu.pack(side="left", padx=12)

        self.type_badge = ctk.CTkLabel(self.quality_row, text=self.t("type_badge_default"), font=("Segoe UI", 11), text_color="#adb5bd")
        self.type_badge.pack(side="right")

        # 4. إطار مجلد الحفظ
        self.path_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.path_frame.pack(fill="x", padx=20, pady=4)

        self.browse_btn = ctk.CTkButton(self.path_frame, text=self.t("browse_btn"), width=135, height=32, command=self.select_save_directory)
        self.browse_btn.pack(side="left")

        self.path_display = ctk.CTkLabel(self.path_frame, text=self.save_directory, font=("Segoe UI", 11), text_color="#868e96", anchor="w")
        self.path_display.pack(side="left", padx=10, fill="x", expand=True)

        self.open_folder_btn = ctk.CTkButton(self.path_frame, text=self.t("open_folder"), width=100, height=32, fg_color="#343a40", hover_color="#495057", command=self.open_save_folder)
        self.open_folder_btn.pack(side="right")

        # 5. جدول قائمة الانتظار
        self.queue_label = ctk.CTkLabel(self, text=self.t("queue_label"), font=("Segoe UI", 11, "bold"))
        self.queue_label.pack(anchor="w", padx=25, pady=(4, 0))

        self.queue_box = ctk.CTkTextbox(self, height=85, width=860, font=("Consolas", 11))
        self.queue_box.pack(padx=20, pady=4)
        self.queue_box.configure(state="disabled")

        # 6. لوحة الإحصائيات (السرعة، الحجم، الوقت)
        self.stats_frame = ctk.CTkFrame(self, fg_color="#181a1f", corner_radius=8)
        self.stats_frame.pack(fill="x", padx=20, pady=6)

        self.speed_label = ctk.CTkLabel(self.stats_frame, text=self.t("speed"), font=("Segoe UI", 11, "bold"), text_color="#00FF7F")
        self.speed_label.pack(side="left", padx=20, pady=8)

        self.eta_label = ctk.CTkLabel(self.stats_frame, text=self.t("eta"), font=("Segoe UI", 11))
        self.eta_label.pack(side="left", padx=20, pady=8)

        self.size_label = ctk.CTkLabel(self.stats_frame, text=self.t("size"), font=("Segoe UI", 11))
        self.size_label.pack(side="right", padx=20, pady=8)

        # 7. شريط التقدم الفعلي والحالة
        self.status_label = ctk.CTkLabel(self, text=self.t("status_ready"), font=("Segoe UI", 11))
        self.status_label.pack(pady=(2, 3))

        self.progress_bar = ctk.CTkProgressBar(self, width=860, height=18)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=4)

        # 8. أزرار التحكم
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.pack(pady=12)

        self.start_btn = ctk.CTkButton(self.controls_frame, text=self.t("start_btn"), width=160, height=38, font=("Segoe UI", 13, "bold"), command=self.start_download)
        self.start_btn.pack(side="left", padx=10)

        self.cancel_btn = ctk.CTkButton(self.controls_frame, text=self.t("cancel_btn"), fg_color="#dc3545", hover_color="#c82333", width=160, height=38, font=("Segoe UI", 13, "bold"), state="disabled", command=self.cancel_download)
        self.cancel_btn.pack(side="left", padx=10)

    def show_ext_guide(self):
        ext_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome_extension")
        if os.path.exists(ext_folder):
            os.startfile(ext_folder)
        messagebox.showinfo(self.t("ext_guide_title"), self.t("ext_guide_body"))

    # --- تبديل الثيمات والمظهر واللغات ---
    def on_mode_change(self, mode_val):
        self.current_mode = mode_val
        ctk.set_appearance_mode(mode_val)

    def on_theme_change(self, theme_name):
        self.current_theme = theme_name
        self.apply_theme()

    def apply_theme(self):
        colors = COLOR_THEMES[self.current_theme]
        pri = colors["primary"]
        hov = colors["hover"]
        card = colors["card_bg"]

        self.analyze_btn.configure(fg_color=pri, hover_color=hov)
        self.start_btn.configure(fg_color=pri, hover_color=hov)
        self.add_queue_btn.configure(fg_color=pri, hover_color=hov)
        self.browse_btn.configure(fg_color=pri, hover_color=hov)
        self.media_frame.configure(fg_color=card)

    def on_lang_change(self, choice):
        self.current_lang = "ar" if "العربية" in choice else "en"
        self.refresh_language_texts()

    def refresh_language_texts(self):
        self.title(self.t("title"))
        self.lang_lbl.configure(text=self.t("lang_label"))
        self.theme_lbl.configure(text=self.t("theme_label"))
        self.mode_label.configure(text=self.t("mode_label"))
        self.ext_guide_btn.configure(text=self.t("ext_btn"))
        
        self.url_label.configure(text=self.t("url_label"))
        self.url_entry.configure(placeholder_text=self.t("url_placeholder"))
        self.analyze_btn.configure(text=self.t("analyze_btn"))
        self.add_queue_btn.configure(text=self.t("add_queue"))
        
        self.quality_label.configure(text=self.t("quality_label"))
        self.browse_btn.configure(text=self.t("browse_btn"))
        self.open_folder_btn.configure(text=self.t("open_folder"))
        self.queue_label.configure(text=self.t("queue_label"))
        
        self.start_btn.configure(text=self.t("start_btn"))
        self.cancel_btn.configure(text=self.t("cancel_btn"))

        if not self.is_downloading:
            self.status_label.configure(text=self.t("status_ready"))
            self.speed_label.configure(text=self.t("speed"))
            self.eta_label.configure(text=self.t("eta"))
            self.size_label.configure(text=self.t("size"))

    # --- استدعاء التنزيل من إضافة كروم الخارجية بدون إزعاج أو فتح النافذة ---
    def trigger_external_download(self, url, quality):
        def _action():
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, url)
            self.current_url = url
            
            if quality:
                self.is_video_mode = True
                def _fetch_and_start():
                    try:
                        ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            self.video_info = ydl.extract_info(url, download=False)
                    except Exception:
                        pass
                    self.safe_ui(lambda: (
                        self.quality_menu.configure(values=[quality]),
                        self.quality_menu.set(quality),
                        self.start_download()
                    ))
                threading.Thread(target=_fetch_and_start, daemon=True).start()
            else:
                self.start_analysis_thread()

        self.safe_ui(_action)

    # --- مراقبة الحافظة التلقائية ---
    def monitor_clipboard_loop(self):
        try:
            clip = self.clipboard_get().strip()
            if clip.startswith(("http://", "https://")) and clip != self.last_clipboard_text:
                self.last_clipboard_text = clip
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, clip)
                self.start_analysis_thread()
        except Exception:
            pass
        self.after(2000, self.monitor_clipboard_loop)

    def select_save_directory(self):
        d = filedialog.askdirectory(initialdir=self.save_directory)
        if d:
            self.save_directory = d
            self.path_display.configure(text=self.save_directory)

    def open_save_folder(self):
        if os.path.exists(self.save_directory):
            os.startfile(self.save_directory)

    def add_to_queue(self):
        url = self.url_entry.get().strip()
        if url and url not in self.download_queue:
            self.download_queue.append(url)
            self.update_queue_display()
            self.url_entry.delete(0, "end")
        else:
            messagebox.showwarning("!", self.t("msg_queue_dup"))

    def update_queue_display(self):
        self.queue_box.configure(state="normal")
        self.queue_box.delete("1.0", "end")
        for idx, item in enumerate(self.download_queue, 1):
            self.queue_box.insert("end", f"[{idx}] {item}\n")
        self.queue_box.configure(state="disabled")

    # --- فحص الرابط واستخراج دقات الفيديو وجودات الصوت ---
    def start_analysis_thread(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        
        self.current_url = url
        self.analyze_btn.configure(state="disabled", text=self.t("analyze_loading"))
        self.status_label.configure(text=self.t("status_analyzing"))
        threading.Thread(target=self.analyze_url, args=(url,), daemon=True).start()

    def analyze_url(self, url):
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
            if info:
                self.is_video_mode = True
                self.video_info = info
                title = info.get('title', 'Media')
                
                resolutions = set()
                formats = info.get('formats', [])
                for f in formats:
                    h = f.get('height')
                    if h and f.get('vcodec') != 'none':
                        resolutions.add(h)
                
                sorted_res = sorted(list(resolutions), reverse=True)
                
                menu_options = [self.t("best_video")]
                for r in sorted_res:
                    if r >= 2160:
                        menu_options.append(f"🎬 Video - {r}p (4K Ultra HD)")
                    elif r >= 1440:
                        menu_options.append(f"🎬 Video - {r}p (2K QHD)")
                    elif r >= 1080:
                        menu_options.append(f"🎬 Video - {r}p (Full HD)")
                    elif r >= 720:
                        menu_options.append(f"🎬 Video - {r}p (HD)")
                    else:
                        menu_options.append(f"🎬 Video - {r}p (SD)")

                # جودات الصوت المفصلة
                menu_options.append("🎵 Audio MP3 - 320 kbps (أعلى جودة صوت / Studio)")
                menu_options.append("🎵 Audio MP3 - 256 kbps (جودة فائقة / Very High)")
                menu_options.append("🎵 Audio MP3 - 192 kbps (جودة ممتازة / High Quality)")
                menu_options.append("🎵 Audio MP3 - 128 kbps (جودة قياسية / Standard)")
                menu_options.append("🎵 Audio M4A - الأصلي (Original Audio Track)")
                menu_options.append("🎵 Audio WAV - غير مضغوط (Lossless WAV)")
                
                self.safe_ui(self.video_title_label.configure, text=f"{self.t('title_prefix')}{title}")
                self.safe_ui(self.quality_menu.configure, values=menu_options)
                self.safe_ui(self.quality_menu.set, menu_options[1] if len(menu_options) > 1 else menu_options[0])
                self.safe_ui(self.type_badge.configure, text=self.t("type_video"), text_color="#00FF7F")
                self.safe_ui(self.status_label.configure, text=self.t("status_analyzed_ok"))
                self.safe_ui(self.analyze_btn.configure, state="normal", text=self.t("analyze_btn"))
                return

        except Exception:
            pass
        
        # فحص كملف تحميل عادي مباشر
        try:
            self.is_video_mode = False
            self.video_info = None
            head_res = requests.head(url, headers=self.headers, allow_redirects=True, timeout=8)
            filename = self.extract_filename(url, head_res.headers)
            size_mb = int(head_res.headers.get('content-length', 0)) / (1024 * 1024)
            size_text = f" ({size_mb:.1f} MB)" if size_mb > 0 else ""
            
            self.safe_ui(self.video_title_label.configure, text=f"{self.t('file_prefix')}{filename}{size_text}")
            self.safe_ui(self.quality_menu.configure, values=[self.t("direct_download_opt")])
            self.safe_ui(self.quality_menu.set, self.t("direct_download_opt"))
            self.safe_ui(self.type_badge.configure, text=self.t("type_direct"), text_color="#17a2b8")
            self.safe_ui(self.status_label.configure, text=self.t("status_direct_ready"))
        except Exception:
            self.safe_ui(self.status_label.configure, text=self.t("status_analyze_fail"))
        finally:
            self.safe_ui(self.analyze_btn.configure, state="normal", text=self.t("analyze_btn"))

    def extract_filename(self, url, headers=None):
        if headers and 'content-disposition' in headers:
            cd = headers['content-disposition']
            matches = re.findall(r'filename\*?=(?:UTF-8\'\')?([^;\\r\\n]+)', cd, re.IGNORECASE)
            if matches:
                name = urllib.parse.unquote(matches[0].strip(' "\''))
                return self.sanitize_name(name)
        
        parsed = urllib.parse.urlparse(url)
        name = os.path.basename(parsed.path)
        if name and '.' in name:
            return self.sanitize_name(name)
        return "downloaded_file.bin"

    def sanitize_name(self, name):
        return re.sub(r'[<>:"/\\|?*]', '_', name).strip()

    # --- بدء عملية التنزيل ---
    def start_download(self):
        url_input = self.url_entry.get().strip()
        
        if not self.current_url:
            if url_input:
                self.current_url = url_input
            elif self.download_queue:
                self.current_url = self.download_queue.pop(0)
                self.update_queue_display()
            else:
                messagebox.showwarning("!", self.t("msg_empty_url"))
                return

        self.is_downloading = True
        self.cancel_flag = False
        self.progress_bar.set(0)
        
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.analyze_btn.configure(state="disabled")

        if self.is_video_mode:
            threading.Thread(target=self.execute_video_audio_download, daemon=True).start()
        else:
            threading.Thread(target=self.execute_direct_download, daemon=True).start()

    # --- محرك التنزيل الذكي للفيديو والصوت (yt-dlp + ffmpeg) ---
    def execute_video_audio_download(self):
        try:
            selected = self.quality_menu.get()
            title = self.video_info.get('title', 'media') if self.video_info else 'media'
            safe_title = self.sanitize_name(title)
            
            out_template = os.path.join(self.save_directory, f"{safe_title}.%(ext)s")
            postprocessors = []

            if "Audio" in selected or "صوت" in selected:
                ydl_format = 'bestaudio/best'
                if "WAV" in selected:
                    postprocessors = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav'}]
                elif "M4A" in selected:
                    postprocessors = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'm4a'}]
                else:
                    bitrate = "192"
                    if "320" in selected: bitrate = "320"
                    elif "256" in selected: bitrate = "256"
                    elif "128" in selected: bitrate = "128"
                    
                    postprocessors = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': bitrate,
                    }]
                self.safe_ui(self.status_label.configure, text=self.t("status_audio_extract"))
            
            elif "p" in selected:
                res_match = re.search(r'(\d+)p', selected)
                height = res_match.group(1) if res_match else "1080"
                ydl_format = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
            else:
                ydl_format = "bestvideo+bestaudio/best"

            def ytdl_hook(d):
                if self.cancel_flag:
                    raise Exception("Cancelled by user")

                if d['status'] == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    speed = d.get('speed', 0) or 0
                    eta = d.get('eta', 0) or 0

                    if total > 0:
                        prog = downloaded / total
                        self.safe_ui(self.progress_bar.set, prog)
                        down_mb = downloaded / (1024 * 1024)
                        tot_mb = total / (1024 * 1024)
                        self.safe_ui(self.size_label.configure, text=f"{self.t('size_prefix')}{down_mb:.1f} MB / {tot_mb:.1f} MB")
                        self.safe_ui(self.status_label.configure, text=f"{self.t('status_downloading')}{int(prog*100)}%")

                    speed_mb = speed / (1024 * 1024)
                    self.safe_ui(self.speed_label.configure, text=f"{self.t('speed_prefix')}{speed_mb:.2f} MB/s")

                    if eta > 0:
                        self.safe_ui(self.eta_label.configure, text=f"{self.t('eta_prefix')}{time.strftime('%M:%S', time.gmtime(eta))}")
                        
                elif d['status'] == 'finished':
                    self.safe_ui(self.status_label.configure, text=self.t("status_merging"))

            ydl_opts = {
                'format': ydl_format,
                'outtmpl': out_template,
                'merge_output_format': 'mp4',
                'progress_hooks': [ytdl_hook],
                'quiet': True,
                'no_warnings': True,
            }
            if postprocessors:
                ydl_opts['postprocessors'] = postprocessors

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.current_url])

            self.safe_ui(self.progress_bar.set, 1.0)
            self.safe_ui(self.status_label.configure, text=self.t("status_done"))
            self.safe_ui(messagebox.showinfo, self.t("msg_success_title"), self.t("msg_success_body"))
            self.finish_download_cycle()

        except Exception as e:
            if not self.cancel_flag:
                self.safe_ui(messagebox.showerror, self.t("msg_error_title"), f"{self.t('msg_error_body')}{str(e)}")
            self.safe_ui(self.reset_ui_after_finish, self.t("status_failed"))

    # --- محرك التنزيل للملفات العادية ---
    def execute_direct_download(self):
        try:
            head_res = requests.head(self.current_url, headers=self.headers, allow_redirects=True, timeout=10)
            filename = self.extract_filename(self.current_url, head_res.headers)
            save_path = os.path.join(self.save_directory, filename)
            
            total_size = int(head_res.headers.get('content-length', 0))
            accept_ranges = head_res.headers.get('accept-ranges', '').lower()

            temp_files = [f"{save_path}.part{i}" for i in range(self.num_threads)]
            self.downloaded_bytes = 0

            threading.Thread(target=self.monitor_direct_stats, args=(total_size,), daemon=True).start()

            if total_size > 0 and 'bytes' in accept_ranges:
                chunk_size = math.ceil(total_size / self.num_threads)
                tasks = []
                with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
                    for i in range(self.num_threads):
                        s = i * chunk_size
                        e = min((i + 1) * chunk_size - 1, total_size - 1)
                        tasks.append(executor.submit(self.download_chunk, self.current_url, s, e, i, temp_files))
                    for t in tasks:
                        t.result()
            else:
                self.download_single_stream(self.current_url, save_path)

            if self.cancel_flag:
                for tf in temp_files:
                    if os.path.exists(tf): os.remove(tf)
                self.safe_ui(self.reset_ui_after_finish, self.t("status_cancelled"))
                return

            with open(save_path, 'wb') as final_file:
                for tf in temp_files:
                    if os.path.exists(tf):
                        with open(tf, 'rb') as f:
                            shutil.copyfileobj(f, final_file, length=1024*1024*4)
                        os.remove(tf)

            self.safe_ui(self.progress_bar.set, 1.0)
            self.safe_ui(messagebox.showinfo, self.t("msg_success_title"), f"{self.t('msg_success_body')} ({filename})")
            self.finish_download_cycle()

        except Exception as e:
            if not self.cancel_flag:
                self.safe_ui(messagebox.showerror, self.t("msg_error_title"), f"{self.t('msg_error_body')}{str(e)}")
            self.safe_ui(self.reset_ui_after_finish, self.t("status_failed"))

    def download_chunk(self, url, start, end, idx, temp_files):
        tf = temp_files[idx]
        headers = self.headers.copy()
        headers['Range'] = f'bytes={start}-{end}'
        with requests.get(url, headers=headers, stream=True, timeout=20) as r:
            with open(tf, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*64):
                    if self.cancel_flag: break
                    if chunk:
                        f.write(chunk)
                        with self.lock:
                            self.downloaded_bytes += len(chunk)

    def download_single_stream(self, url, save_path):
        with requests.get(url, headers=self.headers, stream=True, timeout=20) as r:
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*64):
                    if self.cancel_flag: break
                    if chunk:
                        f.write(chunk)
                        with self.lock:
                            self.downloaded_bytes += len(chunk)

    def monitor_direct_stats(self, total_size):
        last_bytes = 0
        while self.is_downloading and not self.cancel_flag:
            time.sleep(1)
            bytes_sec = max(0, self.downloaded_bytes - last_bytes)
            last_bytes = self.downloaded_bytes

            spd = bytes_sec / (1024 * 1024)
            self.safe_ui(self.speed_label.configure, text=f"{self.t('speed_prefix')}{spd:.2f} MB/s")

            if total_size > 0:
                prog = min(1.0, max(0.0, self.downloaded_bytes / total_size))
                self.safe_ui(self.progress_bar.set, prog)
                self.safe_ui(self.size_label.configure, text=f"{self.t('size_prefix')}{self.downloaded_bytes/(1024*1024):.1f} MB / {total_size/(1024*1024):.1f} MB")
                self.safe_ui(self.status_label.configure, text=f"{self.t('status_downloading')}{int(prog*100)}%")
                if bytes_sec > 0:
                    eta = int((total_size - self.downloaded_bytes) / bytes_sec)
                    self.safe_ui(self.eta_label.configure, text=f"{self.t('eta_prefix')}{time.strftime('%M:%S', time.gmtime(eta))}")

    def finish_download_cycle(self):
        if self.download_queue:
            self.current_url = self.download_queue.pop(0)
            self.safe_ui(self.update_queue_display)
            self.safe_ui(self.start_analysis_thread)
            self.start_download()
        else:
            self.safe_ui(self.reset_ui_after_finish, self.t("status_done"))

    def cancel_download(self):
        self.cancel_flag = True
        self.is_downloading = False
        self.reset_ui_after_finish(self.t("status_cancelled"))

    def reset_ui_after_finish(self, status_text):
        self.is_downloading = False
        self.current_url = ""
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.analyze_btn.configure(state="normal", text=self.t("analyze_btn"))
        self.status_label.configure(text=status_text)

if __name__ == "__main__":
    app = UltimateIDMPro()
    app.mainloop()
