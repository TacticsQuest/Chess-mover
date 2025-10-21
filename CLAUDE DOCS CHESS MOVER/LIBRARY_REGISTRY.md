# LIBRARY REGISTRY - Chess Mover Machine
**Version:** 1.0.0
**Last Updated:** 2025-01-18
**Purpose:** Python hardware libraries for robotics/CNC control

---

## 📚 CURRENT DEPENDENCIES

### Production Dependencies

| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| **pyserial** | 3.5+ | Serial/USB communication with GRBL | ✅ Required |
| **PyYAML** | 6.0.2+ | Config file parsing (settings.yaml) | ✅ Required |

### Development Dependencies

| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| **pytest** | 7.4+ | Unit testing framework | ✅ Recommended |
| **pytest-mock** | 3.12+ | Mocking for tests | ✅ Recommended |
| **black** | 23+ | Code formatting | 🟡 Optional |
| **mypy** | 1.7+ | Static type checking | 🟡 Optional |
| **flake8** | 6.1+ | Linting | 🟡 Optional |

---

## 🔮 FUTURE DEPENDENCIES (Phase 3 - Servos)

### Raspberry Pi Only

| Library | Version | Purpose | When |
|---------|---------|---------|------|
| **adafruit-circuitpython-pca9685** | Latest | PWM servo control via PCA9685 | Phase 3 |
| **RPi.GPIO** | Latest | Raspberry Pi GPIO access | Phase 3, Pi only |
| **adafruit-circuitpython-servokit** | Latest | Higher-level servo API | Phase 3, Alternative |

**Installation (Raspberry Pi):**
```bash
# On Raspberry Pi only
pip3 install adafruit-circuitpython-pca9685
pip3 install RPi.GPIO
```

---

## 🐍 PYTHON VERSION

**Required:** Python 3.11+
**Current:** Python 3.12.10 ✅

**Why 3.11+:**
- Modern type hints (`tuple[float, float]` instead of `Tuple[float, float]`)
- Improved error messages
- Performance improvements
- Raspberry Pi OS now ships with 3.11+

---

## 📦 LIBRARY DETAILS

### pyserial (Critical)

**Purpose:** Serial communication with GRBL controller

**Key Features:**
- Cross-platform (Windows/Linux/macOS)
- USB serial port abstraction
- Timeout handling
- Buffer management

**Usage:**
```python
import serial

ser = serial.Serial('COM4', 115200, timeout=5.0)
ser.write(b'$H\n')  # Send homing command
response = ser.readline().decode()
```

**Documentation:** https://pyserial.readthedocs.io/

---

### PyYAML (Critical)

**Purpose:** Parse settings.yaml configuration file

**Usage:**
```python
import yaml

with open('config/settings.yaml', 'r') as f:
    config = yaml.safe_load(f)

print(config['serial']['port'])  # COM4
print(config['board']['width'])  # 400
```

**Documentation:** https://pyyaml.org/wiki/PyYAMLDocumentation

---

### Tkinter (Built-in)

**Purpose:** Cross-platform GUI framework

**Status:** Ships with Python (no installation needed)

**Why Tkinter:**
- ✅ Built-in (no dependencies)
- ✅ Cross-platform (Windows, Linux, macOS)
- ✅ Lightweight
- ✅ Good enough for control apps
- ✅ Works on Raspberry Pi

**Alternatives considered:**
- PyQt5/PyQt6 - More powerful but large dependency
- Kivy - Overkill for desktop app
- Web UI (Flask + HTML) - Future option

---

## 🚫 LIBRARIES TO AVOID

### Arduino/Firmata
❌ **Don't use:** Arduino libraries for Python

**Why:** GRBL already handles low-level control. Don't bypass GRBL to talk directly to Arduino.

### Serial Alternatives (e.g., minimalmodbus)
❌ **Don't use:** Other serial libraries

**Why:** pyserial is the standard, well-maintained, and works everywhere.

---

## 🔧 OPTIONAL TOOLS

### Development Tools

```bash
# Code formatting
pip install black
black chess_mover/

# Type checking
pip install mypy
mypy chess_mover/

# Linting
pip install flake8
flake8 chess_mover/

# Testing
pip install pytest pytest-mock
pytest tests/
```

### GRBL Simulators

**GRBL Simulator (for testing without hardware):**
- GitHub: https://github.com/grbl/grbl-sim
- Build instructions for testing GRBL responses
- Not needed initially (we use mock classes)

---

## 📊 DEPENDENCY MANAGEMENT

### requirements.txt

```
# Production dependencies
pyserial>=3.5
pyyaml>=6.0.2

# Development dependencies (optional)
pytest>=7.4
pytest-mock>=3.12
black>=23.0
mypy>=1.7
flake8>=6.1
```

### Installing Dependencies

```bash
# Windows (current)
pip install -r requirements.txt

# Raspberry Pi (future)
pip3 install -r requirements.txt
```

### Checking for Updates

```bash
# List outdated packages
pip list --outdated

# Update specific package
pip install --upgrade pyserial
```

---

## 🔐 SECURITY

### Vulnerability Scanning

```bash
# Install safety
pip install safety

# Check for known vulnerabilities
safety check

# Check specific requirements file
safety check -r requirements.txt
```

**Current Status:** No known vulnerabilities in pyserial or PyYAML

---

## 🎯 LIBRARY SELECTION CRITERIA

Before adding ANY new library:

### Questions to Ask:
1. **Is it necessary?** Can we solve this with stdlib?
2. **Is it maintained?** Last update < 6 months?
3. **Is it cross-platform?** Works on Windows + Linux?
4. **Is it lightweight?** < 10MB installed size?
5. **Is it well-documented?** Good docs + examples?
6. **Is it secure?** No known CVEs?

### Approval Process:
1. Search PyPI: https://pypi.org/
2. Check GitHub: Stars, issues, last commit
3. Check documentation quality
4. Test on Windows first
5. Verify works on Raspberry Pi
6. Add to requirements.txt

---

## 📚 STANDARD LIBRARY USAGE

**Prefer stdlib when possible:**

```python
# ✅ Use built-in libraries
import logging      # Logging
import json         # JSON parsing
import pathlib      # File paths
import time         # Timing/delays
import threading    # Background tasks
import queue        # Thread-safe queues
import dataclasses  # Data structures
import enum         # Enumerations
import typing       # Type hints
```

---

## 🔄 UPDATE SCHEDULE

**Check for updates:**
- **Weekly** during active development
- **Monthly** during maintenance
- **Before deployment** to Raspberry Pi

**Update command:**
```bash
pip list --outdated
pip install --upgrade <package>
```

---

## 🎓 LEARNING RESOURCES

### pyserial
- Official docs: https://pyserial.readthedocs.io/
- Tutorial: https://pyserial.readthedocs.io/en/latest/shortintro.html

### Tkinter
- Python docs: https://docs.python.org/3/library/tkinter.html
- Tutorial: https://realpython.com/python-gui-tkinter/

### GRBL
- GRBL Wiki: https://github.com/grbl/grbl/wiki
- G-code Reference: https://linuxcnc.org/docs/html/gcode.html

### Raspberry Pi GPIO (Phase 3)
- RPi.GPIO docs: https://sourceforge.net/projects/raspberry-gpio-python/
- Adafruit guides: https://learn.adafruit.com/

---

**Remember:** Keep dependencies minimal. Every library is a maintenance burden!
