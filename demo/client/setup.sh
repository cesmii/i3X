#!/bin/bash
# Setup script to quickly initialize the virtual environment and run the client
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

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

# Install requirements
echo Install dependencies...
"$SCRIPT_DIR/venv/bin/pip3" install -r "$SCRIPT_DIR/requirements.txt"

# Run the client
echo Starting client...
"$SCRIPT_DIR/venv/bin/python3" "$SCRIPT_DIR/test_client.py"
