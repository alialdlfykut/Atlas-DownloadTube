@echo off
chcp 65001 >nul
echo ===================================================
echo   تثبيت خدمة Atlas DownloadTube الخلفية للتحميل
echo ===================================================
echo.
powershell -NoProfile -Command "Copy-Item '%~dp0start_silent_service.vbs' ([Environment]::GetFolderPath('Startup') + '\Atlas_DownloadTube_Service.vbs') -Force"
echo [✓] تم تفعيل التشغيل التلقائي مع إقلاع الويندوز بنجاح!
echo [✓] جاري تشغيل الخدمة الصامتة في الخلفية الآن...
start "" wscript.exe "%~dp0start_silent_service.vbs"
echo.
echo ===================================================
echo   كل شيء جاهز الآن! يمكنك الذهاب لمتصفح كروم 
echo   وتحميل أي فيديو مباشرة بنقرة واحدة وبدون تكرار!
echo ===================================================
pause
