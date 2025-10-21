# TESTING GUIDE - Chess Mover Machine
**Version:** 1.0.0
**Last Updated:** 2025-01-18
**Purpose:** Hardware testing strategies - mock, simulate, physical

---

## 🎯 THREE-TIER TESTING STRATEGY

```
┌────────────────────────────────────┐
│ Tier 1: Unit Tests (Mock)         │  ← Fast, safe, CI-friendly
│ - No hardware required             │
│ - Mock GRBL controller             │
│ - Test logic & coordinates         │
└────────────────────────────────────┘
               ↓
┌────────────────────────────────────┐
│ Tier 2: Integration Tests (Mock)  │  ← Test workflows
│ - UI → Logic → Mock Hardware       │
│ - Full application flow            │
│ - No physical movement             │
└────────────────────────────────────┘
               ↓
┌────────────────────────────────────┐
│ Tier 3: Hardware Tests (Physical) │  ← Manual verification
│ - Real GRBL over serial            │
│ - Actual gantry movement           │
│ - Calibration verification         │
└────────────────────────────────────┘
```

---

## ✅ TIER 1: UNIT TESTS (Mock Hardware)

### Purpose
- Test business logic without hardware
- Fast execution (milliseconds)
- Safe to run anytime
- Perfect for CI/CD

### Setup

```bash
# Install pytest
pip install pytest pytest-mock

# Run all unit tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=chess_mover --cov-report=html
```

### Example: Test Coordinate Conversion

```python
# tests/test_coordinates.py

import pytest
from logic.coordinate_converter import CoordinateConverter

def test_chess_to_machine_a1():
    """A1 should map to origin."""
    converter = CoordinateConverter(
        board_width=400,
        board_height=400,
        origin_x=0,
        origin_y=0
    )

    x, y = converter.chess_to_machine("A1")

    # A1 center should be at (25, 25) for 400mm board
    # (half a square from origin)
    assert x == pytest.approx(25.0)
    assert y == pytest.approx(25.0)

def test_chess_to_machine_h8():
    """H8 should map to opposite corner."""
    converter = CoordinateConverter(400, 400, 0, 0)

    x, y = converter.chess_to_machine("H8")

    # H8 center should be at (375, 375)
    assert x == pytest.approx(375.0)
    assert y == pytest.approx(375.0)

def test_invalid_square_raises_error():
    """Invalid squares should raise ValueError."""
    converter = CoordinateConverter(400, 400, 0, 0)

    with pytest.raises(ValueError):
        converter.chess_to_machine("Z9")  # Invalid

    with pytest.raises(ValueError):
        converter.chess_to_machine("A0")  # Rank 0 doesn't exist
```

### Example: Test with Mock GRBL

```python
# tests/test_grbl_mock.py

import pytest
from tests.mock_grbl import MockGRBLController

def test_mock_grbl_home():
    """Mock GRBL should track homing."""
    grbl = MockGRBLController()
    grbl.connect("MOCK_PORT")

    assert grbl.home() is True
    assert grbl.is_homed is True
    assert grbl.x == 0.0
    assert grbl.y == 0.0

def test_mock_grbl_move_absolute():
    """Mock GRBL should track position."""
    grbl = MockGRBLController()
    grbl.connect("MOCK_PORT")
    grbl.home()

    grbl.move_absolute(100, 200)

    assert grbl.x == 100.0
    assert grbl.y == 200.0
    assert "G0 X100" in grbl.command_log[-1]

def test_mock_grbl_move_before_home_raises():
    """Moving before homing should raise error."""
    grbl = MockGRBLController()
    grbl.connect("MOCK_PORT")

    with pytest.raises(Exception, match="not homed"):
        grbl.move_absolute(100, 100)
```

### Run Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_coordinates.py -v

# Run specific test
pytest tests/test_coordinates.py::test_chess_to_machine_a1 -v

# Show print statements
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -x
```

---

## 🔄 TIER 2: INTEGRATION TESTS

### Purpose
- Test full application flow
- UI → Logic → Mock Hardware
- Verify components work together
- Still no physical hardware

### Example: Full Workflow Test

```python
# tests/test_integration.py

import pytest
from tests.mock_grbl import MockGRBLController
from logic.coordinate_converter import CoordinateConverter
from logic.path_planner import PathPlanner

def test_full_move_workflow():
    """Test complete move from chess square to GRBL command."""

    # Setup components
    grbl = MockGRBLController()
    grbl.connect("MOCK_PORT")
    grbl.home()

    converter = CoordinateConverter(400, 400, 0, 0)
    planner = PathPlanner(max_x=400, max_y=400)

    # User clicks square E4
    square = "E4"

    # Convert to machine coords
    x, y = converter.chess_to_machine(square)

    # Validate move is safe
    assert planner.validate_move(x, y) is True

    # Execute move
    grbl.move_absolute(x, y, feed_rate=3000)

    # Verify
    assert grbl.x == pytest.approx(x)
    assert grbl.y == pytest.approx(y)
    assert len(grbl.command_log) > 0
```

---

## 🔧 TIER 3: HARDWARE TESTS (Physical)

### Purpose
- Verify with real GRBL controller
- Test actual gantry movement
- Calibration validation
- **Safety critical!**

### Safety Checklist

**Before EVERY hardware test:**
- [ ] Emergency stop button accessible
- [ ] Work area clear of obstacles
- [ ] Machine homed after power-on
- [ ] Feed rates set conservatively (start at 1000 mm/min)
- [ ] Monitor first movement closely
- [ ] Log file enabled for debugging
- [ ] Backup of working configuration

### Manual Test Script

```python
# tests/test_hardware.py (run manually, not automated)

"""
HARDWARE TEST - REQUIRES PHYSICAL FALCON CONNECTED

Safety:
- Ensure work area is clear
- Have emergency stop ready
- Start with slow feed rates
- Monitor closely

Run with: python tests/test_hardware.py
"""

import sys
import time
from controllers.grbl_controller import GRBLController

def test_connection():
    """Test 1: Serial connection."""
    print("\n=== TEST 1: Connection ===")
    port = input("Enter COM port (e.g., COM4): ")

    grbl = GRBLController()

    try:
        grbl.connect(port, 115200)
        print("✅ Connected successfully")

        # Read status
        status = grbl.get_status()
        print(f"Status: {status}")

        return grbl

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

def test_home(grbl):
    """Test 2: Homing cycle."""
    print("\n=== TEST 2: Homing ===")
    input("Press Enter to start homing cycle ($H)...")

    try:
        grbl.home()
        print("✅ Homing complete")
        time.sleep(2)

    except Exception as e:
        print(f"❌ Homing failed: {e}")
        grbl.disconnect()
        sys.exit(1)

def test_small_move(grbl):
    """Test 3: Small test movement."""
    print("\n=== TEST 3: Small Movement ===")
    print("Will move to X10 Y10 (10mm from origin)")
    input("Press Enter to execute move...")

    try:
        grbl.move_absolute(10, 10, feed_rate=1000)  # Slow speed
        print("✅ Move complete")
        time.sleep(2)

        # Return to origin
        print("Returning to origin...")
        grbl.move_absolute(0, 0, feed_rate=1000)
        print("✅ Returned to origin")

    except Exception as e:
        print(f"❌ Movement failed: {e}")
        grbl.emergency_stop()

def test_corners(grbl):
    """Test 4: Test all corners (within safe bounds)."""
    print("\n=== TEST 4: Corner Test ===")
    print("Will visit 4 corners of 200x200mm area")
    input("Press Enter to start...")

    corners = [
        (0, 0, "Origin"),
        (200, 0, "Bottom-Right"),
        (200, 200, "Top-Right"),
        (0, 200, "Top-Left"),
        (0, 0, "Back to Origin")
    ]

    try:
        for x, y, name in corners:
            print(f"Moving to {name} ({x}, {y})...")
            grbl.move_absolute(x, y, feed_rate=2000)
            time.sleep(1)

        print("✅ Corner test complete")

    except Exception as e:
        print(f"❌ Corner test failed: {e}")
        grbl.emergency_stop()

def main():
    print("=" * 50)
    print("CHESS MOVER MACHINE - HARDWARE TEST")
    print("=" * 50)
    print("\n⚠️  WARNING: This will move physical hardware!")
    print("Ensure work area is clear and emergency stop ready.\n")

    proceed = input("Proceed with hardware tests? (yes/no): ")
    if proceed.lower() != "yes":
        print("Aborted.")
        return

    # Run tests
    grbl = test_connection()
    test_home(grbl)
    test_small_move(grbl)

    corners = input("Run corner test? (yes/no): ")
    if corners.lower() == "yes":
        test_corners(grbl)

    # Cleanup
    print("\n=== Test Complete ===")
    grbl.disconnect()
    print("Disconnected. Tests finished.")

if __name__ == "__main__":
    main()
```

### Running Hardware Tests

```bash
# Run manual hardware test
python tests/test_hardware.py

# Follow prompts and confirm each step
# NEVER run automated hardware tests!
```

---

## 📊 TEST COVERAGE GOALS

| Component | Coverage Target | Why |
|-----------|----------------|-----|
| Coordinate conversion | 100% | Critical for accuracy |
| Path planning | 95% | Safety-critical |
| GRBL controller | 80% | Hardware mocking limits |
| UI components | 60% | Manual testing primary |

### Measure Coverage

```bash
# Install coverage tool
pip install pytest-cov

# Run with coverage
pytest tests/ --cov=chess_mover --cov-report=html

# Open htmlcov/index.html to see report
```

---

## 🚨 TESTING CHECKLIST

### Before Each Development Session
- [ ] Run unit tests (pytest)
- [ ] Verify all tests pass
- [ ] Check no regressions

### After Implementing Feature
- [ ] Write unit tests for new code
- [ ] Run full test suite
- [ ] Test with mock GRBL
- [ ] Document test results

### Before Hardware Testing
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Safety checklist complete
- [ ] Backup working config

### Before Committing Code
- [ ] All tests pass
- [ ] Coverage > 80%
- [ ] No debug print statements
- [ ] Docstrings updated

---

## 🔍 DEBUGGING TIPS

### Enable Logging

```python
# Add to top of test file
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Print Test Output

```bash
# Show print statements in tests
pytest tests/ -v -s
```

### Run Specific Test

```bash
# Run one test function
pytest tests/test_coordinates.py::test_chess_to_machine_a1 -v -s
```

### Debug on Failure

```bash
# Drop into debugger on failure
pytest tests/ --pdb
```

---

**Remember:** Test with mocks first, hardware last. Safety is paramount!
