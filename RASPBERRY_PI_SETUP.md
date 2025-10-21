# Raspberry Pi Setup Guide - Chess Mover Machine

**Complete guide for deploying Chess Mover Machine to Raspberry Pi with offline capabilities!**

---

## 🎯 Overview

This guide covers setting up the Chess Mover Machine on Raspberry Pi, including:
- ✅ Python environment setup
- ✅ Stockfish installation for offline chess analysis
- ✅ Hardware connections (GRBL gantry + servos)
- ✅ Auto-start on boot
- ✅ VNC access for remote control
- ✅ Offline operation (no internet required)

---

## 📦 Hardware Requirements

### Required:
- **Raspberry Pi** (Pi 4 or Pi 5 recommended)
  - Minimum: Pi 3B+ (2GB RAM)
  - Recommended: Pi 4 (4GB+ RAM) or Pi 5
- **MicroSD Card** (32GB+ recommended)
- **Power Supply** (official Pi power supply recommended)
- **Creality Falcon** (GRBL gantry, connected via USB)
- **Servo Controller** (PCA9685 or GPIO)
- **2x Servos** (lift + gripper, 6V recommended)
- **Buck Converter** (LM2596 for servo power)

### Optional:
- 7" Touchscreen display (for standalone operation)
- USB keyboard + mouse
- Case with cooling fan

---

## 🔧 Part 1: Raspberry Pi OS Setup

### Step 1: Flash Raspberry Pi OS

**Download Raspberry Pi Imager**:
- From: https://www.raspberrypi.com/software/

**Flash OS**:
1. Insert microSD card into computer
2. Open Raspberry Pi Imager
3. Choose OS: **Raspberry Pi OS (64-bit)** (Full or Lite)
   - **Full**: Includes desktop (recommended for beginners)
   - **Lite**: Headless setup (advanced users)
4. Choose Storage: Select your microSD card
5. Click **Settings** (gear icon):
   - ✅ Set hostname: `chessmover`
   - ✅ Enable SSH
   - ✅ Set username/password
   - ✅ Configure WiFi
   - ✅ Set locale
6. Click **Write**

### Step 2: First Boot

1. Insert microSD into Raspberry Pi
2. Connect power
3. Wait for boot (first boot takes 2-3 minutes)

**If using display:**
- Boot directly to desktop
- Open Terminal

**If headless (no display):**
```bash
# Find Pi IP address
# Check router admin page or use:
nmap -sn 192.168.1.0/24

# SSH into Pi
ssh pi@chessmover.local
# Or: ssh pi@<ip-address>
```

### Step 3: Update System

```bash
# Update package list
sudo apt update

# Upgrade all packages
sudo apt upgrade -y

# Install essential tools
sudo apt install -y git python3-pip python3-venv

# Reboot
sudo reboot
```

---

## 🐍 Part 2: Python Environment Setup

### Step 1: Create Virtual Environment

```bash
# Create project directory
mkdir -p ~/chess_mover
cd ~/chess_mover

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Step 2: Clone Project

```bash
# Clone from your repository
git clone <your-repo-url> .

# Or copy files manually via SCP/SFTP
```

### Step 3: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# If any packages fail on Pi, install system dependencies:
sudo apt install -y python3-dev python3-tk python3-pil python3-pil.imagetk
```

**Common packages in requirements.txt:**
```
pyserial>=3.5
pyyaml>=6.0
python-chess>=1.10.0
supabase>=2.0.0
Pillow>=10.0.0
```

**For servo control (PCA9685):**
```bash
pip install adafruit-circuitpython-pca9685
pip install adafruit-circuitpython-servokit
```

---

## ♟️ Part 3: Stockfish Installation (Offline Chess Analysis)

### Why Stockfish?
- Enables offline chess analysis
- Best move suggestions
- Position evaluation
- No internet required!

### Installation

**Method 1: Package Manager (Easiest)**
```bash
# Install Stockfish from apt
sudo apt install -y stockfish

# Verify installation
which stockfish
# Should output: /usr/bin/stockfish

# Test Stockfish
stockfish
# Type "quit" to exit
```

**Method 2: Download Latest Binary**
```bash
# Download latest Stockfish for ARM
cd ~/Downloads
wget https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish-ubuntu-x86-64-avx2.tar

# Extract
tar -xvf stockfish-ubuntu-x86-64-avx2.tar

# Move to system bin
sudo mv stockfish/stockfish-ubuntu-x86-64-avx2 /usr/local/bin/stockfish
sudo chmod +x /usr/local/bin/stockfish

# Verify
stockfish
```

**Method 3: Compile from Source (Most Powerful)**
```bash
# Install build tools
sudo apt install -y make g++ git

# Clone Stockfish
git clone https://github.com/official-stockfish/Stockfish.git
cd Stockfish/src

# Compile for ARM (Raspberry Pi)
make -j4 ARCH=armv7  # Pi 3/4
# Or for Pi 5:
# make -j4 ARCH=armv8

# Install
sudo cp stockfish /usr/local/bin/
sudo chmod +x /usr/local/bin/stockfish

# Clean up
cd ~
rm -rf Stockfish
```

### Configure Chess Mover to Use Stockfish

The Chess Mover will auto-detect Stockfish at:
- `/usr/bin/stockfish`
- `/usr/local/bin/stockfish`
- `/usr/games/stockfish`

No configuration needed if installed via methods above!

---

## 🔌 Part 4: Hardware Connections

### GRBL Gantry (Creality Falcon)

**Connection:**
```
Falcon USB → Pi USB port
```

**Find Device:**
```bash
# List USB devices
ls /dev/tty*

# Expect: /dev/ttyUSB0 or /dev/ttyACM0

# Give user permission
sudo usermod -a -G dialout $USER
sudo reboot
```

**Configure in settings.yaml:**
```yaml
serial:
  port: "/dev/ttyUSB0"
  baud: 115200
```

### Servos (Lift + Gripper)

**Option A: PCA9685 I2C Servo Controller (Recommended)**

**Wiring:**
```
PCA9685 Board:
  VCC → Pi Pin 1 (3.3V)
  GND → Pi Pin 6 (GND)
  SDA → Pi Pin 3 (GPIO 2 - SDA)
  SCL → Pi Pin 5 (GPIO 3 - SCL)
  V+ → Buck converter output (6V)

Servos:
  Channel 0 (Lift):
    Signal → PCA9685 CH0
    Power → PCA9685 V+ / GND

  Channel 1 (Gripper):
    Signal → PCA9685 CH1
    Power → PCA9685 V+ / GND
```

**Enable I2C:**
```bash
# Enable I2C interface
sudo raspi-config
# → Interface Options → I2C → Enable

# Install I2C tools
sudo apt install -y i2c-tools

# Verify PCA9685 detected
i2cdetect -y 1
# Should show address 0x40
```

**Option B: Direct GPIO Control**

**Wiring:**
```
Lift Servo:
  Signal → GPIO 18 (Pin 12)
  Power → 6V rail
  Ground → Common ground

Gripper Servo:
  Signal → GPIO 19 (Pin 35)
  Power → 6V rail
  Ground → Common ground
```

**Configure in code:**
```python
# controllers/servo_controller.py
LIFT_PIN = 18
GRIPPER_PIN = 19
```

### Power Supply

**Critical: Common Ground!**
```
All devices must share common ground:
  - Raspberry Pi GND
  - Falcon GND (via USB)
  - Servo rail GND
  - Buck converter GND
```

**Servo Power:**
```
12V Input → LM2596 Buck Converter → 6V Output → Servo V+
                                                   ↓
                                            PCA9685 V+ terminal
```

---

## 🚀 Part 5: Running the Application

### Manual Start

```bash
cd ~/chess_mover
source venv/bin/activate
python main.py
```

### Auto-Start on Boot

**Create systemd service:**
```bash
sudo nano /etc/systemd/system/chessmover.service
```

**Add content:**
```ini
[Unit]
Description=Chess Mover Machine
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/chess_mover
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/pi/.Xauthority"
ExecStart=/home/pi/chess_mover/venv/bin/python /home/pi/chess_mover/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable service:**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start
sudo systemctl enable chessmover.service

# Start now
sudo systemctl start chessmover.service

# Check status
sudo systemctl status chessmover.service

# View logs
journalctl -u chessmover.service -f
```

---

## 🖥️ Part 6: Remote Access (VNC)

### Enable VNC Server

```bash
# Enable VNC via raspi-config
sudo raspi-config
# → Interface Options → VNC → Enable

# Or install manually
sudo apt install -y realvnc-vnc-server

# Set VNC resolution (headless mode)
sudo raspi-config
# → Display Options → VNC Resolution → 1920x1080
```

### Connect from Computer

1. **Download VNC Viewer**: https://www.realvnc.com/en/connect/download/viewer/
2. **Connect**: `chessmover.local:5900` or `<pi-ip>:5900`
3. **Login**: Use Pi username/password

Now you can control the Chess Mover UI remotely!

---

## 📊 Part 7: Performance Optimization

### Enable Hardware Acceleration

```bash
# Edit config
sudo nano /boot/firmware/config.txt

# Add/uncomment:
dtoverlay=vc4-kms-v3d
gpu_mem=128

# Reboot
sudo reboot
```

### Reduce CPU Usage

**For headless operation:**
```bash
# Disable desktop (saves RAM)
sudo raspi-config
# → System Options → Boot / Auto Login → Console

# Lightweight window manager
sudo apt install -y openbox
```

### Stockfish Performance

**Limit threads for Pi:**
```python
# In logic/stockfish_engine.py __init__:
self._send_command("setoption name Threads value 2")  # Pi has 4 cores, use 2
```

---

## 🧪 Part 8: Testing

### Test GRBL Connection

```bash
# Activate venv
cd ~/chess_mover
source venv/bin/activate

# Test serial connection
python -c "
import serial
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
print(ser.readline())  # Should show GRBL version
ser.close()
"
```

### Test Servos

```python
# Test PCA9685 servos
from adafruit_servokit import ServoKit
kit = ServoKit(channels=16)

# Test lift (channel 0)
kit.servo[0].angle = 90  # Mid position
kit.servo[0].angle = 0   # Down
kit.servo[0].angle = 180 # Up

# Test gripper (channel 1)
kit.servo[1].angle = 90  # Open
kit.servo[1].angle = 0   # Closed
```

### Test Stockfish

```bash
# Run Stockfish
stockfish

# In Stockfish prompt:
position startpos
go depth 10
quit
```

### Test Full Application

```bash
cd ~/chess_mover
source venv/bin/activate
python main.py

# Should see:
# - Window opens
# - Can connect to GRBL
# - Can home machine
# - Can move to squares
# - Stockfish available for analysis
```

---

## 🌐 Part 9: Offline Operation

### What Works Offline?

✅ **Fully Offline:**
- Board control and movement
- Chess game replay (PGN files)
- Stockfish analysis and suggestions
- Profile management
- Settings

❌ **Requires Internet:**
- TacticsQuest sync (correspondence games)
- Software updates

### Offline Chess Analysis

**Load PGN and get best moves:**
```python
from logic.game_controller import GameController
from logic.stockfish_engine import StockfishEngine

# Initialize
stockfish = StockfishEngine()
stockfish.start()

# Get best move for current position
fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
best_move = stockfish.get_best_move(fen)
print(f"Best move: {best_move}")  # e.g., "e7e5"

# Get top 3 moves
top_moves = stockfish.get_top_moves(fen, count=3)
for move, eval in top_moves:
    print(f"{move}: {eval:+.2f}")

stockfish.stop()
```

---

## 🔧 Part 10: Troubleshooting

### Issue: GRBL Not Connecting

**Check:**
```bash
# Verify device exists
ls /dev/ttyUSB*

# Check permissions
groups
# Should include "dialout"

# If not in dialout group:
sudo usermod -a -G dialout $USER
sudo reboot
```

### Issue: Servos Not Moving

**Check I2C:**
```bash
# Verify I2C enabled
sudo raspi-config
# → Interface Options → I2C → Enabled

# Detect PCA9685
i2cdetect -y 1
# Should show 0x40

# If not detected:
sudo reboot
```

**Check Power:**
- Verify 6V on servo rail
- Check common ground
- Ensure buck converter outputting 6V

### Issue: Stockfish Not Found

**Verify installation:**
```bash
which stockfish
stockfish --version

# If not found, reinstall:
sudo apt install -y stockfish
```

### Issue: Application Won't Start on Boot

**Check service status:**
```bash
sudo systemctl status chessmover.service

# View logs
journalctl -u chessmover.service -n 50

# Common fixes:
# 1. Wrong WorkingDirectory path
# 2. Virtual environment path incorrect
# 3. Display/X server not ready (add sleep to ExecStart)
```

### Issue: VNC Black Screen

**Fix:**
```bash
# Set resolution manually
sudo raspi-config
# → Display Options → VNC Resolution → 1920x1080

# Or edit config:
sudo nano /boot/firmware/config.txt
# Add: hdmi_force_hotplug=1

sudo reboot
```

---

## 📋 Part 11: Configuration Checklist

### Pre-Flight Checklist

Before deploying to Pi, ensure:

- [ ] Raspberry Pi OS flashed and updated
- [ ] SSH enabled and WiFi configured
- [ ] Python 3.11+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed (requirements.txt)
- [ ] Stockfish installed and verified
- [ ] GRBL gantry connected via USB
- [ ] `/dev/ttyUSB0` accessible (dialout group)
- [ ] Servos wired to PCA9685 or GPIO
- [ ] I2C enabled (for PCA9685)
- [ ] Common ground between all devices
- [ ] 6V servo power supply configured
- [ ] settings.yaml configured for Pi paths
- [ ] Application tested manually
- [ ] Auto-start service configured (optional)
- [ ] VNC enabled for remote access (optional)

### Recommended settings.yaml for Pi

```yaml
serial:
  port: "/dev/ttyUSB0"
  baud: 115200

board:
  width: 400.0
  height: 400.0
  files: 8
  ranks: 8
  origin_x: 50.0
  origin_y: 50.0

speed:
  feedrate: 3000
  min_speed: 500
  max_speed: 8000

stockfish:
  path: "/usr/bin/stockfish"
  skill_level: 20
  depth: 20
```

---

## 🚀 Part 12: Deployment Summary

### Quick Deployment Steps

```bash
# 1. Flash Pi OS with Imager (enable SSH, WiFi)

# 2. SSH into Pi
ssh pi@chessmover.local

# 3. Update system
sudo apt update && sudo apt upgrade -y

# 4. Install dependencies
sudo apt install -y git python3-pip python3-venv stockfish i2c-tools

# 5. Clone project
git clone <repo> ~/chess_mover
cd ~/chess_mover

# 6. Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 7. Install servo libraries (if using PCA9685)
pip install adafruit-circuitpython-pca9685 adafruit-circuitpython-servokit

# 8. Configure serial permissions
sudo usermod -a -G dialout $USER
sudo reboot

# 9. Enable I2C (for servos)
sudo raspi-config
# → Interface Options → I2C → Enable

# 10. Test application
cd ~/chess_mover
source venv/bin/activate
python main.py

# 11. Setup auto-start (optional)
# Follow Part 5 instructions

# 12. Done! 🎉
```

---

## ✅ Summary

**What You Can Do on Raspberry Pi:**

✅ Full chess board control (GRBL gantry)
✅ Servo control (lift + gripper)
✅ PGN game replay
✅ Offline chess analysis (Stockfish)
✅ Best move suggestions
✅ Position evaluation
✅ TacticsQuest sync (with internet)
✅ Multi-board profiles
✅ Auto-start on boot
✅ Remote access via VNC
✅ **Fully offline capable!**

**Stockfish Enables:**
- 🏠 Offline operation (no internet needed)
- 🧠 Best move suggestions
- 📊 Position evaluation
- 🎯 Move analysis
- 👨‍🏫 Training mode

**Hardware You Need:**
- Raspberry Pi 4/5 (or Pi 3B+)
- Creality Falcon (GRBL)
- 2x Servos (lift + gripper)
- PCA9685 servo controller
- Buck converter (6V servo power)
- Power supply + case

**Next Steps:**
- Test on Pi hardware tomorrow
- Calibrate board on Pi
- Test servo movements
- Play first game offline with Stockfish!

---

**🎉 Your Chess Mover Machine is ready for Raspberry Pi deployment!**

_Implementation by Claude Code - 2025-01-18_
