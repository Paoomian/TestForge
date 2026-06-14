Write-Host "Restarting all services..." -ForegroundColor Yellow
pm2 restart all
Write-Host ""
Write-Host "Done!" -ForegroundColor Green
Read-Host "Press Enter to close"
