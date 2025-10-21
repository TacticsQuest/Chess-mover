# Chess Mover Machine - Quick Reference Card

## 🚀 Launch Application

```bash
# Windows
launch.bat

# Or with Python
python launcher.py
python main.py
```

---

## 📁 Key Files & What They Do

| File | Purpose |
|------|---------|
| `main.py` | Application entry point |
| `ui/board_window.py` | Main GUI (themes, controls) |
| `controllers/servo_controller.py` | Servo control logic |
| `controllers/gantry_controller.py` | GRBL gantry control |
| `vision/board_finder.py` | ArUco board detection & warping |
| `vision/square_classifier.py` | Piece classification (empty/white/black) |
| `vision/move_verifier.py` | Move detection from board states |
| `vision/service.py` | FastAPI vision REST service |
| `utils/logger.py` | Logging system |
| `utils/diagnostics.py` | Self-test system |
| `config/settings.yaml` | User configuration |
| `logs/chess_mover_*.log` | Daily log files |

---

## 🎨 Theme Toggle

Click **☀** (sun) or **☾** (moon) in top-right toolbar

---

## 🔧 Common Code Tasks

### Add Logging
```python
from utils import get_logger

logger = get_logger(gui_callback=self._log)
logger.info("Operation started")
logger.gantry("Homing complete")
logger.servo("Lift moved to UP")
logger.error("Failed", exc_info=sys.exc_info())
```

### Run Diagnostics
```python
from utils.diagnostics import ChessMoverDiagnostics

diagnostics = ChessMoverDiagnostics(gantry, servos, logger)
all_passed = diagnostics.run_all(progress_callback)
summary = diagnostics.get_summary()
```

### Modify Theme Colors
```python
# File: ui/board_window.py, Lines 15-56
THEMES = {
    'dark': {
        'bg': '#1e1e1e',        # Background
        'fg': '#e0e0e0',        # Foreground text
        'accent': '#3498db',    # Accent color
        # ... more colors
    }
}
```

### Adjust Servo Positions
```python
# File: controllers/servo_controller.py, Lines 31-41
LIFT_UP_POS = 180      # Max up position
LIFT_DOWN_POS = 90     # Down position
GRIP_CLOSED_POS = 45   # Max close (force limited)
```

---

## 🐛 Troubleshooting

### App Won't Start
```bash
python --version  # Check Python 3.11+
pip install -r requirements.txt --force-reinstall
```

### Can't Connect to Gantry
1. Check Device Manager for COM port
2. Close Arduino IDE or other serial programs
3. Try different USB cable
4. Restart computer

### Theme Broken
- Delete `.pyc` files: `find . -name "*.pyc" -delete`
- Restart application
- Check `THEMES` dictionary in `board_window.py`

### Logs Not Appearing
- Check `logs/` folder exists
- Verify permissions: `ls -la logs/`
- Check logger initialization in code

---

## 📊 Phase Status

| Phase | Status | Action |
|-------|--------|--------|
| **Phase 1** | ✅ COMPLETE | Use on Windows |
| **Phase 2** | 📋 READY | Deploy to Raspberry Pi |
| **Phase 3** | 📋 READY | Integrate PCA9685 servos |
| **Phase 4** | ✅ IMPLEMENTED | Test vision system with USB camera |
| **Phase 5** | 📋 READY | Migrate to IMX500 on-sensor inference |
| **Phase 6** | 📋 PLANNED | Add advanced vision features |

---

## 🔑 Keyboard Shortcuts (In Development)

- `Enter` in "Move to Square" field → Execute move
- `Ctrl+T` → Toggle theme (to be implemented)
- `Ctrl+D` → Run diagnostics (to be implemented)
- `Ctrl+L` → Open logs folder (to be implemented)

---

## 📞 Documentation

- **Complete Summary:** `SESSION_SUMMARY.md`
- **Production Guide:** `PRODUCTION_READY.md`
- **Deployment:** `DEPLOYMENT_CHECKLIST.md`
- **User Guide:** `QUICK_START.md`
- **Vision Integration:** `VISION_INTEGRATION.md` (NEW!)
- **Vision Roadmap:** `VISION_ROADMAP.md`
- **Developer Docs:** `CLAUDE DOCS CHESS MOVER/`

---

## ⚡ Quick Commands

```bash
# View logs
tail -f logs/chess_mover_$(date +%Y%m%d).log

# Check Python packages
pip list | grep -E "(serial|yaml)"

# Find serial ports (Windows)
# Check Device Manager → Ports (COM & LPT)

# Find serial ports (Linux/Pi)
ls /dev/ttyUSB* /dev/ttyACM*

# Test Python
python -c "import tkinter; print('Tkinter OK')"
python -c "import serial; print('PySerial OK')"
python -c "import yaml; print('PyYAML OK')"

# Git commands
git status
git add .
git commit -m "Your message"
git push
```

---

## 🎯 Most Common Edits

1. **Change board colors:** `THEMES` in `board_window.py`
2. **Adjust servo limits:** Constants in `servo_controller.py`
3. **Modify logging:** Category methods in `logger.py`
4. **Add buttons:** `_build_ui()` in `board_window.py`
5. **Change board size:** Geometry in `__init__()` in `board_window.py`

---

## 🚨 Safety Reminders

- ✅ Always use logger, not print()
- ✅ Never hardcode colors (use theme)
- ✅ Keep servo position limits
- ✅ Test theme changes in both modes
- ✅ Update docs when adding features

---

## 📈 Performance Targets

- Startup: < 2 seconds
- GUI response: < 50ms
- Theme toggle: < 500ms
- Memory: < 150MB

---

**Keep this file handy for quick reference during development!**
