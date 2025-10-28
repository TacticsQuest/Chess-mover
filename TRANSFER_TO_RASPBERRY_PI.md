# Transfer Chess Mover Machine to Raspberry Pi

This guide covers transferring the Chess Mover Machine repository from Windows to your Raspberry Pi.

## Method 1: Git Clone (Recommended) ✅

This is the **easiest and cleanest** method since your repo is on GitHub.

### On Raspberry Pi:

```bash
# 1. Install git (if not already installed)
sudo apt update
sudo apt install git -y

# 2. Clone the repository
cd ~
git clone https://github.com/TacticsQuest/Chess-mover.git
cd Chess-mover

# 3. Install Python dependencies
pip3 install -r requirements.txt

# 4. Install Raspberry Pi specific hardware libraries
pip3 install adafruit-circuitpython-pca9685 adafruit-circuitpython-servokit
sudo apt install python3-serial -y

# 5. Make the compact mode launcher executable
chmod +x "Launch 7 Inch Compact Mode.bat"

# 6. Test launch (7" touchscreen mode)
python3 launch_compact.py
```

### Before Cloning (Optional - Push Latest Changes):

If you want to push your latest changes from Windows first:

```bash
# On Windows
cd "C:\Users\David\Documents\GitHub\Chess Mover Machine"

# Add all the important new files
git add Launch\ 7\ Inch\ Compact\ Mode.bat
git add launch_compact.py
git add controllers/gantry_controller.py
git add controllers/servo_controller.py
git add config/settings.yaml
git add ui/board_window.py
git add ui/editor_window.py
git add SERVO_SETUP_GUIDE.md
git add WIRING_REFERENCE_CARD.md
git add COMPLETE_RASPBERRY_PI_SETUP_GUIDE.md

# Clean up __pycache__ files (not needed in git)
git rm -r --cached **/__pycache__

# Commit changes
git commit -m "Add keep-alive ping, configure servos, and 7-inch touchscreen mode

- Implement keep-alive ping (M3 S1 every 25s) to prevent Falcon 30s timeout
- Configure Z-lift servo: 0° to 274° (75% of 365° gear rotation)
- Configure gripper servo: 0° to 5° (5° total range)
- Add 7-inch compact touchscreen UI (1024x600)
- Add servo calibration and wiring guides

🤖 Generated with Claude Code"

# Push to GitHub
git push
```

---

## Method 2: USB Drive Transfer

If you prefer a direct file transfer or don't have internet on the Pi:

### On Windows:

```bash
# 1. Copy entire folder to USB drive (excluding unnecessary files)
cd "C:\Users\David\Documents\GitHub"
xcopy "Chess Mover Machine" "E:\Chess Mover Machine" /E /I /H /EXCLUDE:exclude.txt

# Create exclude.txt with:
# __pycache__
# .git
# *.pyc
# test-results
# imager-1.9.6.exe
```

### On Raspberry Pi:

```bash
# 1. Mount USB drive
sudo mkdir -p /mnt/usb
sudo mount /dev/sda1 /mnt/usb

# 2. Copy to home directory
cp -r /mnt/usb/Chess\ Mover\ Machine ~/Chess-mover
cd ~/Chess-mover

# 3. Install dependencies
pip3 install -r requirements.txt
pip3 install adafruit-circuitpython-pca9685 adafruit-circuitpython-servokit
sudo apt install python3-serial -y

# 4. Unmount USB
sudo umount /mnt/usb
```

---

## Method 3: SCP (Secure Copy over Network)

If both machines are on the same network:

### On Windows (using PowerShell):

```powershell
# 1. Install OpenSSH client (if not installed)
# Settings > Apps > Optional Features > Add OpenSSH Client

# 2. Copy to Raspberry Pi
cd "C:\Users\David\Documents\GitHub"
scp -r "Chess Mover Machine" pi@raspberrypi.local:~/Chess-mover

# If prompted, enter Raspberry Pi password
```

### On Raspberry Pi:

```bash
# Install dependencies
cd ~/Chess-mover
pip3 install -r requirements.txt
pip3 install adafruit-circuitpython-pca9685 adafruit-circuitpython-servokit
sudo apt install python3-serial -y
```

---

## Post-Transfer Setup on Raspberry Pi

After transferring files by any method:

### 1. Enable Hardware Interfaces

```bash
sudo raspi-config
# Interface Options > I2C > Enable
# Interface Options > Serial Port > Enable
# Finish > Reboot
```

### 2. Connect Hardware

**GRBL/Falcon Connection:**
- USB cable from Falcon to Raspberry Pi USB port

**Servo Power (LM2596 at 6V):**
- LM2596 OUT+ → Servo red wires
- LM2596 OUT- → Servo brown wires + Raspberry Pi GND (Pin 6)

**Servo Signals:**
- GPIO 17 (Pin 11) → Z-lift servo (orange wire)
- GPIO 27 (Pin 13) → Gripper servo (orange wire)

**Reference:** See `WIRING_REFERENCE_CARD.md`

### 3. Test GRBL Connection

```bash
cd ~/Chess-mover
python3 -c "
from controllers.gantry_controller import GantryController
g = GantryController()
print('Available ports:', g.list_ports())
"
```

### 4. Configure Serial Port

Edit `config/settings.yaml`:
```yaml
grbl_port: "/dev/ttyUSB0"  # Or /dev/ttyACM0
grbl_baud: 115200
keep_alive_enabled: true
keep_alive_interval: 25.0
```

### 5. Enable Servo Hardware (Phase 3)

Edit `controllers/servo_controller.py` (lines 109-117):

**Uncomment these lines:**
```python
# Phase 3: Uncomment this when on Raspberry Pi
from adafruit_servokit import ServoKit
self.pca9685 = ServoKit(channels=16)
self.is_connected = True
self.log("[SERVO] Connected to PCA9685")
```

**Comment out the stub:**
```python
# Phase 1: Stub
# self.log("[SERVO] connect() - stub (Phase 1)")
# self.is_connected = False
```

### 6. Test Servos

```bash
python3 -c "
from controllers.servo_controller import ServoController
s = ServoController()
s.connect()
print('Servo status:', s.get_status())
# Test gripper
s.grip_open()   # Should open gripper (0°)
s.grip_close()  # Should close gripper (5°)
"
```

### 7. Launch Compact Mode (7" Touchscreen)

```bash
cd ~/Chess-mover
python3 launch_compact.py
```

### 8. Auto-Start on Boot (Optional)

```bash
# Use the setup script
chmod +x setup_autostart_pi.sh
./setup_autostart_pi.sh
```

Or manually:
```bash
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/chess-mover.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Chess Mover Machine
Exec=python3 /home/pi/Chess-mover/launch_compact.py
Path=/home/pi/Chess-mover
Terminal=false
EOF
```

---

## Important Files for Raspberry Pi

### Essential Files (Must Transfer):
- `launch_compact.py` - 7" touchscreen launcher
- `controllers/gantry_controller.py` - GRBL + keep-alive ping
- `controllers/servo_controller.py` - Servo control
- `config/settings.yaml` - Configuration
- `ui/board_window.py` - Main UI with keep-alive enabled
- `ui/editor_window.py` - Board editor with correct rank labels
- `logic/profiles.py` - Board profiles
- `assets/` - Chess piece images
- `requirements.txt` - Python dependencies

### Setup Guides (Helpful):
- `COMPLETE_RASPBERRY_PI_SETUP_GUIDE.md`
- `SERVO_SETUP_GUIDE.md`
- `WIRING_REFERENCE_CARD.md`
- `CALIBRATION_GUIDE.md`

### NOT Needed on Raspberry Pi:
- `imager-1.9.6.exe` - Windows only
- `*.bat` files - Windows batch scripts (except use for reference)
- `__pycache__/` folders - Python bytecode (auto-generated)
- `test-results/` - Test screenshots
- `.git/` folder - Git history (if using USB/SCP method)

---

## Troubleshooting

### Serial Port Permission Denied
```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```

### I2C Not Working
```bash
sudo apt install i2c-tools python3-smbus
sudo i2cdetect -y 1
# Should show PCA9685 at address 0x40
```

### Servo Not Moving
```bash
# Check PCA9685 connection
python3 -c "from board import SCL, SDA; import busio; i2c = busio.I2C(SCL, SDA); print('I2C devices:', [hex(x) for x in i2c.scan()])"
```

### Keep-Alive Not Working
- Check `config/settings.yaml` has correct `grbl_port`
- Verify Falcon is powered on
- Check USB cable connection
- Look for `[GRBL] 💓 Keep-alive ping sent (M3 S1)` in logs

### Touch Screen Not Calibrated
```bash
# Install calibration tool
sudo apt install xinput-calibrator
xinput_calibrator
# Follow on-screen instructions
```

---

## Quick Start Commands (Raspberry Pi)

```bash
# Clone repo (Method 1 - Recommended)
git clone https://github.com/TacticsQuest/Chess-mover.git ~/Chess-mover
cd ~/Chess-mover

# Install dependencies
pip3 install -r requirements.txt
pip3 install adafruit-circuitpython-pca9685 adafruit-circuitpython-servokit
sudo apt install python3-serial -y

# Enable hardware
sudo raspi-config  # Enable I2C and Serial

# Edit servo controller to enable hardware
nano controllers/servo_controller.py
# Uncomment lines 110-114 (Phase 3)

# Configure serial port
nano config/settings.yaml
# Set grbl_port: "/dev/ttyUSB0"

# Test
python3 launch_compact.py
```

---

## Support

- **Servo Calibration:** See `SERVO_CALIBRATION_GUIDE.md`
- **Wiring Diagrams:** See `WIRING_REFERENCE_CARD.md`
- **Full Pi Setup:** See `COMPLETE_RASPBERRY_PI_SETUP_GUIDE.md`
- **7" Touchscreen:** See `RASPBERRY_PI_7INCH_TOUCHSCREEN_SETUP.md`
