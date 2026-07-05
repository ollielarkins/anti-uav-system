# Run this in PowerShell as Administrator.
# Enables WSL2 and installs Ubuntu 22.04.
# After it finishes: reboot, then open "Ubuntu 22.04" from the Start menu.

Write-Host "`n=== Anti-UAV System: Windows WSL2 Setup ===" -ForegroundColor Cyan

# Check running as admin
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Run this script as Administrator (right-click PowerShell -> Run as Administrator)"
    exit 1
}

# Enable WSL2
Write-Host "`n[1/3] Enabling WSL2..." -ForegroundColor Yellow
wsl --install --no-distribution
wsl --set-default-version 2

# Install Ubuntu 22.04
Write-Host "`n[2/3] Installing Ubuntu 22.04..." -ForegroundColor Yellow
wsl --install -d Ubuntu-22.04

# Install AMD Software reminder
Write-Host "`n[3/3] AMD GPU Driver Check" -ForegroundColor Yellow
Write-Host "Make sure you have AMD Software: Adrenalin Edition 23.40.27.01 or later."
Write-Host "Download from: https://www.amd.com/en/support"
Write-Host "(Required for ROCm GPU acceleration in WSL2)"

Write-Host "`n=== Done. REBOOT NOW, then open Ubuntu 22.04 from the Start menu. ===" -ForegroundColor Green
Write-Host "Once Ubuntu opens and you've set a username/password, run:" -ForegroundColor Green
Write-Host "  bash /mnt/c/Users/ozzal/anti-uav-system/scripts/2_wsl_setup.sh" -ForegroundColor White
