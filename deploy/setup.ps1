Write-Host "========================================"
Write-Host "  TestForge Setup"
Write-Host "========================================"
Write-Host ""

# Check Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Node.js not found" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python not found" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

$DEPLOY_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

# Step 1: Install PM2
Write-Host "[1/6] Checking PM2..."
if (-not (Get-Command pm2 -ErrorAction SilentlyContinue)) {
    Write-Host "       Installing PM2..."
    npm install -g pm2
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] PM2 install failed" -ForegroundColor Red
        Read-Host "Press Enter to close"
        exit 1
    }
    Write-Host "       PM2 installed"
} else {
    Write-Host "       PM2 already installed"
}

# Step 2: Log rotation
Write-Host "[2/6] Configuring log rotation..."
pm2 install pm2-logrotate 2>$null
pm2 set pm2-logrotate:max_size 10M 2>$null
pm2 set pm2-logrotate:retain 7 2>$null
pm2 set pm2-logrotate:compress true 2>$null
Write-Host "       Done"

# Step 3: Logs directory
Write-Host "[3/6] Creating logs directory..."
$logDir = Join-Path $DEPLOY_DIR "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
Write-Host "       Done"

# Step 4: Clean old processes
Write-Host "[4/6] Cleaning old processes..."
pm2 delete testforge-backend 2>$null
pm2 delete testforge-celery-worker 2>$null
pm2 delete testforge-celery-beat 2>$null
pm2 delete testforge-frontend 2>$null
Write-Host "       Done"

# Step 5: Start services
Write-Host "[5/6] Starting services..."
Set-Location $DEPLOY_DIR
pm2 start ecosystem.config.js
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to start services" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}
Start-Sleep -Seconds 3

# Step 6: Auto-start
Write-Host "[6/6] Configuring auto-start..."
pm2 save 2>$null

# Create scheduled task
$taskName = "TestForge-PM2"
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction -Execute "$env:APPDATA\npm\pm2.cmd" -Argument "resurrect" -WorkingDirectory $DEPLOY_DIR
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -User "SYSTEM" -RunLevel Highest -Force | Out-Null
Write-Host "       Done"

Write-Host ""
Write-Host "========================================"
Write-Host "  Setup complete!" -ForegroundColor Green
Write-Host "========================================"
Write-Host ""
pm2 status
Write-Host ""
Write-Host "  Commands:"
Write-Host "    pm2 status      - Check status"
Write-Host "    pm2 logs        - View logs"
Write-Host "    pm2 restart all - Restart all"
Write-Host "    pm2 stop all    - Stop all"
Write-Host "    pm2 monit       - Monitor"
Write-Host ""
Write-Host "  Backend:  http://localhost:8000/health"
Write-Host "  Frontend: http://localhost:5173"

Write-Host ""
Read-Host "Press Enter to close"
