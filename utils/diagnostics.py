"""
Self-Test Diagnostics for Chess Mover Machine

Automated testing of gantry and servo systems before operation.
"""

from typing import Callable, Dict, List, Tuple
import time

class DiagnosticResult:
    """Result of a single diagnostic test."""

    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.name}: {self.message}"


class ChessMoverDiagnostics:
    """Automated diagnostics for Chess Mover Machine."""

    def __init__(self, gantry_controller, servo_controller, logger):
        """
        Initialize diagnostics.

        Args:
            gantry_controller: GantryController instance
            servo_controller: ServoController instance
            logger: ChessMoverLogger instance
        """
        self.gantry = gantry_controller
        self.servos = servo_controller
        self.log = logger
        self.results: List[DiagnosticResult] = []

    def run_all(self, progress_callback: Callable[[str, int], None] = None) -> bool:
        """
        Run all diagnostic tests.

        Args:
            progress_callback: Optional callback(message, percent) for progress updates

        Returns:
            bool: True if all tests passed
        """
        self.results.clear()
        tests = [
            ("Serial Connection", self._test_serial_connection),
            ("GRBL Communication", self._test_grbl_communication),
            ("Servo Initialization", self._test_servo_init),
            ("Lift Servo Movement", self._test_lift_servo),
            ("Gripper Servo Movement", self._test_gripper_servo),
        ]

        total = len(tests)
        for i, (name, test_fn) in enumerate(tests):
            if progress_callback:
                progress_callback(f"Testing: {name}", int((i / total) * 100))

            try:
                result = test_fn()
                self.results.append(result)
                self.log.info(f"Diagnostic: {result}")
            except Exception as e:
                result = DiagnosticResult(name, False, f"Exception: {e}")
                self.results.append(result)
                self.log.error(f"Diagnostic failed: {name}", exc_info=(type(e), e, e.__traceback__))

            time.sleep(0.2)  # Brief pause between tests

        if progress_callback:
            progress_callback("Diagnostics Complete", 100)

        # Return True only if all tests passed
        return all(r.passed for r in self.results)

    def _test_serial_connection(self) -> DiagnosticResult:
        """Test if serial port is accessible."""
        try:
            ports = self.gantry.list_ports()
            if not ports:
                return DiagnosticResult(
                    "Serial Connection",
                    False,
                    "No serial ports detected. Plug in the machine."
                )

            return DiagnosticResult(
                "Serial Connection",
                True,
                f"Found {len(ports)} port(s): {', '.join(ports)}"
            )
        except Exception as e:
            return DiagnosticResult("Serial Connection", False, str(e))

    def _test_grbl_communication(self) -> DiagnosticResult:
        """Test GRBL communication."""
        if not self.gantry.is_connected:
            return DiagnosticResult(
                "GRBL Communication",
                False,
                "Not connected. Connect to serial port first."
            )

        try:
            # Send status query
            self.gantry.send("?")
            time.sleep(0.1)

            # Check for response
            response = self.gantry.read_line_nowait()
            if response:
                return DiagnosticResult(
                    "GRBL Communication",
                    True,
                    f"GRBL responding: {response[:50]}"
                )
            else:
                return DiagnosticResult(
                    "GRBL Communication",
                    False,
                    "No response from GRBL"
                )
        except Exception as e:
            return DiagnosticResult("GRBL Communication", False, str(e))

    def _test_servo_init(self) -> DiagnosticResult:
        """Test servo controller initialization."""
        try:
            status = self.servos.get_status()

            if not isinstance(status, dict):
                return DiagnosticResult(
                    "Servo Initialization",
                    False,
                    "Invalid status response"
                )

            # Check required keys
            required_keys = ['lift_pos', 'grip_pos', 'lift_state', 'grip_state']
            missing = [k for k in required_keys if k not in status]

            if missing:
                return DiagnosticResult(
                    "Servo Initialization",
                    False,
                    f"Missing status keys: {missing}"
                )

            return DiagnosticResult(
                "Servo Initialization",
                True,
                f"Lift: {status['lift_state']}, Gripper: {status['grip_state']}"
            )
        except Exception as e:
            return DiagnosticResult("Servo Initialization", False, str(e))

    def _test_lift_servo(self) -> DiagnosticResult:
        """Test lift servo movement."""
        try:
            # Get initial position
            initial_pos = self.servos.get_status()['lift_pos']

            # Test increment
            self.servos.lift_increment(1)
            time.sleep(0.1)

            new_pos = self.servos.get_status()['lift_pos']

            # Check if position changed
            if new_pos == initial_pos:
                # Might be at limit, try other direction
                self.servos.lift_increment(-1)
                time.sleep(0.1)
                new_pos = self.servos.get_status()['lift_pos']

            if new_pos != initial_pos:
                # Restore original position
                while self.servos.get_status()['lift_pos'] != initial_pos:
                    direction = 1 if initial_pos > new_pos else -1
                    self.servos.lift_increment(direction)
                    time.sleep(0.05)
                    if abs(self.servos.get_status()['lift_pos'] - initial_pos) < 1:
                        break

                return DiagnosticResult(
                    "Lift Servo Movement",
                    True,
                    f"Moved from {initial_pos}° to {new_pos}°"
                )
            else:
                return DiagnosticResult(
                    "Lift Servo Movement",
                    False,
                    "Position did not change (may be at both limits)"
                )

        except Exception as e:
            return DiagnosticResult("Lift Servo Movement", False, str(e))

    def _test_gripper_servo(self) -> DiagnosticResult:
        """Test gripper servo movement."""
        try:
            # Get initial position
            initial_pos = self.servos.get_status()['grip_pos']

            # Test increment
            self.servos.grip_increment(1)
            time.sleep(0.1)

            new_pos = self.servos.get_status()['grip_pos']

            # Check if position changed
            if new_pos == initial_pos:
                # Might be at limit, try other direction
                self.servos.grip_increment(-1)
                time.sleep(0.1)
                new_pos = self.servos.get_status()['grip_pos']

            if new_pos != initial_pos:
                # Restore original position
                while self.servos.get_status()['grip_pos'] != initial_pos:
                    direction = 1 if initial_pos > new_pos else -1
                    self.servos.grip_increment(direction)
                    time.sleep(0.05)
                    if abs(self.servos.get_status()['grip_pos'] - initial_pos) < 1:
                        break

                return DiagnosticResult(
                    "Gripper Servo Movement",
                    True,
                    f"Moved from {initial_pos}° to {new_pos}°"
                )
            else:
                return DiagnosticResult(
                    "Gripper Servo Movement",
                    False,
                    "Position did not change (may be at both limits)"
                )

        except Exception as e:
            return DiagnosticResult("Gripper Servo Movement", False, str(e))

    def get_summary(self) -> Dict[str, any]:
        """Get diagnostic summary."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'success_rate': (passed / total * 100) if total > 0 else 0,
            'all_passed': failed == 0,
            'results': self.results
        }
