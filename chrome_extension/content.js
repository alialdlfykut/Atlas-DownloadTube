// Atlas DownloadTube - Content Script (V6.5 Precision & Red Edition)
(function () {
  let activeDropdown = null;
  let activeCard = null;
  let progressInterval = null;
  let activeVideo = null;
  let hasCustomPosition = false;

  // قائمة الفيديوهات والروابط التي تم إغلاق الزر عنها مؤقتاً (تُعاد تلقائياً عند F5)
  const dismissedVideos = new WeakSet();
  const dismissedUrls = new Set();

  const LOGO_URL = chrome.runtime.getURL("icon48.png");

  // التحقق إن كان الفيديو قد تم إغلاقه بعلامة [x]
  function isVideoDismissed(video) {
    if (!video) return false;
    if (video.dataset && video.dataset.atlasDismissed === "true") return true;
    if (dismissedVideos.has(video)) return true;

    const parent = video.closest("div[role='article'], div[data-pagelet*='FeedUnit'], #movie_player, .html5-video-player");
    if (parent && parent.dataset && parent.dataset.atlasDismissed === "true") return true;

    if (window.location.hostname.includes("youtube.com") && dismissedUrls.has(window.location.href)) return true;

    const vUrl = getActualVideoUrl(video);
    if (vUrl && dismissedUrls.has(vUrl)) return true;

    return false;
  }

  // تنظيف اسم الملف ليكون مناسباً للحفظ في ويندوز
  function sanitizeFilename(name, ext = "mp4") {
    let clean = (name || "video")
      .replace(/[\\/:*?"<>|]/g, "_")
      .replace(/\s+/g, " ")
      .trim();
    if (clean.length > 80) clean = clean.substring(0, 80);
    return `${clean}.${ext}`;
  }

  // استخراج عنوان منشور فيسبوك الحقيقي الدقيق من محتوى المنشور
  function extractFacebookPostTitle(videoElement) {
    if (window.location.pathname.includes("/reel/")) {
      const reelDesc = document.querySelector("div[role='main'] div[dir='auto']");
      if (reelDesc && reelDesc.textContent.trim()) {
        const line = reelDesc.textContent.trim().split("\n")[0].trim();
        if (line.length > 2) return line.substring(0, 80);
      }
    }

    if (window.location.pathname.includes("/watch")) {
      const h1 = document.querySelector("h1, div[role='main'] h2");
      if (h1 && h1.textContent.trim()) {
        const line = h1.textContent.trim().split("\n")[0].trim();
        if (line.length > 2) return line.substring(0, 80);
      }
    }

    let container = videoElement.closest("div[role='article'], div[data-pagelet*='FeedUnit'], div[role='feed'] > div");
    if (!container) {
      let cur = videoElement.parentElement;
      for (let i = 0; i < 12 && cur && cur !== document.body; i++) {
        if (cur.querySelector("div[dir='auto'], a[href*='/watch/'], a[href*='/reel/']")) {
          container = cur;
          break;
        }
        cur = cur.parentElement;
      }
    }

    if (container) {
      const msg = container.querySelector("[data-ad-preview='message'], [data-ad-comet-preview='message']");
      if (msg && msg.textContent.trim()) {
        const line = msg.textContent.trim().split("\n")[0].trim();
        if (line.length > 3) return line.substring(0, 80);
      }

      const autoDivs = container.querySelectorAll("div[dir='auto'], span[dir='auto']");
      for (const d of autoDivs) {
        const txt = d.textContent.trim();
        if (
          txt.length > 6 &&
          !txt.includes("متابعة") &&
          !txt.includes("Like") &&
          !txt.includes("Share") &&
          !txt.includes("أعجبني") &&
          !txt.includes("تعليق") &&
          !txt.includes("مشاركة")
        ) {
          return txt.split("\n")[0].trim().substring(0, 80);
        }
      }

      const author = container.querySelector("h2 strong, h3 strong, h4 strong, a strong");
      if (author && author.textContent.trim()) {
        return `فيديو ${author.textContent.trim()}`;
      }
    }

    const docTitle = document.title
      .replace(/\s*\|\s*Facebook/gi, "")
      .replace(/\s*-\s*Facebook/gi, "")
      .replace(/\(\d+\)/g, "")
      .trim();
    if (docTitle && !docTitle.toLowerCase().includes("facebook") && docTitle.length > 3) {
      return docTitle.split("\n")[0].trim().substring(0, 80);
    }

    return "فيديو فيسبوك";
  }

  // استخراج الرابط الفعلي لصفحة الفيديو
  function getActualVideoUrl(videoElement) {
    const host = window.location.hostname;

    if (host.includes("facebook.com")) {
      if (
        window.location.pathname.includes("/watch") ||
        window.location.pathname.includes("/reel/") ||
        window.location.pathname.includes("/videos/")
      ) {
        return window.location.href.split("?")[0];
      }

      let container = videoElement.closest("div[role='article'], div[data-pagelet*='FeedUnit'], div[role='feed'] > div");
      if (!container) {
        let cur = videoElement.parentElement;
        for (let i = 0; i < 12 && cur && cur !== document.body; i++) {
          if (cur.querySelector("a[href*='/watch/'], a[href*='/reel/'], a[href*='/videos/'], a[href*='/posts/']")) {
            container = cur;
            break;
          }
          cur = cur.parentElement;
        }
      }

      if (container) {
        const link = container.querySelector(
          "a[href*='/watch/'], a[href*='/reel/'], a[href*='/videos/'], a[href*='/posts/'], a[href*='fb.watch']"
        );
        if (link && link.href) {
          return link.href.split("?")[0];
        }

        const timeLink = container.querySelector("a[href*='/permalink/'], a[href*='fbid=']");
        if (timeLink && timeLink.href) return timeLink.href.split("&")[0];
      }

      if (videoElement.src && videoElement.src.includes("fbcdn.net")) {
        return videoElement.src;
      }
    }

    if (host.includes("youtube.com")) {
      if (window.location.pathname === "/watch") {
        const v = new URLSearchParams(window.location.search).get("v");
        if (v) return `https://www.youtube.com/watch?v=${v}`;
      }
      if (window.location.pathname.startsWith("/shorts/")) {
        const parts = window.location.pathname.split("/");
        return `https://www.youtube.com/shorts/${parts[2] || ""}`;
      }
      let item = videoElement.closest("ytd-rich-item-renderer, ytd-video-renderer, ytd-grid-video-renderer, ytd-compact-video-renderer");
      if (item) {
        const a = item.querySelector("a#thumbnail, a#video-title-link, a[href*='/watch?v=']");
        if (a && a.href) {
          const v = new URLSearchParams(a.search).get("v");
          if (v) return `https://www.youtube.com/watch?v=${v}`;
          return a.href.split("&list=")[0];
        }
      }
    }

    if (videoElement.src && !videoElement.src.startsWith("blob:") && !videoElement.src.startsWith("data:")) {
      return videoElement.src;
    }
    if (videoElement.currentSrc && !videoElement.currentSrc.startsWith("blob:")) {
      return videoElement.currentSrc;
    }

    return window.location.href;
  }

  // إخفاء الزر عن الفيديو الحالي (عند الضغط على علامة ×)
  function dismissCurrentVideo() {
    if (activeVideo) {
      try {
        dismissedVideos.add(activeVideo);
      } catch (e) {}

      if (activeVideo.dataset) {
        activeVideo.dataset.atlasDismissed = "true";
      }

      const parent = activeVideo.closest("div[role='article'], div[data-pagelet*='FeedUnit'], #movie_player, .html5-video-player");
      if (parent && parent.dataset) {
        parent.dataset.atlasDismissed = "true";
      }

      const vUrl = getActualVideoUrl(activeVideo);
      if (vUrl) dismissedUrls.add(vUrl);
    }

    if (window.location.hostname.includes("youtube.com")) {
      dismissedUrls.add(window.location.href);
    }

    // إخفاء الزر نهائياً وفورياً عن هذا الفيديو
    if (mainButton) {
      mainButton.classList.add("atlas-hidden");
      mainButton.style.setProperty("display", "none", "important");
    }

    if (activeDropdown) {
      activeDropdown.remove();
      activeDropdown = null;
    }
  }

  // إنشاء الزر الرئيسي الموحد لـ Atlas DownloadTube
  let mainButton = null;

  function getOrCreateButton() {
    if (mainButton && document.body.contains(mainButton)) {
      return mainButton;
    }

    const btn = document.createElement("div");
    btn.className = "atlas-video-btn atlas-hidden";
    btn.id = "atlas-video-btn";
    btn.innerHTML = `
      <span class="atlas-btn-text">تحميل الفيديو</span>
      <span class="atlas-btn-close" id="atlas-btn-close" title="إخفاء من هذا الفيديو">&times;</span>
    `;
    btn.title = "اضغط للتحميل، أو اسحبه بالماوس لأي مكان في الصفحة";
    btn.style.setProperty("display", "none", "important");

    document.body.appendChild(btn);
    mainButton = btn;

    // ربط النقر المباشر على علامة [x]
    const closeBtn = btn.querySelector("#atlas-btn-close");
    if (closeBtn) {
      closeBtn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        dismissCurrentVideo();
      });
      closeBtn.addEventListener("mousedown", (e) => {
        e.stopPropagation();
      });
      closeBtn.addEventListener("mouseup", (e) => {
        e.stopPropagation();
      });
    }

    setupButtonDragging(btn);
    return btn;
  }

  // إعداد سحب الزر بحرية في كامل الصفحة وحفظ موقعه
  function setupButtonDragging(btn) {
    let isDragging = false;
    let startX = 0, startY = 0;
    let initialLeft = 0, initialTop = 0;
    let hasMoved = false;

    // استعادة الموقع المحفوظ سابقاً
    try {
      const saved = localStorage.getItem("atlas_btn_pos") || localStorage.getItem("idm_btn_pos");
      if (saved) {
        const pos = JSON.parse(saved);
        if (pos.left !== undefined && pos.top !== undefined) {
          const maxL = Math.max(0, window.innerWidth - 170);
          const maxT = Math.max(0, window.innerHeight - 45);
          btn.style.left = `${Math.min(pos.left, maxL)}px`;
          btn.style.top = `${Math.min(pos.top, maxT)}px`;
          btn.style.right = "auto";
          btn.style.bottom = "auto";
          hasCustomPosition = true;
        }
      }
    } catch (e) {}

    const onMouseMove = (e) => {
      if (!isDragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;

      if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
        hasMoved = true;
        e.preventDefault();
      }

      let newLeft = initialLeft + dx;
      let newTop = initialTop + dy;

      // حرية الحركة في كامل حدود نافذة المتصفح (من أقصى اليمين لأقصى اليسار)
      const maxLeft = Math.max(0, window.innerWidth - btn.offsetWidth);
      const maxTop = Math.max(0, window.innerHeight - btn.offsetHeight);

      newLeft = Math.max(0, Math.min(newLeft, maxLeft));
      newTop = Math.max(0, Math.min(newTop, maxTop));

      btn.style.left = `${newLeft}px`;
      btn.style.top = `${newTop}px`;
      btn.style.right = "auto";
      btn.style.bottom = "auto";
    };

    const onMouseUp = () => {
      if (!isDragging) return;
      isDragging = false;
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);

      btn.style.cursor = "grab";
      btn.style.transition = "transform 0.2s ease, box-shadow 0.2s ease";

      if (hasMoved) {
        hasCustomPosition = true;
        const pos = {
          left: parseInt(btn.style.left, 10),
          top: parseInt(btn.style.top, 10),
        };
        try {
          localStorage.setItem("atlas_btn_pos", JSON.stringify(pos));
        } catch (e) {}
      }
    };

    btn.addEventListener("mousedown", (e) => {
      if (e.target.closest("#atlas-btn-close")) return;
      if (e.button !== 0) return;

      isDragging = true;
      hasMoved = false;
      startX = e.clientX;
      startY = e.clientY;

      const rect = btn.getBoundingClientRect();
      initialLeft = rect.left;
      initialTop = rect.top;

      btn.style.cursor = "grabbing";
      btn.style.transition = "none";
      e.stopPropagation();

      document.addEventListener("mousemove", onMouseMove, { passive: false });
      document.addEventListener("mouseup", onMouseUp);
    });

    btn.addEventListener(
      "click",
      (e) => {
        if (e.target.closest("#atlas-btn-close")) {
          e.preventDefault();
          e.stopPropagation();
          dismissCurrentVideo();
          return;
        }

        if (hasMoved) {
          e.preventDefault();
          e.stopPropagation();
          hasMoved = false;
          return;
        }

        e.preventDefault();
        e.stopPropagation();
        if (activeVideo && !isVideoDismissed(activeVideo)) {
          const videoUrl = getActualVideoUrl(activeVideo);
          openQualityMenu(btn, videoUrl, activeVideo);
        }
      },
      true
    );
  }

  // تحديث موضع الزر إذا لم يكن المستخدم قد حدد موضعاً مخصصاً بنفسه
  function updateDefaultButtonPosition(video) {
    if (hasCustomPosition || !mainButton) return;
    const rect = video.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;

    const top = Math.max(10, Math.min(rect.top + 14, window.innerHeight - 50));
    const left = Math.max(10, Math.min(rect.left + 14, window.innerWidth - 180));
    mainButton.style.left = `${left}px`;
    mainButton.style.top = `${top}px`;
    mainButton.style.right = "auto";
    mainButton.style.bottom = "auto";
  }

  // تعيين الفيديو النشط وعرض الزر له
  function setActiveVideo(video) {
    if (!video || !document.body.contains(video)) return;
    activeVideo = video;

    const btn = getOrCreateButton();

    if (isVideoDismissed(video)) {
      btn.classList.add("atlas-hidden");
      btn.style.setProperty("display", "none", "important");
      return;
    }

    btn.classList.remove("atlas-hidden");
    btn.style.setProperty("display", "flex", "important");
    updateDefaultButtonPosition(video);
  }

  // فتح قائمة اختيار الجودات المستخرجة
  function openQualityMenu(btn, videoUrl, videoElement) {
    if (activeDropdown) {
      activeDropdown.remove();
      activeDropdown = null;
    }

    const dropdown = document.createElement("div");
    dropdown.className = "atlas-quality-dropdown";

    const rect = btn.getBoundingClientRect();
    let dropTop = rect.bottom + 8;
    if (dropTop + 380 > window.innerHeight) {
      dropTop = Math.max(10, rect.top - 390);
    }
    dropdown.style.top = `${dropTop}px`;

    let dropLeft = rect.left;
    if (dropLeft + 340 > window.innerWidth) {
      dropLeft = Math.max(10, window.innerWidth - 350);
    }
    dropdown.style.left = `${dropLeft}px`;
    dropdown.style.right = "auto";

    let displayTitle = document.title;
    if (window.location.hostname.includes("facebook.com")) {
      displayTitle = extractFacebookPostTitle(videoElement);
    } else if (window.location.hostname.includes("youtube.com")) {
      displayTitle = document.title.replace(" - YouTube", "").trim();
    }

    dropdown.innerHTML = `
      <div class="atlas-dropdown-header">
        <span class="atlas-dropdown-title">⚡ Atlas DownloadTube</span>
        <button class="atlas-close-btn" id="atlas-menu-close-btn">&times;</button>
      </div>
      <div class="atlas-loading-spinner" id="atlas-menu-spinner">جاري استخراج دقات الفيديو وجودات الصوت... ⏳</div>
    `;

    document.body.appendChild(dropdown);
    activeDropdown = dropdown;

    dropdown.querySelector("#atlas-menu-close-btn").addEventListener("click", () => {
      dropdown.remove();
      activeDropdown = null;
    });

    chrome.runtime.sendMessage(
      {
        action: "analyze",
        url: videoUrl,
        title: displayTitle,
      },
      (data) => {
        if (!data || data.status !== "success") {
          dropdown.innerHTML = `
            <div class="atlas-dropdown-header">
              <span class="atlas-dropdown-title" title="${displayTitle}">🎬 ${displayTitle}</span>
              <button class="atlas-close-btn" id="atlas-menu-close-btn3">&times;</button>
            </div>
            <div class="atlas-section-label">🎬 دقات الفيديو المتاحة:</div>
            <div class="atlas-opt-item atlas-v-opt" data-q="best">
              <span>🎬 Video - 1080p (Full HD)</span>
              <span class="atlas-opt-badge">MP4</span>
            </div>
            <div class="atlas-opt-item atlas-v-opt" data-q="720p">
              <span>🎬 Video - 720p (HD)</span>
              <span class="atlas-opt-badge">MP4</span>
            </div>
            <div class="atlas-opt-item atlas-v-opt" data-q="480p">
              <span>🎬 Video - 480p (SD)</span>
              <span class="atlas-opt-badge">MP4</span>
            </div>
            <div class="atlas-section-label">🎵 جودات الصوت (Audio Only):</div>
            <div class="atlas-opt-item atlas-a-opt" data-q="320">
              <span>🎵 Audio MP3 - 320 kbps (أعلى جودة Studio)</span>
              <span class="atlas-opt-badge" style="background:rgba(226, 76, 65, 0.25); color:#e24c41;">MP3</span>
            </div>
            <div class="atlas-opt-item atlas-a-opt" data-q="192">
              <span>🎵 Audio MP3 - 192 kbps (قياسية)</span>
              <span class="atlas-opt-badge" style="background:rgba(226, 76, 65, 0.25); color:#e24c41;">MP3</span>
            </div>
          `;
          dropdown.querySelector("#atlas-menu-close-btn3").addEventListener("click", () => {
            dropdown.remove();
            activeDropdown = null;
          });
          dropdown.querySelectorAll(".atlas-v-opt, .atlas-a-opt").forEach((el) => {
            el.addEventListener("click", () => {
              const q = el.getAttribute("data-q");
              startAtlasDownload(videoUrl, q, displayTitle);
              dropdown.remove();
              activeDropdown = null;
            });
          });
          return;
        }

        const finalTitle = data.title || displayTitle;
        renderMenuOptions(dropdown, finalTitle, data.video_options || [], data.audio_options || [], videoUrl);
      }
    );
  }

  // عرض خيارات الجودات المستخرجة
  function renderMenuOptions(dropdown, title, videoOpts, audioOpts, videoUrl) {
    let html = `
      <div class="atlas-dropdown-header">
        <span class="atlas-dropdown-title" title="${title}">🎬 ${title}</span>
        <button class="atlas-close-btn" id="atlas-menu-close-btn2">&times;</button>
      </div>
    `;

    if (videoOpts.length > 0) {
      html += `<div class="atlas-section-label">🎬 دقات الفيديو المتاحة:</div>`;
      videoOpts.forEach((opt) => {
        html += `
          <div class="atlas-opt-item atlas-v-opt" data-q="${opt}">
            <span>${opt}</span>
            <span class="atlas-opt-badge">MP4</span>
          </div>
        `;
      });
    }

    if (audioOpts.length > 0) {
      html += `<div class="atlas-section-label">🎵 جودات الصوت (Audio Only):</div>`;
      audioOpts.forEach((opt) => {
        html += `
          <div class="atlas-opt-item atlas-a-opt" data-q="${opt}">
            <span>${opt}</span>
            <span class="atlas-opt-badge" style="background:rgba(226, 76, 65, 0.25); color:#e24c41;">MP3</span>
          </div>
        `;
      });
    }

    dropdown.innerHTML = html;

    dropdown.querySelector("#atlas-menu-close-btn2").addEventListener("click", () => {
      dropdown.remove();
      activeDropdown = null;
    });

    dropdown.querySelectorAll(".atlas-v-opt").forEach((el) => {
      el.addEventListener("click", () => {
        const q = el.getAttribute("data-q");
        startAtlasDownload(videoUrl, q, title);
        dropdown.remove();
        activeDropdown = null;
      });
    });

    dropdown.querySelectorAll(".atlas-a-opt").forEach((el) => {
      el.addEventListener("click", () => {
        const q = el.getAttribute("data-q");
        startAtlasDownload(videoUrl, q, title);
        dropdown.remove();
        activeDropdown = null;
      });
    });
  }

  // بدء التحميل المباشر وتنزيل الملف تلقائياً في مجلد Downloads بدون طلب مكان الحفظ مرة ثانية
  function startAtlasDownload(url, quality, title) {
    if (activeCard) activeCard.remove();
    if (progressInterval) clearInterval(progressInterval);

    const card = document.createElement("div");
    card.className = "atlas-active-card";
    card.innerHTML = `
      <button class="atlas-card-close" id="atlas-card-close-btn" title="إغلاق">&times;</button>
      <div class="atlas-card-title">⚡ جاري التحميل: ${title}</div>
      <div class="atlas-progress-row">
        <div class="atlas-progress-container">
          <div class="atlas-progress-bar" id="atlas-prog-bar" style="width: 0%;"></div>
        </div>
        <span class="atlas-progress-pct" id="atlas-prog-pct">0%</span>
      </div>
      <div class="atlas-card-stats">
        <span id="atlas-card-status">جاري الاتصال وسحب التدفق...</span>
        <span id="atlas-card-speed">0.00 MB/s</span>
      </div>
      <div class="atlas-card-stats">
        <span id="atlas-card-size">0 MB</span>
        <span id="atlas-card-eta">الوقت: --:--</span>
      </div>
    `;

    document.body.appendChild(card);
    activeCard = card;

    card.querySelector("#atlas-card-close-btn").addEventListener("click", () => {
      if (progressInterval) clearInterval(progressInterval);
      card.remove();
      activeCard = null;
    });

    chrome.runtime.sendMessage(
      {
        action: "download",
        url: url,
        quality: quality,
        title: title,
      },
      () => {
        const progBar = card.querySelector("#atlas-prog-bar");
        const pctBadge = card.querySelector("#atlas-prog-pct");
        const statusLbl = card.querySelector("#atlas-card-status");
        const speedLbl = card.querySelector("#atlas-card-speed");
        const sizeLbl = card.querySelector("#atlas-card-size");
        const etaLbl = card.querySelector("#atlas-card-eta");

        progressInterval = setInterval(() => {
          chrome.runtime.sendMessage({ action: "get_status" }, (status) => {
            if (!status) return;

            if (status.is_downloading) {
              const currentPct = (typeof status.percent === "number") ? status.percent : Math.round((status.progress || 0) * 100);
              const displayPct = Math.max(0, Math.min(99, currentPct));
              if (progBar) progBar.style.setProperty("width", `${Math.max(3, displayPct)}%`, "important");
              if (pctBadge) pctBadge.textContent = `${displayPct}%`;
              statusLbl.textContent = status.status_text || "جاري التحميل...";
              speedLbl.textContent = status.speed || "0.00 MB/s";
              sizeLbl.textContent = status.size || "0 MB";
              etaLbl.textContent = `متبقي: ${status.eta || "--:--"}`;
            } else if (status.progress >= 1.0) {
              clearInterval(progressInterval);
              if (progBar) {
                progBar.style.setProperty("width", "100%", "important");
                progBar.style.setProperty("background", "#00d26a", "important");
              }
              if (pctBadge) {
                pctBadge.textContent = "100%";
                pctBadge.style.setProperty("background", "#00d26a", "important");
              }

              const ext = quality.includes("Audio") || quality.includes("MP3") || quality.includes("صوت") ? "mp3" : "mp4";
              const finishedFilename = status.last_finished_file || sanitizeFilename(title, ext);

              card.innerHTML = `
                <button class="atlas-card-close" id="atlas-card-close-btn" title="إغلاق">&times;</button>
                <div class="atlas-card-title" style="color:#00d26a;">✅ اكتمل التحميل بنجاح!</div>
                <div style="font-size:11px; color:#cbd5e0; margin-bottom:4px;">
                  تم حفظ الملف تلقائياً في مجلد التنزيلات (Downloads):
                </div>
                <div style="font-size:11px; color:#00d26a; font-weight:bold; margin-bottom:8px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
                  📁 ${finishedFilename}
                </div>
              `;

              let autoCloseTimer = setTimeout(() => {
                if (card && card.parentNode) {
                  card.style.transition = "opacity 0.5s ease";
                  card.style.opacity = "0";
                  setTimeout(() => {
                    if (card && card.parentNode) {
                      card.remove();
                    }
                    if (activeCard === card) {
                      activeCard = null;
                    }
                  }, 500);
                }
              }, 10000);

              const closeCardBtn = card.querySelector("#atlas-card-close-btn");
              if (closeCardBtn) {
                closeCardBtn.addEventListener("click", () => {
                  clearTimeout(autoCloseTimer);
                  card.remove();
                  activeCard = null;
                });
              }
            } else if (status.error) {
              clearInterval(progressInterval);
              statusLbl.textContent = `خطأ: ${status.error}`;
              progBar.style.background = "#ff4d4f";
            }
          });
        }, 500);
      }
    );
  }

  // فحص الفيديوهات في الصفحة وربط الأحداث بها
  function scanForVideos() {
    const videos = document.querySelectorAll("video");
    if (!videos || videos.length === 0) return;

    let bestVideo = null;

    videos.forEach((video) => {
      if (video.offsetWidth < 120 && video.offsetHeight < 80) return;

      if (!video.dataset.atlasTracked) {
        video.dataset.atlasTracked = "true";

        video.addEventListener("mouseenter", () => {
          if (!isVideoDismissed(video)) {
            setActiveVideo(video);
          }
        });
        video.addEventListener("play", () => {
          if (!isVideoDismissed(video)) {
            setActiveVideo(video);
          }
        });
        video.addEventListener("playing", () => {
          if (!isVideoDismissed(video)) {
            setActiveVideo(video);
          }
        });
        video.addEventListener("timeupdate", () => {
          if ((!activeVideo || activeVideo.paused) && !isVideoDismissed(video)) {
            setActiveVideo(video);
          }
        });

        const parentContainer = video.closest("div[role='article'], div[data-pagelet*='FeedUnit'], #movie_player, .html5-video-player");
        if (parentContainer && !parentContainer.dataset.atlasTracked) {
          parentContainer.dataset.atlasTracked = "true";
          parentContainer.addEventListener("mouseenter", () => {
            if (!isVideoDismissed(video)) {
              setActiveVideo(video);
            }
          });
        }
      }

      // اختيار أفضل فيديو لم يتم إلغاء الزر عنه
      if (!isVideoDismissed(video)) {
        if (!video.paused && video.currentTime > 0) {
          bestVideo = video;
        } else if (!bestVideo) {
          const rect = video.getBoundingClientRect();
          if (rect.top >= 0 && rect.top <= window.innerHeight && rect.height > 100) {
            bestVideo = video;
          }
        }
      }
    });

    if (bestVideo && (!activeVideo || activeVideo.paused || isVideoDismissed(activeVideo))) {
      setActiveVideo(bestVideo);
    }
  }

  // معالجة وضع ملء الشاشة (Fullscreen)
  document.addEventListener("fullscreenchange", () => {
    const btn = getOrCreateButton();
    const fs = document.fullscreenElement;
    if (fs) {
      fs.appendChild(btn);
    } else {
      document.body.appendChild(btn);
    }
  });

  const observer = new MutationObserver(() => scanForVideos());
  observer.observe(document.body, { childList: true, subtree: true });

  window.addEventListener("load", scanForVideos);
  window.addEventListener("yt-navigate-finish", scanForVideos);
  window.addEventListener("scroll", () => {
    if (activeVideo && !hasCustomPosition && !isVideoDismissed(activeVideo)) {
      updateDefaultButtonPosition(activeVideo);
    }
  }, { passive: true });
  window.addEventListener("resize", () => {
    if (activeVideo && !hasCustomPosition && !isVideoDismissed(activeVideo)) {
      updateDefaultButtonPosition(activeVideo);
    }
  });

  setInterval(scanForVideos, 2500);

  document.addEventListener("click", (e) => {
    if (activeDropdown && !activeDropdown.contains(e.target) && !e.target.closest("#atlas-video-btn")) {
      activeDropdown.remove();
      activeDropdown = null;
    }
  });
})();
