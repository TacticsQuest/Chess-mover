# Pi 5 Desktop Shortcuts

This folder contains desktop shortcut files (.desktop) for your Raspberry Pi 5.

## Installation Instructions

On your Raspberry Pi 5, run these commands:

```bash
# 1. Create Desktop directory if it doesn't exist
mkdir -p ~/Desktop

# 2. Copy shortcut files to Desktop
cp ~/Chess-mover/pi5-desktop-shortcuts/*.desktop ~/Desktop/

# 3. Make them executable
chmod +x ~/Desktop/*.desktop

# 4. Trust and allow launching (REQUIRED for Raspberry Pi OS)
gio set ~/Desktop/claude-code.desktop metadata::trusted true
gio set ~/Desktop/chess-mover.desktop metadata::trusted true
```

## Shortcuts Included

### 1. Claude Code
- **Icon:** Terminal
- **Action:** Opens Claude Code in Chess Mover directory
- **Usage:** Double-click to start coding with AI assistance

### 2. Chess Mover Machine
- **Icon:** Games
- **Action:** Launches the Chess Mover application
- **Usage:** Double-click to start the chess robot

## Troubleshooting

### Shortcut doesn't work when double-clicked
**Solution:** Make sure you ran the `chmod +x` and `gio set` commands above.

### "Untrusted application launcher" warning
**Solution:** Right-click the .desktop file → "Allow Launching"

Or run:
```bash
gio set ~/Desktop/claude-code.desktop metadata::trusted true
```

### Claude Code says "command not found"
**Solution:** Restart your terminal or run:
```bash
source ~/.bashrc
```

The PATH should now include `$HOME/.local/bin`

### Chess Mover doesn't start
**Possible issues:**
1. Python dependencies not installed - run `pip install -r requirements.txt`
2. main.py doesn't exist - check repo structure
3. Virtual environment not activated - activate if using venv

## Manual Launch

If shortcuts don't work, you can launch manually:

### Claude Code:
```bash
cd ~/Chess-mover
claude
```

### Chess Mover:
```bash
cd ~/Chess-mover
python main.py
```

## Customization

To change icons, edit the `Icon=` line in the .desktop files.

Common icon names on Raspberry Pi OS:
- `terminal` - Terminal icon
- `applications-games` - Games icon
- `applications-development` - Development icon
- `system-run` - Run/execute icon

To use a custom icon, provide full path:
```
Icon=/home/david/Chess-mover/icon.png
```
