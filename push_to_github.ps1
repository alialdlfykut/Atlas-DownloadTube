[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "Atlas DownloadTube - GitHub Uploader"

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  جاري رفع مشروع Atlas DownloadTube إلى GitHub..." -ForegroundColor Yellow
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "المستودع: https://github.com/alialdlfykut/Atlas-DownloadTube" -ForegroundColor Gray
Write-Host ""
Write-Host "إذا ظهرت لك نافذة في المتصفح، اضغط على 'Sign in with your browser' للموافقة." -ForegroundColor Magenta
Write-Host ""

git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "====================================================" -ForegroundColor Green
    Write-Host "  [✓] تم رفع المشروع بنجاح تام إلى GitHub!" -ForegroundColor Green
    Write-Host "====================================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "====================================================" -ForegroundColor Red
    Write-Host "  [!] حدث خطأ أثناء الرفع، تأكد من تسجيل الدخول بحسابك." -ForegroundColor Red
    Write-Host "====================================================" -ForegroundColor Red
}

Write-Host ""
Read-Host "اضغط Enter للإغلاق..."
