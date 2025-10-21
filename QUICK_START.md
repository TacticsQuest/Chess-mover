# Chess Mover Machine - Quick Start Guide

## 🚀 First Time Setup (5 Minutes)

### Step 1: Verify Python Installation

Open Command Prompt and check Python is installed:
```cmd
python --version
```

You should see `Python 3.12.10` or similar (3.11+ required).

If not installed:
1. Download Python from https://python.org
2. During installation, **check "Add Python to PATH"**
3. Restart Command Prompt

### Step 2: Install Dependencies

Navigate to the Chess Mover Machine folder and run:
```cmd
cd "C:\Users\David\Documents\GitHub\Chess Mover Machine"
pip install -r requirements.txt
```

This installs:
- `pyserial` - For USB/serial communication with Falcon
- `pyyaml` - For configuration files

---

## 🎮 Launching the Application

### Option 1: Double-Click Launcher (Easiest)

1. Navigate to the Chess Mover Machine folder
2. Double-click **`launch.bat`**
3. The application will start automatically

### Option 2: Python Launcher (With Error Details)

1. Open Command Prompt
2. Run:
   ```cmd
   cd "C:\Users\David\Documents\GitHub\Chess Mover Machine"
   python launcher.py
   ```

### Option 3: Direct Launch (Advanced)

```cmd
cd "C:\Users\David\Documents\GitHub\Chess Mover Machine"
python main.py
```

---

## 🔌 Connecting the Falcon Gantry

### Hardware Setup

1. **Plug in Falcon** - Connect Falcon's USB cable to your PC
2. **Wait 5 seconds** - Windows will install drivers
3. **Find COM Port:**
   - Open **Device Manager** (Win+X → Device Manager)
   - Expand **Ports (COM & LPT)**
   - Look for "USB Serial Port (COM#)" - note the number (e.g., COM4)

### Software Connection

1. **Launch the application** (use launch.bat)
2. **Click "Settings"** in the top toolbar
3. **Select your COM port** from the dropdown
4. **Set baud rate** to `115200` (default for GRBL)
5. **Click "Save"**
6. **Click "Connect"** in the main window
7. You should see `Connected: COM#` in the status bar

### Test Connection

1. **Click "Home"** - The gantry will move to home position (requires limit switches)
2. Watch the command log - you should see GRBL responses
3. If successful, you'll see `ok` messages

---

## 🎯 Configuring for Chess Board

### Board Dimensions

1. **Measure your physical board:**
   - Width (mm)
   - Height (mm)
   - Example: Standard 400mm x 400mm board

2. **Set origin point (A1 corner):**
   - Place board under gantry
   - Manually jog gantry to A1 square center
   - Note the X/Y coordinates from GRBL
   - In Settings, enter these as "Origin X" and "Origin Y"

3. **Save settings**

### Quick Calibration Steps

1. **Place board** under gantry (any corner can be origin)
2. **Home the gantry** (`$H` or click "Home")
3. **Move to A1 center:**
   - Use Settings to set where A1 should be
   - Click the A1 square on the canvas
   - Verify gantry moves to correct position
4. **Test corners:**
   - Click "Test Path" - gantry visits A1, H1, H8, A8, center, back to A1
   - If aligned correctly, the head visits square centers

### Adjusting Alignment

If squares are off:
- **Adjust Origin X/Y** - Shifts entire board
- **Adjust Board Width/Height** - Changes square size
- **Check rotation** - Board may be rotated vs. machine axes

---

## 🎪 Using the Application

### Main Interface

```
┌─────────────────────────────────────────────┐
│ [Connect] [Disconnect] [Home] [Settings]   │ ← Toolbar
│                                  [Test Path]│
├───────────────┬─────────────────────────────┤
│               │                             │
│   Chess       │   Command Log               │
│   Board       │                             │
│   Canvas      │   >> G0 X100 Y100           │
│               │   << ok                     │
│   (Click      │   [UI] Clicked square e4    │
│   squares)    │   >> G0 X175.0 Y175.0       │
│               │   << ok                     │
│               │                             │
├───────────────┴─────────────────────────────┤
│ Status: Connected: COM4                     │ ← Status Bar
└─────────────────────────────────────────────┘
```

### Moving the Gantry

**Method 1: Click a Square**
- Click any square on the board canvas
- Gantry moves to that square's center
- Logged in command window

**Method 2: Test Path**
- Click "Test Path"
- Gantry visits: A1 → H1 → H8 → A8 → center → A1
- Good for verifying calibration

**Method 3: Manual GRBL Commands**
- Type G-code directly in Settings (future feature)

### GRBL Commands Reference

| Command | Description |
|---------|-------------|
| `$H` | Home cycle (moves to limit switches) |
| `$X` | Unlock (after alarm) |
| `G0 X100 Y100 F2000` | Rapid move to X100, Y100 at 2000mm/min |
| `?` | Status query (position, state) |
| `!` | Emergency stop (feed hold) |
| `~` | Resume from hold |

---

## 🔧 Troubleshooting

### "No COM ports found"

**Problem:** Application can't find Falcon
**Solutions:**
1. Ensure Falcon is plugged in via USB
2. Check Device Manager for COM port
3. Install CH340 drivers if needed: https://learn.sparkfun.com/tutorials/how-to-install-ch340-drivers
4. Try a different USB cable
5. Restart computer

### "Connection failed"

**Problem:** Can't connect to selected port
**Solutions:**
1. Close other programs using the serial port (Arduino IDE, other CNC software)
2. Verify correct COM port in Settings
3. Check baud rate is 115200
4. Unplug/replug Falcon USB
5. Try different COM port

### "Alarm" state

**Problem:** GRBL is locked in alarm state
**Solutions:**
1. Click "Home" to perform homing cycle
2. If no limit switches, manually unlock:
   - In command log, send `$X`
3. Check GRBL settings with `$$`

### Gantry moves to wrong squares

**Problem:** Calibration is off
**Solutions:**
1. Re-measure board dimensions
2. Verify origin X/Y coordinates
3. Check board orientation (A1 in correct corner)
4. Run Test Path to see pattern
5. Adjust settings incrementally

### Application won't launch

**Problem:** Python or dependency issues
**Solutions:**
1. Check Python installed: `python --version`
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Use `launcher.py` to see detailed error messages
4. Check permissions (Run as Administrator if needed)

---

## 📁 Creating Desktop Shortcut (Windows)

### Method 1: Manual Shortcut

1. **Right-click** on Desktop
2. **New → Shortcut**
3. **Target:** `C:\Users\David\Documents\GitHub\Chess Mover Machine\launch.bat`
4. **Name:** Chess Mover Machine
5. **Click Finish**

### Method 2: Copy Existing File

1. Navigate to Chess Mover Machine folder
2. Right-click `launch.bat`
3. **Send to → Desktop (create shortcut)**
4. Rename shortcut to "Chess Mover Machine"

### Optional: Custom Icon

1. Right-click shortcut → **Properties**
2. Click **Change Icon**
3. Browse to an icon file (`.ico`) or choose Windows default
4. Click **OK**

---

## 🎓 Next Steps

### Phase 1 (Current): Gantry Control
- [x] Connect to Falcon via USB
- [x] Click squares to move gantry
- [x] Calibrate board alignment
- [ ] Save/load calibration profiles
- [ ] Live position display

### Phase 2: Raspberry Pi Deployment
- [ ] Deploy same code to Raspberry Pi
- [ ] Auto-start on boot
- [ ] VNC remote control

### Phase 3: Servo Control
- [ ] Add gripper servo (open/close)
- [ ] Add lift servo (up/down)
- [ ] Integrate PCA9685 controller
- [ ] Complete piece moving

---

## 📚 Additional Resources

- **GRBL Wiki:** https://github.com/grbl/grbl/wiki
- **G-code Reference:** https://linuxcnc.org/docs/html/gcode.html
- **Project Docs:** See `CLAUDE DOCS CHESS MOVER/` folder

---

## 🆘 Getting Help

If you encounter issues:

1. Check this troubleshooting guide
2. Review logs in application command window
3. Check `CLAUDE DOCS CHESS MOVER/` folder for detailed documentation
4. Test with mock hardware first (see TESTING_GUIDE.md)

**Remember:** This controls physical hardware - always:
- Keep emergency stop accessible
- Start with slow speeds
- Test in safe environment
- Monitor first movements closely

---

**Happy Chess Moving!** 🤖♟️
