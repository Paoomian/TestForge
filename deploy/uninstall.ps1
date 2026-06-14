Write-Host "========================================"
Write-Host "  TestForge Uninstall"
Write-Host "========================================"
Write-Host ""

Write-Host "[1/3] Stopping PM2 processes..."
pm2 delete testforge-backend 2>$null
pm2 delete testforge-celery-worker 2>$null
pm2 delete testforge-celery-beat 2>$null
pm2 delete testforge-frontend 2>$null
pm2 kill 2>$null
Write-Host "       Done"

Write-Host "[2/3] Removing scheduled task..."
Unregister-ScheduledTask -TaskName "TestForge-PM2" -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "       Done"

Write-Host "[3/3] Cleaning logs..."
$logDir = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "logs"
if (Test-Path $logDir) { Remove-Item "$logDir\*" -Force -ErrorAction SilentlyContinue }
Write-Host "       Done"

Write-Host ""
Write-Host "========================================"
Write-Host "  Uninstall complete!" -ForegroundColor Green
Write-Host "========================================"
Write-Host ""
Write-Host "  To fully remove PM2:"
Write-Host "    npm uninstall -g pm2"
Write-Host "    npm uninstall -g pm2-logrotate"

Write-Host ""
Read-Host "Press Enter to close"
