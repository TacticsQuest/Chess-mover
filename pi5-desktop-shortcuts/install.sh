#!/bin/bash
#
# Install desktop shortcuts for Raspberry Pi 5
# Run this script from the Chess Mover directory
#

echo "========================================"
echo "Raspberry Pi 5 Desktop Shortcuts Installer"
echo "========================================"
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "⚠ Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Installation cancelled."
        exit 1
    fi
fi

echo "Installing desktop shortcuts..."
echo ""

# 1. Create Desktop directory
echo "[1/4] Creating ~/Desktop directory..."
mkdir -p ~/Desktop

# 2. Copy shortcut files
echo "[2/4] Copying shortcut files..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/claude-code.desktop" ~/Desktop/
cp "$SCRIPT_DIR/chess-mover.desktop" ~/Desktop/

# 3. Make executable
echo "[3/4] Making shortcuts executable..."
chmod +x ~/Desktop/claude-code.desktop
chmod +x ~/Desktop/chess-mover.desktop

# 4. Trust shortcuts (required on Raspberry Pi OS)
echo "[4/4] Trusting shortcuts..."
if command -v gio &> /dev/null; then
    gio set ~/Desktop/claude-code.desktop metadata::trusted true 2>/dev/null || true
    gio set ~/Desktop/chess-mover.desktop metadata::trusted true 2>/dev/null || true
    echo "✓ Shortcuts trusted"
else
    echo "⚠ 'gio' command not found - you may need to right-click shortcuts and select 'Allow Launching'"
fi

echo ""
echo "========================================"
echo "✓ Installation Complete!"
echo "========================================"
echo ""
echo "Shortcuts installed:"
echo "  • Claude Code (Terminal)"
echo "  • Chess Mover Machine (Games)"
echo ""
echo "You can now double-click the shortcuts on your desktop."
echo ""

# Check if Claude Code is installed
if [ ! -f ~/.local/bin/claude ]; then
    echo "⚠ Warning: Claude Code not found at ~/.local/bin/claude"
    echo "   Install it with: curl -fsSL https://claude.ai/install.sh | bash"
    echo ""
else
    echo "✓ Claude Code found at ~/.local/bin/claude"
fi

# Check if PATH includes ~/.local/bin
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo "⚠ Warning: ~/.local/bin is not in your PATH"
    echo "   Add to ~/.bashrc: export PATH=\$HOME/.local/bin:\$PATH"
    echo "   Then run: source ~/.bashrc"
    echo ""
fi

echo "Enjoy your Chess Mover Machine! 🤖♟️"
