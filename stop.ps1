<#
.SYNOPSIS
    Stops the Gieni OS platform servers (ports 8000 and 3000).

.DESCRIPTION
    Identifies and terminates processes specifically listening on port 8000 (FastAPI)
    and port 3000 (Vite Frontend), freeing them cleanly.

.PARAMETER BackendPort
    Port for the FastAPI backend (Default: 8000).

.PARAMETER FrontendPort
    Port for the Vite frontend (Default: 3000).

.EXAMPLE
    .\stop.ps1
#>

[CmdletBinding()]
param (
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000
)

$ErrorActionPreference = "SilentlyContinue"

Write-Host ""
Write-Host " ====================================================================== " -ForegroundColor DarkYellow
Write-Host "   GIENI OS - STOPPING PLATFORM SERVERS                                 " -ForegroundColor Yellow
Write-Host " ====================================================================== " -ForegroundColor DarkYellow
Write-Host ""

function Stop-ProcessOnPort ([int]$Port, [string]$ServiceName) {
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' }
        if ($connections) {
            foreach ($conn in $connections) {
                $pidToKill = $conn.OwningProcess
                if ($pidToKill -gt 0) {
                    $proc = Get-Process -Id $pidToKill -ErrorAction SilentlyContinue
                    $procName = if ($proc) { $proc.ProcessName } else { "PID $pidToKill" }
                    Write-Host " [*] Stopping $ServiceName ($procName on Port $Port, PID: $pidToKill)..." -ForegroundColor Cyan
                    Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
                    Write-Host " [✓] $ServiceName stopped." -ForegroundColor Green
                }
            }
        } else {
            Write-Host " [i] No active process listening on Port $Port ($ServiceName)." -ForegroundColor Gray
        }
    } catch {
        Write-Host " [!] Error stopping process on Port $Port : $_" -ForegroundColor Red
    }
}

Stop-ProcessOnPort -Port $BackendPort -ServiceName "Backend API"
Stop-ProcessOnPort -Port $FrontendPort -ServiceName "Frontend Dev Server"

Write-Host ""
Write-Host " [✓] Cleanup completed." -ForegroundColor Green
Write-Host ""
