# Setup script to quickly initialize the virtual environment and run the server
$ScriptDir = $PSScriptRoot

# Create config file if it doesn't exist
if (-not (Test-Path -Path "$ScriptDir\config.json")) {
    Write-Host "Creating default config..." -ForegroundColor Green
    Copy-Item -Path "$ScriptDir\config-example.json" -Destination "$ScriptDir\config.json"
}

# Create virtual environment if it doesn't exist or is broken
# Also check the interpreter is still valid (e.g. Python was upgraded/removed)
$PythonExe = "$ScriptDir\venv\Scripts\python.exe"
if (-not (Test-Path -Path "$ScriptDir\venv") -or -not (& $PythonExe --version 2>$null)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Green
    Remove-Item -Recurse -Force "$ScriptDir\venv" -ErrorAction SilentlyContinue
    if (-not (python -m venv "$ScriptDir\venv")) {
        Write-Host ""
        Write-Host "ERROR: Failed to create virtual environment." -ForegroundColor Red
        Write-Host ""
        exit 1
    }
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& "$ScriptDir\venv\Scripts\Activate.ps1"

# Upgrade pip to ensure binary wheels are recognized (e.g. pydantic-core on Apple Silicon)
Write-Host "Upgrading pip..." -ForegroundColor Green
& "$ScriptDir\venv\Scripts\pip.exe" install --upgrade pip

# Install requirements
Write-Host "Installing dependencies..." -ForegroundColor Green
& "$ScriptDir\venv\Scripts\pip.exe" install -r "$ScriptDir\requirements.txt"
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Failed to install dependencies." -ForegroundColor Red
    Write-Host "If the error mentions 'pydantic-core' or 'failed building wheel',"
    Write-Host "ensure you have a recent Python (3.11+) and try again."
    Write-Host ""
    exit 1
}

# Run the server
Write-Host "Starting server..." -ForegroundColor Green
& "$ScriptDir\venv\Scripts\python.exe" "$ScriptDir\app.py"
