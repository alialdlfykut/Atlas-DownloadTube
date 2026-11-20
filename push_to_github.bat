@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ====================================================
echo   جاري رفع مشروع Atlas DownloadTube إلى GitHub...
echo ====================================================
echo.
echo سيتم الآن رفع الملفات إلى:
echo https://github.com/alialdlfykut/Atlas-DownloadTube
echo.
echo إذا ظهرت لك نافذة تسجيل الدخول إلى GitHub في المتصفح،
echo يرجى الضغط على "Sign in with your browser" وتأكيد الحساب.
echo.
git push -u origin main
echo.
if %errorlevel% equ 0 (
    echo ====================================================
    echo   [✓] تم رفع المشروع بنجاح تام إلى GitHub!
    echo ====================================================
) else (
    echo ====================================================
    echo   [!] حدث خطأ أثناء الرفع، تأكد من تسجيل الدخول بحسابك.
    echo ====================================================
)
echo.
pause
