// Atlas DownloadTube - Popup Controller
document.addEventListener("DOMContentLoaded", () => {
  const statusBadge = document.getElementById("app-status");
  const urlBox = document.getElementById("url-box");
  const analyzeBtn = document.getElementById("analyze-tab-btn");
  const resultsContainer = document.getElementById("results-container");

  let currentTabUrl = "";
  let currentTabTitle = "";

  // فحص الاتصال بالخدمة
  chrome.runtime.sendMessage({ action: "ping" }, (res) => {
    if (res && res.success) {
      statusBadge.textContent = "متصل بالخدمة ✓";
      statusBadge.className = "status-badge online";
    } else {
      statusBadge.textContent = "الخدمة غير متصلة ✗";
      statusBadge.className = "status-badge offline";
    }
  });

  // قراءة التبويب النشط
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs && tabs[0]) {
      currentTabUrl = tabs[0].url || "";
      currentTabTitle = tabs[0].title || "video";
      urlBox.textContent = currentTabUrl;
    }
  });

  analyzeBtn.addEventListener("click", () => {
    if (!currentTabUrl) return;

    analyzeBtn.textContent = "جاري الفحص واستخراج الوسائط... ⏳";
    analyzeBtn.disabled = true;

    chrome.runtime.sendMessage(
      {
        action: "analyze",
        url: currentTabUrl,
        title: currentTabTitle,
      },
      (data) => {
        analyzeBtn.textContent = "🔍 فحص واستخراج وسائط الصفحة";
        analyzeBtn.disabled = false;

        resultsContainer.style.display = "block";

        if (!data || data.status !== "success") {
          resultsContainer.innerHTML = `
            <div style="color: #cbd5e0; text-align: center; padding: 10px; font-size:12px;">
              ${(data && data.message) || "لم يتم العثور على خيارات وسائط مباشرة لهذه الصفحة."}
              <button id="popup-dl-btn" class="btn" style="margin-top:8px;">
                🚀 بدء التحميل بأعلى جودة
              </button>
            </div>
          `;
          const pBtn = resultsContainer.querySelector("#popup-dl-btn");
          if (pBtn) {
            pBtn.addEventListener("click", () => {
              chrome.runtime.sendMessage({
                action: "download",
                url: currentTabUrl,
                quality: "best",
                title: currentTabTitle,
              });
              window.close();
            });
          }
          return;
        }

        let html = `<div style="font-weight:bold; color:#00d26a; margin-bottom:8px; font-size:12px;">🎬 ${data.title}</div>`;

        if (data.video_options && data.video_options.length > 0) {
          data.video_options.forEach((opt) => {
            html += `
              <div class="opt-item" data-q="${opt}">
                <span>${opt}</span>
                <span class="badge" style="background:#007bff; color:#fff;">MP4</span>
              </div>
            `;
          });
        }

        if (data.audio_options && data.audio_options.length > 0) {
          data.audio_options.forEach((opt) => {
            html += `
              <div class="opt-item" data-q="${opt}">
                <span>${opt}</span>
                <span class="badge" style="background:#2f855a; color:#fff;">MP3</span>
              </div>
            `;
          });
        }

        resultsContainer.innerHTML = html;

        resultsContainer.querySelectorAll(".opt-item").forEach((el) => {
          el.addEventListener("click", () => {
            const q = el.getAttribute("data-q");
            chrome.runtime.sendMessage({
              action: "download",
              url: currentTabUrl,
              quality: q,
              title: data.title || currentTabTitle,
            });
            window.close();
          });
        });
      }
    );
  });
});
