# Chess Mover – Control App (Windows first, then Raspberry Pi)

This app gives you a LightBurn-like workspace for a *chessboard*. Click squares to move the Falcon gantry there. Phase 1 is **Windows only** (no servos). Then deploy the same code to a **Raspberry Pi**.

---

## 0) Hardware Assumptions
- Creality Falcon laser engraver (controller speaks GRBL over USB)
- Falcon connected by USB to your Windows PC (Phase 1)
- Chessboard placed under the gantry (eye-ball alignment is fine for now)

---

## 1) Windows – Setup & Run

### Install Python (3.11+ recommended)
- Install from python.org; during install, check **Add Python to PATH**.

### Project layout
```
chess_mover/
  main.py
  requirements.txt
  config/settings.yaml
  ui/... controllers/... logic/...
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Plug in Falcon and find COM port
- Open **Device Manager → Ports (COM & LPT)**, note COM number (e.g., COM4).

### Launch the app
```bash
python main.py
```

### First run checklist
1. Click **Settings** → choose your **COM port** and **baud 115200**. Optionally set board width/height.
2. Click **Connect**. You should see `Grbl 1.1...` lines in the log shortly after.
3. Click **Home** to home the gantry (`$H`).
4. Click anywhere on the board canvas — the head should move to that square’s center.
5. Use **Test Path** to visit corners + center.

> If motion is mirrored: swap your origin values (origin X/Y) or rotate the board 180° for testing. Later add a checkbox to invert axes.

---

## 2) Calibrating Board Dimensions (Easy 3-Step Method!)

**New! Quick Calibration Feature:**
1. Click **Connect** → **Home** to home the machine
2. Jog the head to center of square A1 using arrow buttons
3. Click **📍 Set Current Position as A1** button
4. Done! ✓

See [CALIBRATION_GUIDE.md](CALIBRATION_GUIDE.md) for detailed instructions.

**Manual calibration (advanced):**
- Enter board dimensions in **Settings**
- Manually enter Origin X/Y coordinates
- See guide for details

---

## 3) Profile Management (Multi-Board Support) ⭐ NEW!

**Multiple Board Profiles:**
- Save calibrations for different boards (tournament, travel, practice)
- Switch between profiles instantly via toolbar dropdown
- Each profile stores:
  - Board dimensions and calibration
  - Piece dimensions (for future gripper)

**Quick Start:**
1. **Settings → Manage Profiles** to create/edit profiles
2. Use toolbar dropdown to switch between boards
3. Calibrate each profile once - never recalibrate again!

See [PROFILE_MANAGEMENT_GUIDE.md](PROFILE_MANAGEMENT_GUIDE.md) for complete guide.

**Default profile:** "Default Board" (400mm standard chess)

---

## 4) Raspberry Pi Deployment (Phase 2) ⭐ READY!

**Full offline operation with Stockfish chess engine!**

The Chess Mover Machine runs perfectly on Raspberry Pi with complete offline capabilities:

### 🏠 Offline Features:
- ✅ **Stockfish integration** - Best move suggestions without internet
- ✅ **Position analysis** - Evaluate any chess position
- ✅ **PGN replay** - Play through games offline
- ✅ **Multi-game support** - Load and analyze multiple games
- ✅ **Auto-start on boot** - Machine ready when Pi boots
- ✅ **VNC remote access** - Control from any computer

### 📦 Quick Setup:
```bash
# 1. Flash Pi OS and update
sudo apt update && sudo apt upgrade -y

# 2. Install Stockfish (offline chess engine)
sudo apt install -y stockfish

# 3. Clone project and install dependencies
git clone <your-repo-url> ~/chess_mover
cd ~/chess_mover
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure serial port
# Edit config/settings.yaml → serial.port: "/dev/ttyUSB0"

# 5. Run!
python main.py
```

### 📖 Complete Setup Guide:
See [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) for:
- Complete Raspberry Pi OS setup
- Stockfish installation & compilation
- Hardware connections (GRBL + servos)
- Auto-start configuration
- VNC remote access
- Performance optimization
- Troubleshooting guide

---

## 5) Next Steps – Servos (Phase 3)
- On Windows we left stubs in `controllers/servo_controller.py`.
- On Pi, replace stubs with real PCA9685 or GPIO control and power the servos from a 6V LM2596 buck.
- Keep **common ground** between Falcon, Pi, and servo rail.

Suggested libraries (Pi):
- `adafruit-circuitpython-pca9685`
- `adafruit-circuitpython-servokit`

Implement:
- `lift_up()`, `lift_down()`, `grip_open()`, `grip_close()` with calibrated angles.

---

## 6) Chess Automation & Game Integration ⭐ NEW!

### ♟️ Automated Chess Game Replay
Load and replay famous chess games on your physical board!

**Features:**
- ✅ Load PGN files from chess.com, lichess, or any source
- ✅ Step through games move-by-move
- ✅ Auto-play with configurable speed
- ✅ Full move validation (castling, en passant, promotion)
- ✅ Automatic capture handling
- ✅ Complete chess rule engine

**Quick Start:**
1. Open Game Panel
2. Load PGN file or paste PGN text
3. Click Play and watch the magic!

See [CHESS_AUTOMATION_GUIDE.md](CHESS_AUTOMATION_GUIDE.md) for complete guide.

### ⚡ TacticsQuest Integration (Correspondence Chess)
Sync your online correspondence games to the physical board!

**Features:**
- ✅ Automatic opponent move execution on physical board
- ✅ Configurable polling (Active, Home, Away, Work, Sleep modes)
- ✅ Online/offline mode toggle
- ✅ Multi-game support
- ✅ Secure authorization (davidljones88@yahoo.com only)

**How it works:**
1. Connect to TacticsQuest Supabase
2. Enable sync for correspondence games
3. Opponent makes move in TacticsQuest app
4. Machine automatically executes move on physical board!

See [TACTICSQUEST_INTEGRATION_GUIDE.md](TACTICSQUEST_INTEGRATION_GUIDE.md) for setup & usage.

---

## 7) Features & Improvements

### ✅ Implemented:
- ✅ **Quick calibration**: Set current position as A1 center (no manual measurement!)
- ✅ **Profile manager UI**: Create, edit, switch between multiple board profiles
- ✅ **Speed limiting**: Configurable min/max speeds with automatic clamping
- ✅ **Safety features**: Emergency stop, position validation, health monitoring
- ✅ **Auto-reconnect**: Automatically reconnects if connection lost
- ✅ **Real-time position tracking**: Live position updates from GRBL
- ✅ **Piece dimension storage**: Ready for future gripper integration
- ✅ **Chess game automation**: PGN replay, move validation, auto-play
- ✅ **TacticsQuest sync**: Online correspondence game integration
- ✅ **Stockfish integration**: Offline chess analysis and best moves
- ✅ **Raspberry Pi ready**: Complete Pi deployment guide

### 📚 Documentation:
- [CALIBRATION_GUIDE.md](CALIBRATION_GUIDE.md) - Board calibration walkthrough
- [PROFILE_MANAGEMENT_GUIDE.md](PROFILE_MANAGEMENT_GUIDE.md) - Multi-board setup guide
- [PROFILE_SYSTEM_SUMMARY.md](PROFILE_SYSTEM_SUMMARY.md) - Technical implementation details
- [CHESS_AUTOMATION_GUIDE.md](CHESS_AUTOMATION_GUIDE.md) - Chess game automation guide
- [TACTICSQUEST_INTEGRATION_GUIDE.md](TACTICSQUEST_INTEGRATION_GUIDE.md) - Online game sync guide
- [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) - Complete Pi deployment guide
- [IMPROVEMENTS_COMPLETE.md](IMPROVEMENTS_COMPLETE.md) - Full feature list
- [QUICK_WINS_GUIDE.md](QUICK_WINS_GUIDE.md) - 45-minute integration guide

### 🎯 Future Ideas:
- **Invert axis checkboxes**: Handle machine orientation
- **Live position dot**: Show head position on canvas
- **Path preview**: Draw travel lines before executing
- **Import/Export profiles**: Share calibrations
- **Computer vision**: Auto-detect board size
