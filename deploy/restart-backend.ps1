Write-Host "Restarting backend..." -ForegroundColor Yellow
pm2 restart testforge-backend
pm2 restart testforge-celery-worker
pm2 restart testforge-celery-beat
Write-Host ""
Write-Host "Done!" -ForegroundColor Green
Read-Host "Press Enter to close"
