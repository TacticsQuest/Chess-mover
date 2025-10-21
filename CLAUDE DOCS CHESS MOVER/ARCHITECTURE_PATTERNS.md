# ARCHITECTURE PATTERNS - Chess Mover Machine
**Version:** 1.0.0
**Last Updated:** 2025-01-18
**Purpose:** Python/Tkinter/GRBL architecture patterns and best practices

---

## 📋 LAYER ARCHITECTURE

### Three-Layer Pattern

```
┌─────────────────────────────────────┐
│   UI Layer (Tkinter)                │  ← User interaction
│   - main_window.py                  │
│   - board_canvas.py                 │
│   - settings_dialog.py              │
└──────────────┬──────────────────────┘
               │ (events, callbacks)
┌──────────────▼──────────────────────┐
│   Logic Layer (Python)              │  ← Business logic
│   - coordinate_converter.py         │
│   - path_planner.py                 │
│   - state_manager.py                │
└──────────────┬──────────────────────┘
               │ (commands)
┌──────────────▼──────────────────────┐
│   Hardware Layer (Controllers)      │  ← Physical control
│   - grbl_controller.py              │
│   - servo_controller.py             │
└─────────────────────────────────────┘
```

**Key Principles:**
- **UI knows about Logic**, not Hardware
- **Logic knows about Hardware interfaces**, not implementation
- **Hardware knows nothing** about UI or chess
- Each layer can be tested independently

---

## 🗂️ FILE ORGANIZATION

### Current Structure

```
chess_mover/
├── main.py                          # 50 lines - Entry point only
│
├── config/
│   └── settings.yaml               # Board dims, COM port, profiles
│
├── ui/                             # UI Layer
│   ├── __init__.py
│   ├── main_window.py              # Main Tkinter window (200 lines)
│   ├── board_canvas.py             # Chess board canvas (250 lines)
│   └── settings_dialog.py          # Config dialog (150 lines)
│
├── controllers/                    # Hardware Layer
│   ├── __init__.py
│   ├── grbl_controller.py          # GRBL serial comm (300 lines)
│   └── servo_controller.py         # Servo stubs (100 lines, Phase 3)
│
├── logic/                          # Business Logic Layer
│   ├── __init__.py
│   ├── coordinate_converter.py     # Chess ←→ Machine coords (150 lines)
│   ├── path_planner.py             # Safety & path planning (200 lines)
│   └── state_manager.py            # App state tracking (150 lines)
│
├── tests/                          # Testing
│   ├── __init__.py
│   ├── mock_grbl.py                # Mock GRBL controller
│   ├── test_coordinates.py
│   ├── test_path_planning.py
│   └── test_integration.py
│
├── docs/                           # Documentation
│   └── CALIBRATION_GUIDE.md
│
└── requirements.txt
```

---

## 🎯 FILE TEMPLATES

### 1. UI Component (Tkinter)

```python
"""
board_canvas.py

Purpose: Interactive chess board canvas for square selection
Layer: UI (knows nothing about GRBL)
Dependencies: coordinate_converter (logic layer)

Why separate: Keeps UI logic isolated, testable
Could swap: Replace Tkinter with PyQt, web UI later

Last modified: 2025-01-18
"""

import tkinter as tk
from typing import Callable, Optional

class BoardCanvas(tk.Canvas):
    """
    Chess board widget that handles user clicks and visualization.

    Responsibilities:
    - Draw 8x8 chess board
    - Handle square clicks
    - Highlight selected squares
    - Show gantry position overlay

    Does NOT:
    - Know about GRBL commands
    - Handle coordinate conversion (delegates to logic layer)
    - Manage hardware state
    """

    def __init__(
        self,
        parent: tk.Widget,
        square_size: int = 50,
        on_square_click: Optional[Callable[[str], None]] = None
    ):
        """
        Args:
            parent: Tkinter parent widget
            square_size: Pixel size of each square
            on_square_click: Callback when square is clicked (receives "A1"-"H8")
        """
        width = height = square_size * 8
        super().__init__(parent, width=width, height=height, bg="white")

        self.square_size = square_size
        self.on_square_click = on_square_click
        self.highlighted_square: Optional[str] = None

        self._draw_board()
        self.bind("<Button-1>", self._handle_click)

    def _draw_board(self) -> None:
        """Draw 8x8 chess board pattern."""
        files = "ABCDEFGH"
        for row in range(8):
            for col in range(8):
                x1 = col * self.square_size
                y1 = row * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size

                # Alternating colors (beige/brown)
                color = "#F0D9B5" if (row + col) % 2 == 0 else "#B58863"
                self.create_rectangle(x1, y1, x2, y2, fill=color, tags=f"square")

                # Square label (e.g., "A1")
                square = f"{files[col]}{8 - row}"
                self.create_text(
                    x1 + 5, y1 + 5,
                    text=square, anchor="nw",
                    font=("Arial", 8), tags=f"label_{square}"
                )

    def _handle_click(self, event: tk.Event) -> None:
        """Convert click position to chess square and invoke callback."""
        col = event.x // self.square_size
        row = event.y // self.square_size

        if 0 <= col < 8 and 0 <= row < 8:
            files = "ABCDEFGH"
            square = f"{files[col]}{8 - row}"
            self.highlight_square(square)

            if self.on_square_click:
                self.on_square_click(square)

    def highlight_square(self, square: str) -> None:
        """Highlight selected square with yellow border."""
        # Clear previous highlight
        self.delete("highlight")

        files = "ABCDEFGH"
        file_idx = files.index(square[0])
        rank = int(square[1])
        row = 8 - rank
        col = file_idx

        x1 = col * self.square_size
        y1 = row * self.square_size
        x2 = x1 + self.square_size
        y2 = y1 + self.square_size

        # Draw yellow highlight border
        self.create_rectangle(
            x1, y1, x2, y2,
            outline="yellow", width=3,
            tags="highlight"
        )
        self.highlighted_square = square

# Usage example:
# canvas = BoardCanvas(root, square_size=60, on_square_click=handle_square_click)
# canvas.pack()
```

---

### 2. Hardware Controller

```python
"""
grbl_controller.py

Purpose: Low-level GRBL serial communication
Layer: Hardware (knows nothing about chess or UI)
Dependencies: pyserial

Why separate: Hardware abstraction allows mocking for tests
Could swap: Different CNC controller, robotic arm

Last modified: 2025-01-18
"""

import serial
import time
import logging
from typing import Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class GRBLState(Enum):
    """GRBL machine states"""
    IDLE = "Idle"
    RUN = "Run"
    HOLD = "Hold"
    ALARM = "Alarm"
    HOME = "Home"
    UNKNOWN = "Unknown"

class GRBLError(Exception):
    """GRBL-specific errors"""
    pass

class GRBLController:
    """
    GRBL CNC controller interface over serial.

    Responsibilities:
    - Establish serial connection
    - Send G-code commands
    - Parse GRBL responses
    - Track machine state
    - Emergency stop

    Does NOT:
    - Know about chess coordinates
    - Know about UI state
    - Make movement decisions (logic layer)
    """

    def __init__(self, timeout: float = 5.0):
        """
        Args:
            timeout: Default command timeout in seconds
        """
        self.serial: Optional[serial.Serial] = None
        self.timeout = timeout
        self.current_state = GRBLState.UNKNOWN
        self.position: Tuple[float, float] = (0.0, 0.0)

    def connect(self, port: str, baud: int = 115200) -> bool:
        """
        Connect to GRBL controller via serial port.

        Args:
            port: COM port (e.g., "COM4" on Windows, "/dev/ttyUSB0" on Linux)
            baud: Baud rate (default 115200 for GRBL 1.1)

        Returns:
            True if connected successfully

        Raises:
            ConnectionError: If connection fails
        """
        try:
            self.serial = serial.Serial(
                port,
                baud,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            time.sleep(2)  # Wait for GRBL to initialize

            # Read initialization message
            while self.serial.in_waiting:
                line = self.serial.readline().decode().strip()
                logger.info(f"GRBL init: {line}")

            logger.info(f"Connected to GRBL on {port}")
            self.current_state = GRBLState.IDLE
            return True

        except serial.SerialException as e:
            logger.error(f"Failed to connect to {port}: {e}")
            raise ConnectionError(f"Cannot connect to {port}: {e}")

    def disconnect(self) -> None:
        """Close serial connection."""
        if self.serial and self.serial.is_open:
            self.serial.close()
            logger.info("Disconnected from GRBL")
        self.serial = None
        self.current_state = GRBLState.UNKNOWN

    def send_command(self, cmd: str, wait_ok: bool = True) -> str:
        """
        Send G-code command to GRBL.

        Args:
            cmd: G-code command (e.g., "G0 X10 Y10")
            wait_ok: Wait for "ok" response before returning

        Returns:
            GRBL response text

        Raises:
            ConnectionError: If not connected
            GRBLError: If GRBL returns error
            TimeoutError: If no response within timeout
        """
        if not self.serial or not self.serial.is_open:
            raise ConnectionError("Not connected to GRBL")

        try:
            # Send command
            logger.debug(f"Sending: {cmd}")
            self.serial.write(f"{cmd}\n".encode())
            self.serial.flush()

            if not wait_ok:
                return ""

            # Wait for response
            start = time.time()
            response = ""

            while time.time() - start < self.timeout:
                if self.serial.in_waiting:
                    line = self.serial.readline().decode().strip()
                    logger.debug(f"Received: {line}")
                    response += line + "\n"

                    if line == "ok":
                        return response
                    elif line.startswith("error"):
                        raise GRBLError(f"GRBL error: {line}")

            raise TimeoutError(f"No response to command: {cmd}")

        except serial.SerialException as e:
            logger.error(f"Serial error: {e}")
            self.disconnect()
            raise ConnectionError(f"Serial communication failed: {e}")

    def home(self) -> bool:
        """
        Perform homing cycle ($H).

        Returns:
            True if homing successful

        Raises:
            GRBLError: If homing fails
        """
        logger.info("Starting homing cycle...")
        self.send_command("$H")
        self.position = (0.0, 0.0)
        self.current_state = GRBLState.IDLE
        logger.info("Homing complete")
        return True

    def move_absolute(self, x: float, y: float, feed_rate: int = 3000) -> bool:
        """
        Move to absolute position (G0 rapid move).

        Args:
            x: X coordinate in mm
            y: Y coordinate in mm
            feed_rate: Feed rate in mm/min (default 3000)

        Returns:
            True if move successful

        Note: Caller must validate coordinates are within bounds!
        """
        cmd = f"G0 X{x:.3f} Y{y:.3f} F{feed_rate}"
        self.send_command(cmd)
        self.position = (x, y)
        logger.info(f"Moved to X{x:.3f} Y{y:.3f}")
        return True

    def emergency_stop(self) -> bool:
        """
        Emergency stop - send feed hold (!) to GRBL.

        Returns:
            True if stop command sent
        """
        if self.serial and self.serial.is_open:
            logger.warning("EMERGENCY STOP")
            self.serial.write(b"!")
            self.serial.flush()
            self.current_state = GRBLState.HOLD
            return True
        return False

    def get_status(self) -> dict:
        """
        Query GRBL status (?).

        Returns:
            Dict with keys: state, x, y, speed
        """
        if not self.serial or not self.serial.is_open:
            return {"state": "disconnected"}

        # Send status query (don't wait for 'ok')
        self.serial.write(b"?\n")
        time.sleep(0.1)

        if self.serial.in_waiting:
            line = self.serial.readline().decode().strip()
            # Parse: <Idle|MPos:0.000,0.000,0.000|FS:0,0>
            # Simplified parsing (full parser would be more robust)
            logger.debug(f"Status: {line}")

        return {
            "state": self.current_state.value,
            "x": self.position[0],
            "y": self.position[1]
        }
```

---

### 3. Business Logic

```python
"""
coordinate_converter.py

Purpose: Convert between chess coordinates and machine coordinates
Layer: Logic (bridges UI and hardware)
Dependencies: None (pure math)

Why separate: Testable without UI or hardware
Critical: All movements depend on this being correct!

Last modified: 2025-01-18
"""

from typing import Tuple
import logging

logger = logging.getLogger(__name__)

class CoordinateConverter:
    """
    Converts between chess board coordinates and machine coordinates.

    Chess coordinates: "A1" to "H8" (user-facing)
    Machine coordinates: (X, Y) in mm (GRBL)

    Coordinate systems:
    - Chess: A1 = bottom-left (white's perspective)
    - Machine: Origin at physical corner (configurable)

    Configuration:
    - board_width: Physical board width in mm
    - board_height: Physical board height in mm
    - origin_x: Machine X coordinate of A1 square center
    - origin_y: Machine Y coordinate of A1 square center
    """

    def __init__(
        self,
        board_width: float,
        board_height: float,
        origin_x: float = 0.0,
        origin_y: float = 0.0
    ):
        """
        Args:
            board_width: Physical board width in mm (e.g., 400mm)
            board_height: Physical board height in mm (e.g., 400mm)
            origin_x: Machine X coord of A1 center (mm)
            origin_y: Machine Y coord of A1 center (mm)
        """
        self.board_width = board_width
        self.board_height = board_height
        self.origin_x = origin_x
        self.origin_y = origin_y

        self.square_width = board_width / 8
        self.square_height = board_height / 8

        logger.info(
            f"Coordinate system: {board_width}x{board_height}mm, "
            f"origin at ({origin_x}, {origin_y}), "
            f"square size {self.square_width:.1f}x{self.square_height:.1f}mm"
        )

    def chess_to_machine(self, square: str) -> Tuple[float, float]:
        """
        Convert chess square to machine coordinates.

        Args:
            square: Chess square (e.g., "A1", "H8")

        Returns:
            Tuple (x, y) in mm

        Raises:
            ValueError: If square is invalid

        Examples:
            "A1" → (origin_x, origin_y)
            "H8" → (origin_x + 7*square_width, origin_y + 7*square_height)
        """
        if not self.validate_square(square):
            raise ValueError(f"Invalid chess square: {square}")

        file = square[0].upper()
        rank = int(square[1])

        # Convert file (A-H) to column index (0-7)
        file_index = ord(file) - ord('A')

        # Convert rank (1-8) to row index (0-7)
        rank_index = rank - 1

        # Calculate machine coordinates (center of square)
        x = self.origin_x + (file_index * self.square_width) + (self.square_width / 2)
        y = self.origin_y + (rank_index * self.square_height) + (self.square_height / 2)

        logger.debug(f"{square} → ({x:.2f}, {y:.2f})")
        return (x, y)

    def machine_to_chess(self, x: float, y: float) -> str:
        """
        Convert machine coordinates to nearest chess square.

        Args:
            x: Machine X coordinate in mm
            y: Machine Y coordinate in mm

        Returns:
            Chess square (e.g., "D4")

        Note: Returns nearest square even if outside board
        """
        # Calculate relative position from origin
        rel_x = x - self.origin_x
        rel_y = y - self.origin_y

        # Find nearest square
        file_index = int(rel_x / self.square_width)
        rank_index = int(rel_y / self.square_height)

        # Clamp to valid range
        file_index = max(0, min(7, file_index))
        rank_index = max(0, min(7, rank_index))

        file = chr(ord('A') + file_index)
        rank = rank_index + 1

        square = f"{file}{rank}"
        logger.debug(f"({x:.2f}, {y:.2f}) → {square}")
        return square

    def validate_square(self, square: str) -> bool:
        """
        Check if square is valid chess notation.

        Args:
            square: Chess square to validate

        Returns:
            True if valid (A1-H8)
        """
        if len(square) != 2:
            return False

        file = square[0].upper()
        rank = square[1]

        return file in "ABCDEFGH" and rank in "12345678"
```

---

## 🔍 PATTERN: Mock for Testing

```python
"""
tests/mock_grbl.py

Purpose: Mock GRBL controller for testing without hardware
Why: Fast tests, CI/CD, safe edge case testing

Usage:
    from tests.mock_grbl import MockGRBLController
    grbl = MockGRBLController()
    grbl.connect("MOCK_PORT")
    grbl.home()
    grbl.move_absolute(100, 100)
    assert grbl.position == (100, 100)
"""

from controllers.grbl_controller import GRBLState

class MockGRBLController:
    """Simulates GRBL without serial hardware."""

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.is_connected = False
        self.is_homed = False
        self.current_state = GRBLState.UNKNOWN
        self.command_log = []

    def connect(self, port: str, baud: int = 115200) -> bool:
        print(f"[MOCK GRBL] Connected to {port} at {baud} baud")
        self.is_connected = True
        self.current_state = GRBLState.IDLE
        return True

    def home(self) -> bool:
        if not self.is_connected:
            raise ConnectionError("Not connected")
        print("[MOCK GRBL] Homing...")
        self.x, self.y = 0.0, 0.0
        self.is_homed = True
        self.command_log.append("$H")
        return True

    def move_absolute(self, x: float, y: float, feed_rate: int = 3000) -> bool:
        if not self.is_homed:
            raise Exception("Machine not homed!")
        print(f"[MOCK GRBL] Moving to X{x:.2f} Y{y:.2f} F{feed_rate}")
        self.x, self.y = x, y
        self.command_log.append(f"G0 X{x:.3f} Y{y:.3f} F{feed_rate}")
        return True

    def send_command(self, cmd: str, wait_ok: bool = True) -> str:
        print(f"[MOCK GRBL] Command: {cmd}")
        self.command_log.append(cmd)
        return "ok\n"

    def get_status(self) -> dict:
        return {
            "state": self.current_state.value,
            "x": self.x,
            "y": self.y
        }
```

---

## 📏 CODE QUALITY STANDARDS

### File Size Limits
- **Max 300 lines per file** - If larger, split into modules
- **Max 50 lines per function** - Extract helper functions
- **Max 5 parameters** - Use dataclasses or config dicts

### Type Hints (Required)
```python
# ✅ Good - Type hints on all functions
def chess_to_machine(self, square: str) -> Tuple[float, float]:
    ...

# ❌ Bad - No type hints
def chess_to_machine(self, square):
    ...
```

### Docstrings (Required)
```python
"""
Module docstring explaining file purpose.

Why this file exists, what layer it belongs to,
what it depends on, and what could replace it.
"""

class MyClass:
    """One-line class description.

    Responsibilities:
    - What it does
    - What it manages

    Does NOT:
    - What it doesn't do (important!)
    """

    def my_method(self, param: str) -> bool:
        """
        One-line method description.

        Args:
            param: Description

        Returns:
            Description

        Raises:
            ValueError: When this happens
        """
```

---

## 🎯 ANTI-PATTERNS TO AVOID

### ❌ God Class

```python
# DON'T DO THIS
class ChessMoverApp:
    """One class that does EVERYTHING"""
    def __init__(self):
        self.setup_ui()
        self.connect_grbl()
        self.convert_coordinates()
        self.plan_path()
        # ... 2000 lines later ...
```

### ✅ Separated Concerns

```python
# DO THIS INSTEAD
class MainWindow:
    """UI only"""
    def __init__(self, grbl_service):
        self.grbl_service = grbl_service
        self.setup_ui()

class GRBLService:
    """Hardware control only"""
    def __init__(self, converter, planner):
        self.converter = converter
        self.planner = planner
```

---

## ✅ ARCHITECTURE CHECKLIST

Before adding new code:
- [ ] Which layer does this belong to? (UI/Logic/Hardware)
- [ ] Can this be tested without hardware?
- [ ] Are there hardcoded values that should be in config?
- [ ] Is this file under 300 lines?
- [ ] Do all functions have type hints and docstrings?
- [ ] Is there a mock version for testing?
- [ ] Are errors handled gracefully?
- [ ] Is logging comprehensive?

---

**Remember:** Good architecture makes testing easy and future changes simple!
