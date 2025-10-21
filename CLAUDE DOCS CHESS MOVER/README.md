# Claude Code Documentation - Chess Mover Machine
**Version:** 1.0.0
**Created:** 2025-01-18
**Purpose:** Hardware control project workflow for Chess Mover Machine

---

## 🚀 QUICK START

**New to this project?** → Read [00_READ_ME_FIRST.md](00_READ_ME_FIRST.md)

**Starting a new feature?** → Follow [MASTER_WORKFLOW.md](MASTER_WORKFLOW.md)

**Writing code?** → Check [ARCHITECTURE_PATTERNS.md](ARCHITECTURE_PATTERNS.md)

---

## 📚 DOCUMENTATION INDEX

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [**00_READ_ME_FIRST.md**](00_READ_ME_FIRST.md) | Session initialization | **Every new session** |
| [**MASTER_WORKFLOW.md**](MASTER_WORKFLOW.md) | Development workflow | Starting any feature |
| [**ARCHITECTURE_PATTERNS.md**](ARCHITECTURE_PATTERNS.md) | Code structure & patterns | While coding |
| [**LIBRARY_REGISTRY.md**](LIBRARY_REGISTRY.md) | Python dependencies | Before adding libraries |
| [**TESTING_GUIDE.md**](TESTING_GUIDE.md) | Testing strategies | Before/after coding |

---

## 🎯 PROJECT OVERVIEW

**Chess Mover Machine** converts a Creality Falcon laser engraver into a chess piece moving robot.

### Technology Stack
```yaml
Language: Python 3.12.10
GUI: Tkinter (built-in)
Hardware: GRBL over USB serial
Config: YAML files
Platform: Windows → Raspberry Pi
```

### Project Phases
1. **Phase 1 (Current):** Windows GUI with gantry control
2. **Phase 2:** Deploy to Raspberry Pi
3. **Phase 3:** Add servo gripper control

---

## 🔑 KEY DIFFERENCES FROM WEB APPS

This is **NOT a web application**. It's a **hardware control system**.

### What's Different
- ❌ No database (uses YAML config)
- ❌ No authentication (single-user desktop app)
- ❌ No API endpoints (direct hardware control)
- ❌ No React/Next.js (Python Tkinter)

### What's Critical
- ✅ Serial communication (GRBL protocol)
- ✅ Coordinate transformation (chess → machine)
- ✅ Safety checks (bounds validation)
- ✅ Hardware state management
- ✅ Error handling (timeouts, disconnections)

---

## 🏗️ PROJECT STRUCTURE

```
Chess Mover Machine/
├── main.py                      # Entry point
├── requirements.txt             # pyserial, pyyaml
│
├── config/
│   └── settings.yaml           # COM port, board dimensions
│
├── ui/                         # Tkinter GUI
│   ├── main_window.py
│   ├── board_canvas.py
│   └── settings_dialog.py
│
├── controllers/                # Hardware control
│   ├── grbl_controller.py     # Serial/GRBL
│   └── servo_controller.py     # Servos (Phase 3)
│
├── logic/                      # Business logic
│   ├── coordinate_converter.py
│   ├── path_planner.py
│   └── state_manager.py
│
├── tests/                      # Testing
│   ├── mock_grbl.py           # Mock controller
│   ├── test_coordinates.py
│   └── test_integration.py
│
└── CLAUDE DOCS CHESS MOVER/   # This documentation
```

---

## 🎓 WORKFLOW SUMMARY

### Starting a New Feature

1. **Read** [MASTER_WORKFLOW.md](MASTER_WORKFLOW.md)
2. **Understand** hardware requirements
3. **Design** with safety in mind
4. **Mock** hardware first
5. **Implement** with layers separated
6. **Test** with mocks, then hardware
7. **Document** changes

### Code Quality Standards

- **Max 300 lines per file** - Break into modules if larger
- **Type hints required** - All functions typed
- **Docstrings required** - Explain WHY, not just WHAT
- **No hardcoded values** - Use config/settings.yaml
- **Safety first** - Validate before sending to hardware

---

## 🚨 CRITICAL SAFETY RULES

### ALWAYS
- ✅ Validate coordinates before sending to GRBL
- ✅ Implement emergency stop mechanism
- ✅ Handle serial disconnections gracefully
- ✅ Test with mocks before physical hardware
- ✅ Log all commands and errors

### NEVER
- ❌ Send untested commands to hardware
- ❌ Skip bounds checking
- ❌ Assume serial connection is stable
- ❌ Mix UI and hardware logic
- ❌ Hardcode COM ports or dimensions

---

## 📖 LEARNING PATH

### New to Hardware Control?

1. **Start here:** [00_READ_ME_FIRST.md](00_READ_ME_FIRST.md)
2. **Understand GRBL:** https://github.com/grbl/grbl/wiki
3. **Learn pyserial:** https://pyserial.readthedocs.io/
4. **Review architecture:** [ARCHITECTURE_PATTERNS.md](ARCHITECTURE_PATTERNS.md)
5. **Run mock tests:** [TESTING_GUIDE.md](TESTING_GUIDE.md)

### Experienced Developer?

- Read [MASTER_WORKFLOW.md](MASTER_WORKFLOW.md) for workflow
- Check [ARCHITECTURE_PATTERNS.md](ARCHITECTURE_PATTERNS.md) for code patterns
- Review existing code structure
- Start with mock testing

---

## 🔧 DEPENDENCIES

**Current (Phase 1):**
```
pyserial>=3.5        # Serial communication
pyyaml>=6.0.2        # Config parsing
```

**Future (Phase 3 - Servos):**
```
adafruit-circuitpython-pca9685  # PWM servo control
RPi.GPIO                         # Raspberry Pi GPIO
```

**Installation:**
```bash
pip install -r requirements.txt
```

---

## 🧪 TESTING

**Three-tier testing:**

1. **Unit Tests (Mock)** - Fast, safe, no hardware
   ```bash
   pytest tests/ -v
   ```

2. **Integration Tests (Mock)** - Full workflow, no hardware
   ```bash
   pytest tests/test_integration.py -v
   ```

3. **Hardware Tests (Physical)** - Manual verification only
   ```bash
   python tests/test_hardware.py  # Run manually
   ```

**Read more:** [TESTING_GUIDE.md](TESTING_GUIDE.md)

---

## 📚 EXTERNAL RESOURCES

### GRBL
- **GRBL Wiki:** https://github.com/grbl/grbl/wiki
- **G-code Reference:** https://linuxcnc.org/docs/html/gcode.html

### Python
- **pyserial:** https://pyserial.readthedocs.io/
- **Tkinter:** https://docs.python.org/3/library/tkinter.html
- **pytest:** https://docs.pytest.org/

### Raspberry Pi (Phase 2)
- **Pi Imager:** https://www.raspberrypi.com/software/
- **GPIO Guide:** https://learn.adafruit.com/

---

## 🎯 CURRENT STATUS (Phase 1)

### Completed ✅
- Basic Tkinter UI with board visualization
- GRBL serial connection
- Homing functionality
- Click-to-move on board canvas
- Settings dialog for configuration
- Test path functionality

### Next Steps 🔄
- Refine calibration workflow
- Add live position display
- Implement G54 work offset
- Improve error handling
- Add comprehensive logging

### Future (Phase 2)
- Deploy to Raspberry Pi
- Systemd service setup
- VNC access

### Future (Phase 3)
- Integrate PCA9685 servo controller
- Implement gripper control
- Implement lift mechanism
- Complete piece-moving capability

---

## 💬 WHEN YOU NEED HELP

**Priority order:**
1. Check relevant doc in this folder
2. Check GRBL documentation
3. Review existing code for patterns
4. Ask user for clarification

**Never:**
- Guess at hardware behavior
- Skip safety checks
- Assume web app patterns apply

---

## ✅ SESSION CHECKLIST

At the start of each session:

- [ ] Read [00_READ_ME_FIRST.md](00_READ_ME_FIRST.md)
- [ ] Understand current phase (Phase 1: Windows)
- [ ] Know the tech stack (Python + Tkinter + GRBL)
- [ ] Remember: Safety first, test with mocks
- [ ] Check [MASTER_WORKFLOW.md](MASTER_WORKFLOW.md) for process

---

## 📝 MAINTENANCE

**Update these docs when:**
- Adding new hardware (Phase 3 servos)
- Changing architecture patterns
- Adding new dependencies
- Discovering better workflows

**How to update:**
1. User must explicitly request: "Update the Claude DOCS"
2. Only then modify documentation
3. Update version numbers
4. Document what changed

---

**Built for:** Chess Mover Machine hardware control project
**Maintained by:** Claude Code (with user approval for updates)
**Purpose:** Ensure consistent, safe hardware control development

---

🤖 **Ready to build!** Start with [MASTER_WORKFLOW.md](MASTER_WORKFLOW.md)
