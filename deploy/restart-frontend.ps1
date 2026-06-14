Write-Host "Restarting frontend..." -ForegroundColor Yellow
pm2 restart testforge-frontend
Write-Host ""
Write-Host "Done!" -ForegroundColor Green
Read-Host "Press Enter to close"
