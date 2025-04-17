#!/bin/bash

INSTALL_DIR="${HOME}/.local/bin"
SCRIPT_NAME="kreq"
SCRIPT_SOURCE="kreq.py"

# Create target directory if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Verify source file exists
if [ ! -f "$SCRIPT_SOURCE" ]; then
    echo "Error: Source file $SCRIPT_SOURCE not found"
    exit 1
fi

# Install
echo "Installing $SCRIPT_NAME to $INSTALL_DIR"
cp "$SCRIPT_SOURCE" "$INSTALL_DIR/$SCRIPT_NAME"
chmod +x "$INSTALL_DIR/$SCRIPT_NAME"

# Update PATH if needed
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> ~/.bashrc
    echo "Note: Added $INSTALL_DIR to PATH in ~/.bashrc"
    echo "Run 'source ~/.bashrc' or restart your terminal"
fi

echo "Success: $SCRIPT_NAME installed"
echo "Verify with: kreq --help"
