#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing Terminal Radio..."

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
.venv/bin/python radio.py "\$@"
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

echo ""
echo "Installation complete!"
echo "Run 'radio' to start listening."
