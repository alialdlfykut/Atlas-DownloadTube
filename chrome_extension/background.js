// Atlas DownloadTube - Background Service Worker (V5.0)
const PYTHON_API_BASE = "http://127.0.0.1:9876";

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "ping") {
    fetch(`${PYTHON_API_BASE}/ping`)
      .then((r) => r.json())
      .then((data) => sendResponse({ success: true, data }))
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (request.action === "analyze") {
    const url = request.url || "";
    const title = request.title || "";
    fetch(`${PYTHON_API_BASE}/analyze?url=${encodeURIComponent(url)}&title=${encodeURIComponent(title)}`)
      .then((r) => r.json())
      .then((data) => sendResponse(data))
      .catch((err) => sendResponse({ status: "error", message: err.message }));
    return true;
  }

  if (request.action === "download") {
    const url = request.url || "";
    const quality = request.quality || "best";
    const title = request.title || "";
    fetch(
      `${PYTHON_API_BASE}/download?url=${encodeURIComponent(url)}&quality=${encodeURIComponent(
        quality
      )}&title=${encodeURIComponent(title)}`
    )
      .then((r) => r.json())
      .then((data) => sendResponse(data))
      .catch((err) => sendResponse({ status: "error", message: err.message }));
    return true;
  }

  if (request.action === "get_status") {
    fetch(`${PYTHON_API_BASE}/status`)
      .then((r) => r.json())
      .then((data) => sendResponse(data))
      .catch((err) => sendResponse({ status: "error", message: err.message }));
    return true;
  }

  if (request.action === "open_downloads") {
    const file = request.file || "";

    // 1. فتح مجلد التنزيلات فوراً ومباشرة عبر محرك كروم نفسه ليظهر أمام المستخدم فوراً
    try {
      if (chrome.downloads && chrome.downloads.showDefaultFolder) {
        chrome.downloads.showDefaultFolder();
      }
    } catch (e) {}

    // 2. إرسال أمر للخدمة المحلية لتحديد وتظليل الملف داخل المجلد إن وجد
    const url = file
      ? `${PYTHON_API_BASE}/open_downloads?file=${encodeURIComponent(file)}`
      : `${PYTHON_API_BASE}/open_downloads`;

    fetch(url)
      .then((r) => r.json())
      .then((data) => sendResponse({ success: true, data }))
      .catch((err) => sendResponse({ success: true, error: err.message }));
    return true;
  }
});
