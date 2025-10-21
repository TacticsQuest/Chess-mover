import threading
import time
import serial
import serial.tools.list_ports
from queue import Queue, Empty
from typing import Callable, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ConnectionState(Enum):
    """GRBL connection state."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    ALARM = "alarm"

@dataclass
class Position:
    """Machine position in mm."""
    x: float
    y: float
    z: float

@dataclass
class SafetyLimits:
    """Software safety limits in mm."""
    x_min: float = 0.0
    x_max: float = 400.0
    y_min: float = 0.0
    y_max: float = 400.0
    z_min: float = 0.0
    z_max: float = 100.0

class GantryController:
    """
    GRBL gantry controller with safety features and health monitoring.

    Features:
    - Automatic reconnection on connection loss
    - Software safety limits
    - Connection health monitoring
    - Emergency stop
    - Real-time position tracking
    """

    def __init__(self, log_fn: Callable[[str], None] = print, safety_limits: Optional[SafetyLimits] = None):
        self._ser: Optional[serial.Serial] = None
        self._rx_thread: Optional[threading.Thread] = None
        self._rx_queue: Queue[str] = Queue()
        self._running = False
        self.log = log_fn

        # Connection state
        self._state = ConnectionState.DISCONNECTED
        self._last_response_time = 0.0
        self._health_check_interval = 2.0  # seconds
        self._auto_reconnect = False
        self._port = ""
        self._baud = 115200

        # Position tracking
        self._current_pos: Optional[Position] = None
        self._position_callbacks: list[Callable[[Position], None]] = []

        # Safety limits
        self.safety_limits = safety_limits or SafetyLimits()
        self._emergency_stop = False

        # Speed limiter settings
        self.max_speed_mm_min = 5000  # Maximum allowed speed
        self.min_speed_mm_min = 100   # Minimum allowed speed
        self.enable_speed_limit = True  # Enable/disable speed limiting

    @staticmethod
    def list_ports() -> list[str]:
        """List available serial ports."""
        return [p.device for p in serial.tools.list_ports.comports()]

    def get_state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state

    def get_position(self) -> Optional[Position]:
        """Get current machine position."""
        return self._current_pos

    def register_position_callback(self, callback: Callable[[Position], None]) -> None:
        """Register callback for position updates."""
        self._position_callbacks.append(callback)

    def enable_auto_reconnect(self, enable: bool = True) -> None:
        """Enable/disable automatic reconnection on connection loss."""
        self._auto_reconnect = enable
        if enable:
            self.log("[GRBL] Auto-reconnect enabled")

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

    def reset_emergency_stop(self) -> None:
        """Clear emergency stop flag."""
        self._emergency_stop = False
        self.log("[GRBL] Emergency stop cleared")

    def validate_position(self, x: float, y: float, z: float = 0.0) -> Tuple[bool, str]:
        """
        Validate position against safety limits.

        Returns:
            (valid, error_message)
        """
        if self._emergency_stop:
            return False, "Emergency stop active"

        limits = self.safety_limits
        if not (limits.x_min <= x <= limits.x_max):
            return False, f"X={x:.2f} out of range [{limits.x_min:.2f}, {limits.x_max:.2f}]"
        if not (limits.y_min <= y <= limits.y_max):
            return False, f"Y={y:.2f} out of range [{limits.y_min:.2f}, {limits.y_max:.2f}]"
        if not (limits.z_min <= z <= limits.z_max):
            return False, f"Z={z:.2f} out of range [{limits.z_min:.2f}, {limits.z_max:.2f}]"

        return True, ""

    def validate_speed(self, speed_mm_min: int) -> Tuple[int, str]:
        """
        Validate and clamp speed to safe limits.

        Args:
            speed_mm_min: Requested speed in mm/min

        Returns:
            (clamped_speed, warning_message)
        """
        if not self.enable_speed_limit:
            return speed_mm_min, ""

        original_speed = speed_mm_min
        warning = ""

        # Clamp to maximum
        if speed_mm_min > self.max_speed_mm_min:
            speed_mm_min = self.max_speed_mm_min
            warning = f"Speed limited: {original_speed} → {speed_mm_min} mm/min (max)"

        # Clamp to minimum
        elif speed_mm_min < self.min_speed_mm_min:
            speed_mm_min = self.min_speed_mm_min
            warning = f"Speed limited: {original_speed} → {speed_mm_min} mm/min (min)"

        return speed_mm_min, warning

    def connect(self, port: str, baud: int = 115200, auto_reconnect: bool = False):
        """
        Connect to GRBL controller.

        Args:
            port: Serial port (e.g., "COM4" or "/dev/ttyUSB0")
            baud: Baud rate (default 115200)
            auto_reconnect: Enable automatic reconnection on failure
        """
        self.disconnect()
        self._port = port
        self._baud = baud
        self._auto_reconnect = auto_reconnect
        self._emergency_stop = False

        try:
            self._state = ConnectionState.CONNECTING
            self._ser = serial.Serial(port=port, baudrate=baud, timeout=0.1)
            time.sleep(2.0)  # allow GRBL reset
            self._running = True
            self._last_response_time = time.time()

            # Start reader thread
            self._rx_thread = threading.Thread(target=self._reader, daemon=True)
            self._rx_thread.start()

            # Start health monitor thread
            self._health_thread = threading.Thread(target=self._health_monitor, daemon=True)
            self._health_thread.start()

            self._state = ConnectionState.CONNECTED
            self.log(f"[GRBL] ✓ Connected on {port} @ {baud}")

        except Exception as e:
            self._state = ConnectionState.ERROR
            self.log(f"[GRBL] ✗ Connection failed: {e}")
            raise

    def disconnect(self):
        """Disconnect from GRBL controller."""
        self._running = False
        self._auto_reconnect = False
        if self._ser:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None
        self._state = ConnectionState.DISCONNECTED
        self._current_pos = None
        self.log("[GRBL] Disconnected")

    def _reader(self):
        """Background thread to read GRBL responses."""
        assert self._ser is not None
        buf = b""
        while self._running:
            try:
                chunk = self._ser.read(1024)
                if chunk:
                    buf += chunk
                    self._last_response_time = time.time()

                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        line = line.strip().decode(errors='ignore')
                        if line:
                            self._rx_queue.put(line)
                            self._process_response(line)

            except Exception as e:
                self.log(f"[GRBL] RX error: {e}")
                self._state = ConnectionState.ERROR
                break

    def _process_response(self, line: str) -> None:
        """Process GRBL response for state updates."""
        # Detect alarm state
        if line.startswith("ALARM"):
            self._state = ConnectionState.ALARM
            self.log(f"[GRBL] ⚠️ ALARM: {line}")

        # Parse position from status reports
        # Format: <Idle|MPos:0.000,0.000,0.000|...>
        if line.startswith("<"):
            try:
                # Extract MPos if present
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
                            try:
                                callback(self._current_pos)
                            except Exception as e:
                                self.log(f"[GRBL] Position callback error: {e}")
            except Exception as e:
                pass  # Silently ignore parsing errors

    def _health_monitor(self) -> None:
        """Background thread to monitor connection health."""
        while self._running:
            time.sleep(self._health_check_interval)

            if not self._running:
                break

            # Check if we've received data recently
            elapsed = time.time() - self._last_response_time
            if elapsed > 5.0 and self._state == ConnectionState.CONNECTED:
                self.log(f"[GRBL] ⚠️ No response for {elapsed:.1f}s")

                # Request status to check if still alive
                if self._ser:
                    try:
                        self._ser.write(b'?')  # Status query (real-time command)
                    except Exception as e:
                        self.log(f"[GRBL] Health check failed: {e}")
                        self._state = ConnectionState.ERROR

                        # Attempt reconnection if enabled
                        if self._auto_reconnect:
                            self._attempt_reconnect()

    def _attempt_reconnect(self) -> None:
        """Attempt to reconnect to GRBL."""
        self.log("[GRBL] Attempting auto-reconnect...")
        try:
            self.disconnect()
            time.sleep(1.0)
            self.connect(self._port, self._baud, auto_reconnect=True)
        except Exception as e:
            self.log(f"[GRBL] Auto-reconnect failed: {e}")
        
    def read_line_nowait(self) -> Optional[str]:
        """Read line from GRBL without blocking."""
        try:
            return self._rx_queue.get_nowait()
        except Empty:
            return None

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

    def request_status(self) -> None:
        """Request real-time status from GRBL."""
        if self._ser:
            try:
                self._ser.write(b'?')  # Real-time status query
            except Exception as e:
                self.log(f"[GRBL] Status request failed: {e}")

    def get_current_position_blocking(self, timeout: float = 2.0) -> Optional[Position]:
        """
        Request current position and wait for response.

        Args:
            timeout: Maximum time to wait for response (seconds)

        Returns:
            Current position or None if timeout/error
        """
        if not self._ser:
            return None

        # Clear any old position data
        start_time = time.time()

        # Request status
        self.request_status()

        # Wait for position update
        while time.time() - start_time < timeout:
            if self._current_pos:
                return self._current_pos
            time.sleep(0.05)

        return None

    # Convenience methods
    def unlock(self) -> bool:
        """Unlock GRBL from alarm state ($X command)."""
        success = self.send("$X")
        if success and self._state == ConnectionState.ALARM:
            self._state = ConnectionState.CONNECTED
            self.log("[GRBL] Unlocked")
        return success

    def home(self) -> bool:
        """Home the machine ($H command)."""
        return self.send("$H")

    def set_mm_absolute(self) -> bool:
        """Set units to mm and absolute positioning mode."""
        success = self.send("G21")  # mm mode
        success = success and self.send("G90")  # absolute mode
        return success

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
        # Validate position
        valid, error_msg = self.validate_position(x_mm, y_mm, z_mm)
        if not valid:
            self.log(f"[GRBL] ✗ Move blocked: {error_msg}")
            return False

        # Validate and clamp speed
        clamped_speed, speed_warning = self.validate_speed(feed_mm_min)
        if speed_warning:
            self.log(f"[GRBL] ⚠️ {speed_warning}")

        return self.send(f"G0 X{float(x_mm):.3f} Y{float(y_mm):.3f} Z{float(z_mm):.3f} F{int(clamped_speed)}")
