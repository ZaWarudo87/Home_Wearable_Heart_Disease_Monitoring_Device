# Heart Monitor Docker Startup Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Heart Monitor - Docker Deploy" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/5] Checking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "OK Docker: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR Docker not found!" -ForegroundColor Red
    Write-Host "Install from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

Write-Host "[2/5] Checking Docker service..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "OK Docker running" -ForegroundColor Green
} catch {
    Write-Host "ERROR Docker not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop" -ForegroundColor Yellow
    exit 1
}

Write-Host "[3/5] Backend directory check..." -ForegroundColor Yellow
$currentPath = Get-Location
Write-Host "OK Path: $currentPath" -ForegroundColor Green

Write-Host ""
Write-Host "[4/5] Building Docker container..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray
Write-Host ""

docker-compose down 2>$null
docker-compose up --build -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "OK Container started" -ForegroundColor Green
} else {
    Write-Host "ERROR Container failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[5/5] Getting Cloudflare URL..." -ForegroundColor Yellow
Write-Host "Waiting 15 seconds..." -ForegroundColor Gray
Start-Sleep -Seconds 15

$tunnelUrl = ""
for ($i = 1; $i -le 10; $i++) {
    $logs = docker logs heart-monitor-backend 2>&1
    $match = $logs | Select-String -Pattern "https://[a-zA-Z0-9-]+\.trycloudflare\.com" | Select-Object -First 1
    
    if ($match) {
        $matchStr = $match.ToString().Trim()
        if ($matchStr -match "(https://[a-zA-Z0-9-]+\.trycloudflare\.com)") {
            $tunnelUrl = $matches[1]
            break
        }
    }
    
    Write-Host "Attempt $i/10..." -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SUCCESS!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($tunnelUrl) {
    Write-Host "Cloudflare URL:" -ForegroundColor Green
    Write-Host "  $tunnelUrl" -ForegroundColor Yellow
    Write-Host ""
    
    try {
        Set-Clipboard -Value $tunnelUrl
        Write-Host "OK URL copied to clipboard!" -ForegroundColor Green
    } catch {
        # Ignore clipboard errors
    }
} else {
    Write-Host "WARNING Could not get URL" -ForegroundColor Yellow
    Write-Host "Run: docker logs heart-monitor-backend | Select-String trycloudflare" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Local URL:" -ForegroundColor Green
Write-Host "  http://localhost:5001" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Copy Cloudflare URL above" -ForegroundColor White
Write-Host "2. Edit frontend/script.js" -ForegroundColor White
Write-Host "3. Update API_BASE_URL" -ForegroundColor White
Write-Host "4. Open frontend/index.html" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Commands:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Logs:    docker-compose logs -f" -ForegroundColor Gray
Write-Host "Stop:    docker-compose down" -ForegroundColor Gray
Write-Host "Restart: docker-compose restart" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "View live logs? (y/n): " -NoNewline -ForegroundColor Yellow
$response = Read-Host

if ($response -eq 'y' -or $response -eq 'Y') {
    Write-Host ""
    Write-Host "Live logs (Ctrl+C to exit)..." -ForegroundColor Cyan
    Write-Host ""
    docker-compose logs -f
}