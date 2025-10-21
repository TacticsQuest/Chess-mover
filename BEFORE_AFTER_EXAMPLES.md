# Chess Mover Machine - Before & After Code Examples

This document shows concrete before/after examples of the improvements.

---

## Example 1: Emergency Stop

### ❌ Before (No Emergency Stop)
```python
# No emergency stop capability
# User had to close application or unplug USB to stop motion
# Risk of damage if something goes wrong
```

### ✅ After (Emergency Stop Available)
```python
# In gantry_controller.py
def emergency_stop(self) -> None:
    """Emergency stop - immediately halt all motion."""
    self._emergency_stop = True
    if self._ser:
        try:
            # Send real-time command (no newline, highest priority)
            self._ser.write(b'!')
            self._ser.flush()
            self.log("[GRBL] ⚠️ EMERGENCY STOP!")
            self._state = ConnectionState.ALARM
        except Exception as e:
            self.log(f"[GRBL] Emergency stop failed: {e}")

# In GUI (board_window.py) - Add to toolbar:
estop_btn = tk.Button(
    right_toolbar,
    text="⚠ EMERGENCY STOP",
    font=("Segoe UI", 10, "bold"),
    bg="#c0392b",
    fg="white",
    command=self._emergency_stop
)
```

**Impact:** Immediate safety - can stop motion in emergency situations!

---

## Example 2: Safety Limits

### ❌ Before (No Validation)
```python
# Could send machine out of bounds - crash into walls!
def rapid_to(self, x_mm: float, y_mm: float, feed_mm_min: int = 2000):
    self.send(f"G0 X{float(x_mm):.3f} Y{float(y_mm):.3f} F{int(feed_mm_min)}")
    # No validation - might crash!
```

### ✅ After (Validated Moves)
```python
def rapid_to(self, x_mm: float, y_mm: float, feed_mm_min: int = 2000, z_mm: float = 0.0) -> bool:
    """
    Rapid move to absolute position with safety validation.

    Returns:
        True if command sent, False if blocked by safety
    """
    # Validate position
    valid, error_msg = self.validate_position(x_mm, y_mm, z_mm)
    if not valid:
        self.log(f"[GRBL] ✗ Move blocked: {error_msg}")
        return False

    return self.send(f"G0 X{float(x_mm):.3f} Y{float(y_mm):.3f} Z{float(z_mm):.3f} F{int(feed_mm_min)}")

# Example usage:
success = gantry.rapid_to(1000, 200)  # Returns False if out of bounds
if not success:
    messagebox.showerror("Move Failed", "Position out of safety limits")
```

**Impact:** Prevents crashes and hardware damage!

---

## Example 3: Connection Reliability

### ❌ Before (Manual Reconnection)
```python
# If USB disconnects, user must:
# 1. Notice the disconnect
# 2. Click "Connect" button
# 3. Select COM port again
# 4. Try to resume

# No connection health monitoring
# No automatic recovery
```

### ✅ After (Auto-Reconnect)
```python
# Connect with auto-reconnect
gantry.connect("COM4", 115200, auto_reconnect=True)

# Background health monitor checks connection every 2 seconds
def _health_monitor(self) -> None:
    """Background thread to monitor connection health."""
    while self._running:
        time.sleep(self._health_check_interval)

        elapsed = time.time() - self._last_response_time
        if elapsed > 5.0 and self._state == ConnectionState.CONNECTED:
            self.log(f"[GRBL] ⚠️ No response for {elapsed:.1f}s")

            # Request status to check if still alive
            if self._ser:
                try:
                    self._ser.write(b'?')  # Status query
                except Exception as e:
                    self.log(f"[GRBL] Health check failed: {e}")
                    self._state = ConnectionState.ERROR

                    # Attempt reconnection if enabled
                    if self._auto_reconnect:
                        self._attempt_reconnect()

# If USB disconnects:
# 1. Health monitor detects within 5 seconds
# 2. Automatically attempts reconnection
# 3. Logs the reconnection attempt
# 4. Resumes operation when successful
# User doesn't even need to click anything!
```

**Impact:** Much more reliable - automatic recovery from connection issues!

---

## Example 4: Position Tracking

### ❌ Before (No Position Info)
```python
# No way to know where gantry is
# Can't display position on board
# User has to guess or manually track position
```

### ✅ After (Real-Time Position)
```python
# Position tracking with callbacks
def _process_response(self, line: str) -> None:
    """Process GRBL response for state updates."""
    # Parse position from status reports
    # Format: <Idle|MPos:0.000,0.000,0.000|...>
    if line.startswith("<"):
        try:
            if "MPos:" in line:
                pos_str = line.split("MPos:")[1].split("|")[0]
                coords = pos_str.split(",")
                if len(coords) >= 3:
                    self._current_pos = Position(
                        x=float(coords[0]),
                        y=float(coords[1]),
                        z=float(coords[2])
                    )
                    # Notify callbacks
                    for callback in self._position_callbacks:
                        callback(self._current_pos)
        except Exception:
            pass

# In GUI - Register callback
def on_position_update(pos: Position):
    # Update live position display on board
    self._draw_position_indicator(pos)

gantry.register_position_callback(on_position_update)

# Request position updates
gantry.request_status()  # Every 500ms via _poll_grbl
```

**Impact:** Live position display on board - always know where the gantry is!

---

## Example 5: Type Safety

### ❌ Before (No Type Hints)
```python
def rapid_to(self, x_mm, y_mm, feed_mm_min=2000):
    # What types are these?
    # What does this return?
    # IDE can't help with autocomplete
    self.send(f"G0 X{float(x_mm):.3f} Y{float(y_mm):.3f} F{int(feed_mm_min)}")
```

### ✅ After (Full Type Safety)
```python
def rapid_to(self, x_mm: float, y_mm: float, feed_mm_min: int = 2000, z_mm: float = 0.0) -> bool:
    """
    Rapid move to absolute position with safety validation.

    Args:
        x_mm: X coordinate in mm
        y_mm: Y coordinate in mm
        feed_mm_min: Feed rate in mm/min
        z_mm: Z coordinate in mm (default 0.0)

    Returns:
        True if command sent, False if blocked by safety
    """
    # IDE shows types and return value
    # mypy can catch errors at development time
    # Autocomplete works perfectly
    valid, error_msg = self.validate_position(x_mm, y_mm, z_mm)
    if not valid:
        self.log(f"[GRBL] ✗ Move blocked: {error_msg}")
        return False
    return self.send(f"G0 X{float(x_mm):.3f} Y{float(y_mm):.3f} Z{float(z_mm):.3f} F{int(feed_mm_min)}")

# With dataclasses
@dataclass
class Position:
    """Machine position in mm."""
    x: float
    y: float
    z: float

# IDE autocomplete works:
pos = gantry.get_position()
if pos:
    print(f"X: {pos.x}, Y: {pos.y}, Z: {pos.z}")  # IDE knows these fields!
```

**Impact:** Fewer bugs, better IDE support, easier maintenance!

---

## Example 6: Error Handling

### ❌ Before (Silent Failures)
```python
def send(self, cmd: str):
    if not self._ser:
        self.log("[GRBL] Not connected")
        return  # Fails silently
    line = (cmd.strip() + "\n").encode()
    self._ser.write(line)  # Might throw exception
    self.log(f">> {cmd}")

# Caller doesn't know if command succeeded
gantry.send("G0 X100 Y100")  # Did this work? Who knows!
```

### ✅ After (Explicit Error Handling)
```python
def send(self, cmd: str) -> bool:
    """
    Send command to GRBL.

    Returns:
        True if sent successfully, False otherwise
    """
    if not self._ser:
        self.log("[GRBL] ✗ Not connected")
        return False

    if self._emergency_stop:
        self.log("[GRBL] ✗ Emergency stop active - command blocked")
        return False

    try:
        line = (cmd.strip() + "\n").encode()
        self._ser.write(line)
        self.log(f">> {cmd}")
        return True
    except Exception as e:
        self.log(f"[GRBL] ✗ Send failed: {e}")
        self._state = ConnectionState.ERROR
        return False

# Caller knows if command succeeded
success = gantry.send("G0 X100 Y100")
if not success:
    messagebox.showerror("Command Failed", "Could not send command to GRBL")
```

**Impact:** Better error handling and user feedback!

---

## Example 7: State Management

### ❌ Before (No State Tracking)
```python
# No way to know connection state
# Is it connected? Disconnected? In alarm?
# User has to guess from log messages
```

### ✅ After (Explicit State Management)
```python
class ConnectionState(Enum):
    """GRBL connection state."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    ALARM = "alarm"

# Always know the state
state = gantry.get_state()

if state == ConnectionState.CONNECTED:
    # OK to send commands
    gantry.rapid_to(100, 100)
elif state == ConnectionState.ALARM:
    # Need to unlock first
    messagebox.showwarning("GRBL Alarm", "Please reset alarm before moving")
    gantry.unlock()
elif state == ConnectionState.DISCONNECTED:
    # Need to connect first
    messagebox.showerror("Not Connected", "Please connect to GRBL first")

# GUI can show state with color coding:
state_colors = {
    ConnectionState.CONNECTED: '#27ae60',  # green
    ConnectionState.ALARM: '#e74c3c',      # red
    ConnectionState.ERROR: '#e67e22',      # orange
    ConnectionState.DISCONNECTED: '#95a5a6'  # gray
}
status_label.config(bg=state_colors[state])
```

**Impact:** Always know the system state - better UX and error prevention!

---

## Summary of Improvements

| Feature | Before | After | Impact |
|---------|--------|-------|--------|
| **Emergency Stop** | ❌ None | ✅ Hardware stop button | ⭐⭐⭐⭐⭐ Safety |
| **Safety Limits** | ❌ None | ✅ Automatic validation | ⭐⭐⭐⭐⭐ Prevent crashes |
| **Auto-Reconnect** | ❌ Manual | ✅ Automatic | ⭐⭐⭐⭐☆ Reliability |
| **Position Tracking** | ❌ None | ✅ Real-time | ⭐⭐⭐⭐⭐ Visibility |
| **Type Safety** | ❌ None | ✅ Full types | ⭐⭐⭐⭐☆ Code quality |
| **Error Handling** | ❌ Silent | ✅ Explicit | ⭐⭐⭐⭐☆ Debuggability |
| **State Management** | ❌ Implicit | ✅ Enum-based | ⭐⭐⭐⭐☆ Clarity |
| **Documentation** | ❌ Minimal | ✅ Comprehensive | ⭐⭐⭐⭐☆ Maintainability |

---

## Next: Integrate into GUI!

See `QUICK_WINS_GUIDE.md` for step-by-step instructions to add these features to your GUI in just 45 minutes!

---

🤖 **Generated by Claude Code - 2025-01-18**
