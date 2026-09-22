param(
    [string]$Token = $env:CODECOV_TOKEN
)

# 1. If Token not passed or in env, check .env file
if (-not $Token -and (Test-Path .env)) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*CODECOV_TOKEN\s*=\s*(.+)$') {
            $script:Token = $matches[1].Trim('"', "'", ' ')
        }
    }
}

if (-not $Token) {
    Write-Error "Error: CODECOV_TOKEN not found. Provide it via -Token, set `$env:CODECOV_TOKEN, or add CODECOV_TOKEN=<token> to .env."
    exit 1
}

Write-Host "==> Running pytest with coverage..." -ForegroundColor Cyan
pytest

if ($LASTEXITCODE -ne 0) {
    Write-Error "Tests failed. Aborting coverage upload."
    exit $LASTEXITCODE
}

if (-not (Test-Path "coverage.xml")) {
    Write-Error "coverage.xml not found after running pytest."
    exit 1
}

Write-Host "==> Uploading coverage.xml to Codecov..." -ForegroundColor Cyan
if (Test-Path ".\codecov.exe") {
    .\codecov.exe upload-process -t $Token -f coverage.xml
} else {
    Write-Error "codecov.exe not found in workspace root."
    exit 1
}
