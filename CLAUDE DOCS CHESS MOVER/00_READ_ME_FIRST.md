# 00 - READ ME FIRST (Chess Mover Machine)
**Version:** 1.0.0
**Last Updated:** 2025-01-18
**Purpose:** Session initialization for Chess Mover Machine hardware control project

---

## ⚠️ **CRITICAL - READ AT SESSION START**

**When:** At the beginning of EVERY new conversation/session about Chess Mover Machine

**Why:** Ensures you understand this is a **hardware control project**, not a web app

---

## 📋 PROJECT OVERVIEW

**Chess Mover Machine** is a hardware control application that converts a Creality Falcon laser engraver into a chess piece moving robot.

### Project Type
- **NOT a web app** - Desktop application with hardware control
- **NOT a game** - Control system for physical hardware
- **IS a robotics/CNC control application**

### Technology Stack
```yaml
Language: Python 3.11+
GUI: Tkinter (built-in)
Hardware: GRBL over USB serial
Config: YAML files
Platform: Windows (Phase 1) → Raspberry Pi (Phase 2)
```

---

## 🎯 PROJECT PHASES

### Phase 1: Windows Development ✅ Current
- Tkinter GUI for board visualization
- GRBL communication over serial (USB)
- Click-to-move functionality
- Calibration system for board alignment
- **No servos yet** - just gantry movement

### Phase 2: Raspberry Pi Deployment
- Deploy same code to Raspberry Pi
- Connect Falcon via USB to Pi
- VNC or local display for UI

### Phase 3: Servo Control
- Add gripper servo (open/close)
- Add lift servo (up/down)
- Integrate with PCA9685 PWM controller
- Complete piece moving capability

---

## 🗂️ DOCUMENT INDEX

### Core Workflow (Tailored for Hardware Control)
| Document | Purpose |
|----------|---------|
| [**MASTER_WORKFLOW.md**](MASTER_WORKFLOW.md) | Hardware project workflow |
| [**ARCHITECTURE_PATTERNS.md**](ARCHITECTURE_PATTERNS.md) | Python/Tkinter/GRBL patterns |
| [**LIBRARY_REGISTRY.md**](LIBRARY_REGISTRY.md) | Python hardware libraries |
| [**TESTING_GUIDE.md**](TESTING_GUIDE.md) | Hardware testing strategies |
| [**DEPLOYMENT.md**](DEPLOYMENT.md) | Windows & Raspberry Pi deployment |

---

## 🔑 KEY DIFFERENCES FROM WEB APPS

### What's Different
- ❌ **No database** - Uses YAML config files
- ❌ **No authentication** - Single-user desktop app
- ❌ **No API endpoints** - Direct hardware control
- ❌ **No React/Next.js** - Python Tkinter GUI
- ❌ **No Supabase** - Local file-based storage

### What's Important
- ✅ **Serial communication** - GRBL protocol over USB
- ✅ **Coordinate transformation** - Chess squares → machine coordinates
- ✅ **Safety checks** - Bounds validation, emergency stop
- ✅ **Hardware state** - Track gantry position, connection status
- ✅ **Calibration** - Physical board alignment
- ✅ **Error handling** - Serial timeouts, GRBL errors

---

## 🚀 HARDWARE ARCHITECTURE

```
User Clicks Square (Tkinter)
         ↓
Coordinate Converter (chess coords → machine coords)
         ↓
Path Planner (validate bounds, safety)
         ↓
GRBL Controller (serial commands)
         ↓
Falcon Gantry (physical movement)
```

---

## 🔧 CURRENT PROJECT STRUCTURE

```
Chess Mover Machine/
├── main.py                    # Entry point (Tkinter app)
├── requirements.txt           # pyserial, pyyaml
├── config/
│   └── settings.yaml         # COM port, board dimensions, profiles
├── ui/                       # Tkinter GUI components
│   └── ...
├── controllers/              # Hardware control
│   ├── grbl_controller.py   # Serial/GRBL communication
│   └── servo_controller.py  # Servo stubs (Phase 3)
├── logic/                    # Business logic
│   └── ...
└── CLAUDE DOCS CHESS MOVER/ # This documentation
```

---

## 🎯 TYPICAL WORKFLOW

When starting a new feature:

1. **Read MASTER_WORKFLOW.md** - Hardware-specific workflow
2. **Check ARCHITECTURE_PATTERNS.md** - Python/Tkinter patterns
3. **Check LIBRARY_REGISTRY.md** - Available Python libraries
4. **Follow hardware safety principles:**
   - Always validate coordinates before sending to GRBL
   - Implement emergency stop functionality
   - Handle serial disconnections gracefully
   - Test with mock/simulated hardware first

---

## 🚨 CRITICAL REMINDERS

### Hardware Safety
- ✅ **Bounds checking** - Never send out-of-range coordinates
- ✅ **Connection validation** - Check serial port before sending commands
- ✅ **Error recovery** - Handle GRBL errors without crashing
- ✅ **Emergency stop** - Implement abort/kill functionality
- ✅ **Safe defaults** - Conservative speeds, soft limits

### Code Quality
- ✅ **Separation of concerns** - UI ← Logic ← Hardware
- ✅ **Mock hardware** - Test without physical gantry
- ✅ **Error logging** - Comprehensive logging for debugging
- ✅ **Configuration** - All hardware params in YAML
- ✅ **Cross-platform** - Code works on Windows & Raspberry Pi

---

## 📚 DEPENDENCIES

**Current (requirements.txt):**
```
pyserial>=3.5        # Serial communication with GRBL
pyyaml>=6.0.2        # Config file parsing
```

**Future (Phase 3 - Servos):**
```
adafruit-circuitpython-pca9685  # PWM servo control
RPi.GPIO                         # Raspberry Pi GPIO (Pi only)
```

---

## 🔍 WHEN YOU'RE UNSURE

**Priority order:**
1. Check relevant doc in this folder
2. Check GRBL documentation (https://github.com/grbl/grbl/wiki)
3. Ask user for clarification

**Never:**
- Assume web app patterns apply
- Skip hardware safety checks
- Send untested commands to physical hardware

---

## ✅ SESSION START CONFIRMATION

After reading this, you should know:
- ✅ This is a **hardware control project**, not a web app
- ✅ Tech stack is **Python + Tkinter + GRBL**
- ✅ Focus is on **safety, calibration, and hardware abstraction**
- ✅ Testing uses **mocks/simulators** before real hardware
- ✅ Deployment targets **Windows & Raspberry Pi**

**Now you're ready to work on Chess Mover Machine!** 🤖

---

**Current Status (Phase 1):**
- Basic Tkinter UI with board canvas ✅
- GRBL connection and homing ✅
- Click-to-move functionality ✅
- Settings dialog for COM port & calibration ✅
- Test path functionality ✅

**Next Steps:**
- Refine calibration workflow
- Add live position display
- Implement G54 work offset
- Prepare for servo integration (Phase 3)
