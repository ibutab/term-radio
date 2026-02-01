#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing Terminal Radio..."

# Check for mpv
if ! command -v mpv &> /dev/null; then
    echo "mpv not found. Installing..."
    if command -v brew &> /dev/null; then
        brew install mpv
    elif command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y mpv
    else
        echo "Error: Could not install mpv. Please install it manually."
        exit 1
    fi
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv "$SCRIPT_DIR/.venv"

# Install dependencies
echo "Installing dependencies..."
"$SCRIPT_DIR/.venv/bin/pip" install -q -r "$SCRIPT_DIR/requirements.txt"

# Create bin directory if needed
mkdir -p "$HOME/bin"

# Create radio command
cat > "$HOME/bin/radio" << EOF
#!/bin/bash
cd "$SCRIPT_DIR"
export PYGAME_HIDE_SUPPORT_PROMPT=1
export SDL_VIDEODRIVER=dummy
exec .venv/bin/python -O radio.py "\$@"
EOF
chmod +x "$HOME/bin/radio"

# Check if ~/bin is in PATH
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    SHELL_RC=""
    if [[ "$SHELL" == *"zsh"* ]]; then
        SHELL_RC="$HOME/.zshrc"
    elif [[ "$SHELL" == *"bash"* ]]; then
        SHELL_RC="$HOME/.bashrc"
    fi
    
    if [[ -n "$SHELL_RC" ]]; then
        echo '' >> "$SHELL_RC"
        echo '# Terminal Radio' >> "$SHELL_RC"
        echo 'export PATH="$HOME/bin:$PATH"' >> "$SHELL_RC"
        echo "Added ~/bin to PATH in $SHELL_RC"
        echo "Run 'source $SHELL_RC' or restart your terminal."
    fi
fi

# Pre-compile bytecode for faster subsequent starts
"$SCRIPT_DIR/.venv/bin/python" -m compileall -q "$SCRIPT_DIR"

echo ""
echo "Installation complete!"
echo "Run 'radio' to start listening."
