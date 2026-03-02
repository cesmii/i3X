#!/bin/bash
# Setup script to quickly initialize the virtual environment and run the server
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Create config file if it doesn't exist
if [ ! -e "$SCRIPT_DIR/config.json" ]; then
	echo Creating default config...
	cp "$SCRIPT_DIR/config-example.json" "$SCRIPT_DIR/config.json"
fi

# Create virtual environment if it doesn't exist or is broken
if [ ! -f "$SCRIPT_DIR/venv/bin/activate" ]; then
	echo Creating virtual environment...
	rm -rf "$SCRIPT_DIR/venv"
	if ! python3 -m venv "$SCRIPT_DIR/venv"; then
		echo ""
		echo "ERROR: Failed to create virtual environment."
		echo "On Debian/Ubuntu, install the venv module with:"
		echo "  sudo apt-get install python3-venv"
		echo ""
		exit 1
	fi
fi

# Activate virtual environment
echo Activating virtual environment...
source "$SCRIPT_DIR/venv/bin/activate"

# Upgrade pip to ensure binary wheels are recognized (e.g. pydantic-core on Apple Silicon)
echo Upgrading pip...
"$SCRIPT_DIR/venv/bin/pip3" install --upgrade pip

# Install requirements
echo Install dependencies...
if ! "$SCRIPT_DIR/venv/bin/pip3" install -r "$SCRIPT_DIR/requirements.txt"; then
	echo ""
	echo "ERROR: Failed to install dependencies."
	echo "If the error mentions 'pydantic-core' or 'failed building wheel',"
	echo "ensure you have a recent Python (3.11+) and try again."
	echo "On Apple Silicon Macs, upgrading pip (done above) usually resolves this."
	echo ""
	exit 1
fi

# Run the server
echo Starting server...
"$SCRIPT_DIR/venv/bin/python3" "$SCRIPT_DIR/app.py"
