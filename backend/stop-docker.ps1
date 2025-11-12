# Heart Monitor Docker Stop Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Stop Heart Monitor Container" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$currentPath = Get-Location
Write-Host "Path: $currentPath" -ForegroundColor Yellow
Write-Host ""

Write-Host "Stopping containers..." -ForegroundColor Yellow
docker-compose down

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "OK Containers stopped" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "ERROR Failed to stop" -ForegroundColor Red
    Write-Host ""
    exit 1
}

Write-Host "Remove images? (y/n): " -NoNewline -ForegroundColor Yellow
$response = Read-Host

if ($response -eq 'y' -or $response -eq 'Y') {
    Write-Host ""
    Write-Host "Removing images..." -ForegroundColor Yellow
    docker rmi backend-backend 2>$null
    Write-Host "OK Images removed" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Done!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""