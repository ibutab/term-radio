#!/bin/bash

echo "Uninstalling Term-Radio..."

# Remove radio command
if [[ -f "$HOME/bin/radio" ]]; then
    rm "$HOME/bin/radio"
    echo "Removed ~/bin/radio"
fi

# Remove virtual environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -d "$SCRIPT_DIR/.venv" ]]; then
    rm -rf "$SCRIPT_DIR/.venv"
    echo "Removed virtual environment"
fi

echo ""
echo "Uninstall complete!"
echo "You can now delete this folder if you want."
