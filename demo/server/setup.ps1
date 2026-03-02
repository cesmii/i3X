# Setup script to quickly initialize the virtual environment and run the server

# Create config file if it doesn't exist
if (-not (Test-Path -Path "config.json")) {
    Write-Host "Creating default config..." -ForegroundColor Green
    Copy-Item -Path "config-example.json" -Destination "config.json"
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path -Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Green
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
.\venv\Scripts\Activate

# Upgrade pip to ensure binary wheels are recognized (e.g. pydantic-core on Apple Silicon)
Write-Host "Upgrading pip..." -ForegroundColor Green
pip install --upgrade pip

# Install requirements
Write-Host "Installing dependencies..." -ForegroundColor Green
pip install -r requirements.txt

# Run the server
Write-Host "Starting server..." -ForegroundColor Green
python app.py
