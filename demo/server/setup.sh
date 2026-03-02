#!/bin/bash
# Setup script to quickly initialize the virtual environment and run the server
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Create config file if it doesn't exist
if [ ! -e "$SCRIPT_DIR/config.json" ]; then
	echo Creating default config...
	cp "$SCRIPT_DIR/config-example.json" "$SCRIPT_DIR/config.json"
fi

# Create virtual environment if it doesn't exist or is broken
# Also check the interpreter is still valid (e.g. Python was upgraded/removed)
if [ ! -f "$SCRIPT_DIR/venv/bin/activate" ] || ! "$SCRIPT_DIR/venv/bin/python3" --version &>/dev/null; then
	echo Creating virtual environment...
	rm -rf "$SCRIPT_DIR/venv"
	if ! python3 -m venv "$SCRIPT_DIR/venv"; then
		echo ""
		echo "ERROR: Failed to create virtual environment."
		echo "On Debian/Ubuntu, install the required packages with:"
		echo "  sudo apt-get install python3-venv python3-pip"
		echo ""
		exit 1
	fi
fi

# Activate virtual environment
echo Activating virtual environment...
source "$SCRIPT_DIR/venv/bin/activate"

# Upgrade pip to ensure binary wheels are recognized (e.g. pydantic-core on Apple Silicon)
# Use 'python -m pip' directly in case pip3 wasn't installed into the venv (e.g. minimal Ubuntu)
echo Upgrading pip...
if ! "$SCRIPT_DIR/venv/bin/python3" -m pip install --upgrade pip; then
	echo ""
	echo "ERROR: pip is not available in the virtual environment."
	echo "On Debian/Ubuntu, install the required packages with:"
	echo "  sudo apt-get install python3-venv python3-pip"
	echo ""
	exit 1
fi

# Install requirements
echo Install dependencies...
if ! "$SCRIPT_DIR/venv/bin/python3" -m pip install -r "$SCRIPT_DIR/requirements.txt"; then
	echo ""
	echo "ERROR: Failed to install dependencies."
	echo "If the error mentions 'pydantic-core' or 'failed building wheel',"
	echo "ensure you have a recent Python (3.11+) and try again."
	echo ""
	exit 1
fi

# Run the server
echo Starting server...
"$SCRIPT_DIR/venv/bin/python3" "$SCRIPT_DIR/app.py"
