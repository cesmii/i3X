#!/bin/bash
# Setup script to quickly initialize the virtual environment and run the server
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Create config file if it doesn't exist
if [ ! -e "$SCRIPT_DIR/config.json" ]; then
	echo Creating default config...
	cp "$SCRIPT_DIR/config-example.json" "$SCRIPT_DIR/config.json"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$SCRIPT_DIR/venv" ]; then
	echo Creating virtual environment...
	python3 -m venv "$SCRIPT_DIR/venv"
fi

# Activate virtual environment
echo Activating virtual environment...
source "$SCRIPT_DIR/venv/bin/activate"

# Install requirements
echo Install dependencies...
"$SCRIPT_DIR/venv/bin/pip3" install -r "$SCRIPT_DIR/requirements.txt"

# Run the server
echo Starting server...
"$SCRIPT_DIR/venv/bin/python3" "$SCRIPT_DIR/app.py"
