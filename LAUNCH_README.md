# Chess Mover Machine - Launch Guide

## ✅ What's Been Built

Your Chess Mover Machine application is ready to use! Here's what you have:

### Application Features
- **Tkinter GUI** with interactive chess board canvas
- **GRBL serial communication** for Falcon gantry control
- **Click-to-move** functionality (click square → gantry moves there)
- **Calibration system** for board alignment (origin X/Y, dimensions)
- **Settings dialog** for COM port, baud rate, and board config
- **Test path** function (visits corners and center)
- **Live command logging** to monitor GRBL communication
- **Profile support** for different board sizes

### Launchers Created
1. **`launch.bat`** - Windows batch file (double-click to start)
2. **`launcher.py`** - Python launcher with error handling
3. **`main.py`** - Direct Python entry point

---

## 🚀 How to Launch

### Quickest Method (Recommended)
```
1. Plug in Falcon via USB
2. Double-click: launch.bat
3. Application opens automatically
```

### Command Line Method
```cmd
cd "C:\Users\David\Documents\GitHub\Chess Mover Machine"
python launcher.py
```

---

## 🔌 Connecting Your Falcon

### When Falcon is Plugged In:

1. **Launch application** (use `launch.bat`)
2. **Click "Settings"** button
3. **COM Port dropdown** will show available ports
   - Example: `COM4` or `COM5`
   - If you see multiple, the Falcon is usually the higher number
4. **Set Baud Rate**: `115200` (GRBL default)
5. **Click "Save"**
6. **Click "Connect"** in main window

### You'll Know It's Connected When:
- Status bar shows: `Connected: COM#`
- Command log shows GRBL initialization messages
- Clicking "Home" moves the gantry

---

## 🎯 Configuring for Your Board

### Board Settings (in Settings dialog):

**Board Dimensions:**
- **Width (mm)**: Physical width of your chessboard (e.g., 400)
- **Height (mm)**: Physical height of your chessboard (e.g., 400)
- **Files**: Number of columns (8 for chess)
- **Ranks**: Number of rows (8 for chess)

**Origin Point (A1 corner):**
- **Origin X (mm)**: Machine X coordinate where A1 square center is
- **Origin Y (mm)**: Machine Y coordinate where A1 square center is

**Feed Rate:**
- **Feed Rate (mm/min)**: Speed of movement (default 2000, adjust for your machine)

### Quick Calibration:

1. **Place board** under gantry
2. **Home the gantry** (Click "Home" button)
3. **Set origin:**
   - Manually jog gantry to A1 center (or use UI to click A1)
   - Note X/Y position from GRBL status
   - Enter in Settings as Origin X/Y
4. **Test:** Click "Test Path" to verify alignment

---

## 📂 File Structure

```
Chess Mover Machine/
├── launch.bat              ← DOUBLE-CLICK TO START
├── launcher.py             ← Alternative launcher
├── main.py                 ← Main application entry
│
├── QUICK_START.md          ← Detailed setup guide
├── LAUNCH_README.md        ← This file
├── README.md               ← Project overview
│
├── config/
│   └── settings.yaml       ← Your saved settings
│
├── ui/                     ← GUI components
│   ├── board_window.py     ← Main window
│   └── settings_window.py  ← Settings dialog
│
├── controllers/            ← Hardware control
│   ├── gantry_controller.py ← GRBL/serial communication
│   └── servo_controller.py  ← Servo stubs (Phase 3)
│
├── logic/                  ← Business logic
│   ├── board_map.py        ← Coordinate conversion
│   ├── move_planner.py     ← Movement planning
│   └── profiles.py         ← Settings management
│
├── CLAUDE DOCS CHESS MOVER/ ← Complete documentation
│   ├── 00_READ_ME_FIRST.md
│   ├── MASTER_WORKFLOW.md
│   ├── ARCHITECTURE_PATTERNS.md
│   └── ... (more docs)
│
└── requirements.txt        ← Python dependencies
```

---

## 🔧 Current Capabilities (Phase 1)

### ✅ What Works Now:
- Connect to Falcon gantry via USB/serial
- Detect available COM ports automatically
- Click chess squares to move gantry to position
- Configure board dimensions and origin
- Test path to verify calibration
- Save/load settings from YAML
- Live command logging

### 🔄 Next Features (Future Phases):
- **Phase 2:** Raspberry Pi deployment
- **Phase 3:** Servo gripper and lift control
- Live position display on board
- G54 work offset support
- Multiple board profiles
- Path planning for piece moves

---

## 🆘 Quick Troubleshooting

### "No COM ports found"
**→ Falcon not plugged in** - Connect USB cable and wait 5 seconds

### "Connection failed"
**→ Wrong port** - Check Device Manager for correct COM#
**→ Port in use** - Close other programs (Arduino IDE, etc.)

### Gantry moves to wrong squares
**→ Calibration off** - Verify Origin X/Y and board dimensions
**→ Run Test Path** - See if pattern makes sense, adjust accordingly

### Application won't start
**→ Python not installed** - Install Python 3.11+ from python.org
**→ Dependencies missing** - Run: `pip install -r requirements.txt`

See **QUICK_START.md** for detailed troubleshooting.

---

## 📚 Documentation

### For Daily Use:
- **QUICK_START.md** - Setup and usage guide
- **This file** - Launch instructions

### For Development:
- **CLAUDE DOCS CHESS MOVER/** folder contains:
  - Complete architecture documentation
  - Testing strategies
  - Hardware control patterns
  - Library registry
  - Deployment guides

---

## 🎮 Example Workflow

```
1. Plug in Falcon → Wait 5 seconds
2. Double-click launch.bat
3. Click "Settings"
4. Select COM port → Click "Save"
5. Click "Connect"
6. Click "Home" (gantry homes)
7. Place chessboard under gantry
8. Click "Test Path" to verify calibration
9. Click any square → Gantry moves there!
```

---

## 🔐 Safety Notes

**This controls physical hardware!**

- ✅ Keep emergency stop accessible
- ✅ Start with slow feed rates (1000-2000 mm/min)
- ✅ Clear work area before testing
- ✅ Monitor first movements closely
- ✅ Use Test Path before clicking squares

**Emergency Stop:** Click "Disconnect" or send `!` command

---

## 🚀 Ready to Go!

Everything is set up and ready to use. Just:

1. **Plug in your Falcon**
2. **Double-click `launch.bat`**
3. **Follow the connection steps above**

For detailed help, see **QUICK_START.md**

**Enjoy your Chess Mover Machine!** 🤖♟️
