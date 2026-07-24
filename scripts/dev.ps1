# PowerShell version of scripts/dev.sh.
# Run from repo root:  .\scripts\dev.ps1

$ErrorActionPreference = "Stop"
$root = Resolve-Path "$PSScriptRoot/.."
Set-Location $root

if (-not (Test-Path "backend/.venv")) {
  Write-Host "backend/.venv missing — run: cd backend; python -m venv .venv; pip install -e '.[dev]'"
  exit 1
}
if (-not (Test-Path "frontend/node_modules")) {
  Write-Host "frontend/node_modules missing — run: cd frontend; npm install"
  exit 1
}

$backend = Start-Process `
  -FilePath "powershell" `
  -ArgumentList "-NoProfile","-Command","cd backend; .\.venv\Scripts\Activate.ps1; dazuoagent-api" `
  -PassThru -WindowStyle Minimized
$frontend = Start-Process `
  -FilePath "powershell" `
  -ArgumentList "-NoProfile","-Command","cd frontend; npm run dev" `
  -PassThru -WindowStyle Minimized

Write-Host "[backend]  http://127.0.0.1:8000"
Write-Host "[frontend] http://127.0.0.1:5173"
Write-Host "Press Ctrl-C to stop both."

try {
  while ($true) { Start-Sleep -Seconds 1 }
} finally {
  Stop-Process -Id $backend.Id, $frontend.Id -ErrorAction SilentlyContinue
}