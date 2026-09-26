<#
.SYNOPSIS
    Starts the Gieni OS Acquisition Decision Intelligence Platform.
    Launches FastAPI Backend (port 8000) and Vite React 18 Frontend (port 3000).

.DESCRIPTION
    By default, starts both the backend API and frontend dev server with live hot reload.
    Supports -Unified switch to run the compiled production SPA directly from FastAPI.

.PARAMETER Unified
    Runs only the FastAPI server which serves both the API and the compiled React SPA.

.PARAMETER NoBrowser
    Do not automatically open the web browser upon startup.

.PARAMETER BackendPort
    Port for the FastAPI backend (Default: 8000).

.PARAMETER FrontendPort
    Port for the Vite frontend (Default: 3000).

.EXAMPLE
    .\start.ps1
    Starts both Backend (port 8000) and Frontend (port 3000).

.EXAMPLE
    .\start.ps1 -Unified
    Starts the single unified FastAPI server on port 8000 serving the SPA.
#>

[CmdletBinding()]
param (
    [switch]$Unified,
    [switch]$NoBrowser,
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

# Set PowerShell Title
$host.UI.RawUI.WindowTitle = "Gieni OS - Platform Launcher"

Write-Host ""
Write-Host " ====================================================================== " -ForegroundColor DarkCyan
Write-Host "   GIENI OS - ACQUISITION DECISION INTELLIGENCE PLATFORM LAUNCHER       " -ForegroundColor Cyan
Write-Host " ====================================================================== " -ForegroundColor DarkCyan
Write-Host ""

# 1. Environment & Path Checks
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Host " [!] Virtual environment not found at .venv\Scripts\python.exe" -ForegroundColor Yellow
    Write-Host "     Falling back to system python..." -ForegroundColor Gray
    $PythonExe = "python"
}

# 2. Check for port conflicts
function Test-PortOccupied ([int]$Port) {
    try {
        $conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' }
        return ($null -ne $conn)
    } catch {
        return $false
    }
}

if (Test-PortOccupied -Port $BackendPort) {
    Write-Host " [!] Warning: Port $BackendPort is already occupied!" -ForegroundColor Yellow
    Write-Host "     To free port $BackendPort, run: .\stop.ps1" -ForegroundColor Gray
    Write-Host ""
}

# 3. Check / Build Frontend if needed
$FrontendDir = Join-Path $ProjectRoot "frontend"
$FrontendDist = Join-Path $FrontendDir "dist"
$IndexHtml = Join-Path $FrontendDist "index.html"

if ($Unified -or (-not (Test-Path $IndexHtml))) {
    if (-not (Test-Path $IndexHtml)) {
        Write-Host " [*] Frontend production bundle not found. Building SPA now..." -ForegroundColor Yellow
        Push-Location $FrontendDir
        try {
            npm run build
            Write-Host " [✓] Frontend build completed." -ForegroundColor Green
        } catch {
            Write-Host " [!] Build failed: $_" -ForegroundColor Red
        } finally {
            Pop-Location
        }
    }
}

# 4. Launch Backend (FastAPI on Port 8000)
Write-Host " [*] Starting FastAPI Backend on http://127.0.0.1:$BackendPort ..." -ForegroundColor Cyan
$BackendCmd = @"
`$host.UI.RawUI.WindowTitle = 'Gieni OS - Backend API (Port $BackendPort)';
`$env:PYTHONPATH = 'backend';
& '$PythonExe' -m uvicorn app.main:app --host 127.0.0.1 --port $BackendPort --reload
"@

$BackendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", $BackendCmd -PassThru

# Wait briefly for backend to initialize
Start-Sleep -Seconds 2

# 5. Launch Frontend (If not in Unified mode)
$FrontendProcess = $null
if (-not $Unified) {
    if (Test-PortOccupied -Port $FrontendPort) {
        Write-Host " [!] Notice: Port $FrontendPort is already active. Vite will automatically bind to the next available port." -ForegroundColor Yellow
    }

    Write-Host " [*] Starting Vite Frontend on http://localhost:$FrontendPort ..." -ForegroundColor Cyan
    $FrontendCmd = @"
`$host.UI.RawUI.WindowTitle = 'Gieni OS - Frontend Dev (Port $FrontendPort)';
Set-Location '$FrontendDir';
npm run dev
"@
    $FrontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", $FrontendCmd -PassThru
}

# 6. Display Operational Summary
Write-Host ""
Write-Host " [✓] Gieni OS Services Running Successfully!" -ForegroundColor Green
Write-Host ""
Write-Host " ---------------------------------------------------------------------- " -ForegroundColor DarkGray
if (-not $Unified) {
    Write-Host "   • Frontend Dev App:    http://localhost:$FrontendPort" -ForegroundColor White
}
Write-Host "   • Unified Portal:      http://127.0.0.1:$BackendPort/portal" -ForegroundColor White
Write-Host "   • Backend REST API:    http://127.0.0.1:$BackendPort/api/v1" -ForegroundColor White
Write-Host "   • Interactive Docs:    http://127.0.0.1:$BackendPort/docs" -ForegroundColor White
Write-Host "   • Health Check:        http://127.0.0.1:$BackendPort/health" -ForegroundColor White
Write-Host " ---------------------------------------------------------------------- " -ForegroundColor DarkGray
Write-Host ""
Write-Host "   Press [Ctrl+C] or run .\stop.ps1 to cleanly stop all servers." -ForegroundColor DarkYellow
Write-Host ""

# 7. Auto-open browser
if (-not $NoBrowser) {
    Start-Sleep -Seconds 1
    if (-not $Unified) {
        Start-Process "http://localhost:$FrontendPort"
    } else {
        Start-Process "http://127.0.0.1:$BackendPort/portal"
    }
}
