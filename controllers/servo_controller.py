"""
Servo Controller for Chess Mover Machine

Controls:
1. Lift Servo (Rack & Pinion) - Vertical movement
2. Gripper Servo - Open/Close for piece gripping

Phase 1 (Windows): Stubs for testing UI
Phase 3 (Raspberry Pi): Direct GPIO PWM control
"""

class ServoController:
    """
    Controls lift and gripper servos.

    Lift Positions:
    - UP: Raised position (clear of pieces)
    - DOWN: Lowered position (touching board)

    Gripper Positions:
    - OPEN: Fully open (release piece)
    - CLOSED: Gripping piece (controlled force)

    Safety Features:
    - Position limits to prevent over-extension
    - Force limiting on gripper
    - Current position tracking
    """

    # Servo positions (PWM duty cycle controlled via GPIO)
    # USABLE RANGE: 0° to 274° (75% of 365° gear rotation)
    # The gear can physically rotate 365° total, but we limit to 75% (274°) to prevent binding
    # Note: Standard servos go 0-180°, but with extended range servo or continuous rotation,
    # we can use up to 274° (mapped through GPIO PWM duty cycle)
    LIFT_UP_POS = 274      # Degrees (fully up, clear of all pieces) - 75% of 365°
    LIFT_DOWN_POS = 0      # Degrees (at board level, gripper touching board)
    LIFT_MID_POS = 137     # Degrees (halfway between 0° and 274°)

    # Piece-specific lift heights (degrees) for gripping
    # Height needed to clear the top of each piece when gripped
    # Scaled to 0°-274° range (274° total range)
    LIFT_HEIGHTS = {
        'king': 265,     # Tallest piece (needs most clearance)
        'queen': 250,    # Second tallest
        'bishop': 235,   # Medium-tall (pointed top)
        'knight': 225,   # Medium (horse head)
        'rook': 220,     # Medium (castle turrets)
        'pawn': 200,     # Shortest piece (needs least clearance)
        'default': 235   # Fallback if piece type unknown
    }

    GRIP_OPEN_POS = 0      # Degrees (fully open)
    GRIP_CLOSED_POS = 5    # Degrees (fully closed - 5° total range)

    # Piece-specific grip positions (degrees)
    # These will need calibration with your actual pieces
    # Range: 0° (open) to 5° (closed)
    GRIP_POSITIONS = {
        'king': 5,       # Largest piece (widest base)
        'queen': 5,      # Second largest
        'rook': 4,       # Medium-large (castle turrets)
        'bishop': 4,     # Medium (pointed top)
        'knight': 4,     # Medium (horse head)
        'pawn': 3,       # Smallest piece
        'default': 4     # Fallback if piece type unknown
    }

    # Step size for incremental movement
    LIFT_STEP = 5          # Degrees per step
    GRIP_STEP = 1          # Degrees per step (small range, 0-5°)

    # Smooth movement settings (prevents jerky motion and stress on servos)
    SMOOTH_MOVEMENT = True              # Enable smooth movement
    SMOOTH_STEP_SIZE = 2                # Degrees per step (smaller = smoother)
    SMOOTH_DELAY_MS = 15                # Milliseconds between steps (15ms = ~60 FPS)

    # Speed presets (in degrees per second)
    SPEED_SLOW = 30       # 30°/sec (gentle, for delicate operations)
    SPEED_MEDIUM = 60     # 60°/sec (normal speed)
    SPEED_FAST = 120      # 120°/sec (quick positioning)

    def __init__(self, log_fn=print):
        self.log = log_fn

        # Current positions (start at safe positions)
        self.lift_pos = self.LIFT_UP_POS  # Start in up position (135°)
        self.grip_pos = self.GRIP_OPEN_POS  # Start open (0°)

        # Hardware connection (Phase 3: pigpio)
        self.pi = None            # pigpio connection object
        self.lift_pin = 17        # GPIO pin 17 (Physical PIN 11) for Z-axis lift servo
        self.grip_pin = 27        # GPIO pin 27 (Physical PIN 13) for gripper servo

        # State tracking
        self.is_connected = False

        # Movement speed (default to slow for safety)
        self.lift_speed = self.SPEED_SLOW     # Slow by default
        self.grip_speed = self.SPEED_SLOW     # Slow by default (protect pieces)

        # Auto-load calibration if available
        self.load_calibration()

    def connect(self):
        """
        Initialize pigpio connection for precise servo control.
        pigpio provides microsecond-level PWM precision for smooth servo operation.
        """
        try:
            # Phase 3: Raspberry Pi pigpio Control (best for servos)
            import pigpio
            self.pi = pigpio.pi()

            if not self.pi.connected:
                raise Exception("Failed to connect to pigpiod daemon")

            # Set servo pins to output mode
            self.pi.set_mode(self.lift_pin, pigpio.OUTPUT)
            self.pi.set_mode(self.grip_pin, pigpio.OUTPUT)

            # Initialize servos to safe positions (off)
            self.pi.set_servo_pulsewidth(self.lift_pin, 0)
            self.pi.set_servo_pulsewidth(self.grip_pin, 0)

            self.is_connected = True
            self.log(f"[SERVO] Connected via pigpio to GPIO {self.lift_pin} (lift) and {self.grip_pin} (gripper)")
            self.log(f"[SERVO] Using hardware PWM for microsecond precision")

        except Exception as e:
            self.log(f"[SERVO] Connection failed: {e}")
            self.log(f"[SERVO] Tip: Ensure pigpio library is installed and you have GPIO permissions")
            self.is_connected = False
            self.pi = None

    def _angle_to_pulsewidth(self, angle: int, max_angle: int = 180) -> int:
        """
        Convert angle to PWM pulsewidth in microseconds (for pigpio).

        Standard servo timing:
        - 500μs pulse = 0° (minimum)
        - 1500μs pulse = 90° (center)
        - 2500μs pulse = 180° (maximum)

        For extended range (0-274°), we scale accordingly.

        Args:
            angle: Desired angle
            max_angle: Maximum angle range (180 or 274)

        Returns:
            Pulsewidth in microseconds (500-2500μs for standard servos)
        """
        # Standard servo uses 500-2500μs pulsewidth for 0-180°
        # For 0-274° we extend the range proportionally
        min_pulse = 500   # microseconds
        max_pulse = 2500  # microseconds

        # Scale angle to pulsewidth
        pulse_range = max_pulse - min_pulse
        pulsewidth = min_pulse + (angle / max_angle) * pulse_range

        return int(pulsewidth)

    def _set_servo(self, pin: int, angle: int):
        """
        Set servo to specific angle (instant movement) using pigpio.

        Args:
            pin: GPIO pin number (17 for lift, 27 for gripper)
            angle: Angle in degrees (0-274 for lift servo, 0-90 for gripper)
        """
        # Clamp angle to valid range based on pin
        if pin == self.lift_pin:
            # Lift servo: 0° to 274° (75% of 365°)
            angle = max(0, min(274, angle))
            max_angle = 274
        else:
            # Gripper servo: limited to 0° to 90°
            angle = max(0, min(90, angle))
            max_angle = 180  # Standard servo range for pulsewidth calculation

        if self.is_connected and self.pi:
            # Phase 3: Real hardware (pigpio)
            pulsewidth = self._angle_to_pulsewidth(angle, max_angle)
            self.pi.set_servo_pulsewidth(pin, pulsewidth)
            self.log(f"[SERVO] GPIO {pin} → {angle}° (pulsewidth: {pulsewidth}μs)")
        else:
            # Phase 1: Stub
            self.log(f"[SERVO] GPIO {pin} → {angle}° (stub)")

    def _set_servo_smooth(self, pin: int, target_angle: int, speed_deg_per_sec: int):
        """
        Move servo smoothly to target angle at specified speed.
        Prevents jerky motion and reduces stress on servos.

        Args:
            pin: GPIO pin number (12 for lift, 13 for gripper)
            target_angle: Target angle in degrees (0-274 for lift, 0-180 for gripper)
            speed_deg_per_sec: Movement speed in degrees per second

        Example:
            _set_servo_smooth(12, 90, SPEED_SLOW)  # Move lift to 90° slowly
        """
        import time

        # Clamp target to valid range based on pin
        if pin == self.lift_pin:
            target_angle = max(0, min(274, target_angle))
        else:
            target_angle = max(0, min(90, target_angle))

        # Get current position
        if pin == self.lift_pin:
            current_angle = self.lift_pos
        elif pin == self.grip_pin:
            current_angle = self.grip_pos
        else:
            current_angle = 90  # Default if unknown pin

        # Calculate movement
        delta = target_angle - current_angle

        if abs(delta) < 1:
            # Already at target
            return

        # Calculate delay between steps based on speed
        # delay = step_size / speed
        delay_sec = self.SMOOTH_STEP_SIZE / speed_deg_per_sec

        # Determine step direction
        step = self.SMOOTH_STEP_SIZE if delta > 0 else -self.SMOOTH_STEP_SIZE

        # Move smoothly
        angle = current_angle
        while abs(target_angle - angle) > self.SMOOTH_STEP_SIZE:
            angle += step
            self._set_servo(pin, int(angle))

            # Update tracked position
            if pin == self.lift_pin:
                self.lift_pos = int(angle)
            elif pin == self.grip_pin:
                self.grip_pos = int(angle)

            time.sleep(delay_sec)

        # Final position (ensure we hit exact target)
        self._set_servo(pin, target_angle)

        # Update tracked position
        if pin == self.lift_pin:
            self.lift_pos = target_angle
        elif pin == self.grip_pin:
            self.grip_pos = target_angle

    # ========== LIFT SERVO (Rack & Pinion) ==========

    def lift_up(self):
        """Raise lift to maximum height (smooth, slow movement)."""
        self.log(f"[SERVO] Lift UP → {self.LIFT_UP_POS}° (smooth, {self.lift_speed}°/sec)")
        if self.SMOOTH_MOVEMENT:
            self._set_servo_smooth(self.lift_pin, self.LIFT_UP_POS, self.lift_speed)
        else:
            self.lift_pos = self.LIFT_UP_POS
            self._set_servo(self.lift_pin, self.lift_pos)

    def lift_down(self):
        """Lower lift to board level (smooth, slow movement)."""
        self.log(f"[SERVO] Lift DOWN → {self.LIFT_DOWN_POS}° (smooth, {self.lift_speed}°/sec)")
        if self.SMOOTH_MOVEMENT:
            self._set_servo_smooth(self.lift_pin, self.LIFT_DOWN_POS, self.lift_speed)
        else:
            self.lift_pos = self.LIFT_DOWN_POS
            self._set_servo(self.lift_pin, self.lift_pos)

    def lift_mid(self):
        """Move lift to middle position (smooth, slow movement)."""
        self.log(f"[SERVO] Lift MID → {self.LIFT_MID_POS}° (smooth, {self.lift_speed}°/sec)")
        if self.SMOOTH_MOVEMENT:
            self._set_servo_smooth(self.lift_pin, self.LIFT_MID_POS, self.lift_speed)
        else:
            self.lift_pos = self.LIFT_MID_POS
            self._set_servo(self.lift_pin, self.lift_pos)

    def lift_piece(self, piece_type: str):
        """
        Lift to the optimal height for a specific piece type.
        Uses piece-specific heights to clear the piece without going too high.

        Args:
            piece_type: 'king', 'queen', 'rook', 'bishop', 'knight', or 'pawn'

        Example:
            # After gripping a king
            grip_piece('king')
            lift_piece('king')  # Lifts to 175° (enough to clear king)

            # After gripping a pawn
            grip_piece('pawn')
            lift_piece('pawn')  # Lifts to 155° (enough to clear pawn)
        """
        piece_type = piece_type.lower()
        lift_height = self.LIFT_HEIGHTS.get(piece_type, self.LIFT_HEIGHTS['default'])

        self.log(f"[SERVO] Lift {piece_type.upper()} → {lift_height}° (smooth, {self.lift_speed}°/sec)")

        if self.SMOOTH_MOVEMENT:
            self._set_servo_smooth(self.lift_pin, lift_height, self.lift_speed)
        else:
            self.lift_pos = lift_height
            self._set_servo(self.lift_pin, lift_height)

    def lift_increment(self, direction: int):
        """
        Move lift incrementally.

        Args:
            direction: +1 for up, -1 for down
        """
        new_pos = self.lift_pos + (direction * self.LIFT_STEP)

        # Clamp to valid range (0° to 274° - prevents mechanical binding at 75% of 365°)
        new_pos = max(self.LIFT_DOWN_POS, min(self.LIFT_UP_POS, new_pos))

        if new_pos != self.lift_pos:
            self.lift_pos = new_pos
            self._set_servo(self.lift_pin, self.lift_pos)
            self.log(f"[SERVO] Lift → {self.lift_pos}° ({'up' if direction > 0 else 'down'})")
        else:
            limit_type = "UP (274°)" if direction > 0 else "DOWN (0°)"
            self.log(f"[SERVO] Lift at {limit_type} limit")

    # ========== GRIPPER SERVO ==========

    def grip_open(self):
        """Open gripper fully (smooth, slow movement to prevent damage)."""
        self.log(f"[SERVO] Gripper OPEN → {self.GRIP_OPEN_POS}° (smooth, {self.grip_speed}°/sec)")
        if self.SMOOTH_MOVEMENT:
            self._set_servo_smooth(self.grip_pin, self.GRIP_OPEN_POS, self.grip_speed)
        else:
            self.grip_pos = self.GRIP_OPEN_POS
            self._set_servo(self.grip_pin, self.grip_pos)

    def grip_close(self):
        """
        Close gripper to default position (smooth, slow movement).
        For piece-specific gripping, use grip_piece() instead.
        """
        self.log(f"[SERVO] Gripper CLOSE → {self.GRIP_CLOSED_POS}° (smooth, {self.grip_speed}°/sec)")
        if self.SMOOTH_MOVEMENT:
            self._set_servo_smooth(self.grip_pin, self.GRIP_CLOSED_POS, self.grip_speed)
        else:
            self.grip_pos = self.GRIP_CLOSED_POS
            self._set_servo(self.grip_pin, self.grip_pos)

    def grip_piece(self, piece_type: str):
        """
        Close gripper to the optimal position for a specific piece type.
        Uses piece-specific grip positions for secure, non-damaging grip.

        Args:
            piece_type: 'king', 'queen', 'rook', 'bishop', 'knight', or 'pawn'

        Example:
            grip_piece('king')   # Grips king (42°)
            grip_piece('pawn')   # Grips pawn (28°)
        """
        piece_type = piece_type.lower()
        grip_angle = self.GRIP_POSITIONS.get(piece_type, self.GRIP_POSITIONS['default'])

        self.log(f"[SERVO] Gripper GRIP {piece_type.upper()} → {grip_angle}° (smooth, {self.grip_speed}°/sec)")

        if self.SMOOTH_MOVEMENT:
            self._set_servo_smooth(self.grip_pin, grip_angle, self.grip_speed)
        else:
            self.grip_pos = grip_angle
            self._set_servo(self.grip_pin, grip_angle)

    def grip_increment(self, direction: int):
        """
        Move gripper incrementally.

        Args:
            direction: +1 for close, -1 for open
        """
        new_pos = self.grip_pos + (direction * self.GRIP_STEP)

        # Clamp to valid range
        new_pos = max(self.GRIP_OPEN_POS, min(self.GRIP_CLOSED_POS, new_pos))

        if new_pos != self.grip_pos:
            self.grip_pos = new_pos
            self._set_servo(self.grip_pin, self.grip_pos)
            action = 'closing' if direction > 0 else 'opening'
            self.log(f"[SERVO] Gripper → {self.grip_pos}° ({action})")
        else:
            limit = 'closed' if direction > 0 else 'open'
            self.log(f"[SERVO] Gripper at limit ({limit}, {self.grip_pos}°)")

    # ========== CALIBRATION ==========

    def calibrate_grip(self, piece_type: str, grip_angle: int):
        """
        Calibrate grip position for a specific piece type.
        Use this to fine-tune grip positions for your actual chess pieces.

        Args:
            piece_type: 'king', 'queen', 'rook', 'bishop', 'knight', or 'pawn'
            grip_angle: Optimal grip angle in degrees (0-180)

        Example:
            # Test gripping a pawn
            servos.grip_piece('pawn')  # Uses current setting (28°)

            # If too loose or tight, calibrate:
            servos.calibrate_grip('pawn', 30)  # Adjust to 30°
            servos.grip_piece('pawn')  # Now uses 30°
        """
        piece_type = piece_type.lower()

        if piece_type not in self.GRIP_POSITIONS:
            self.log(f"[SERVO] ✗ Unknown piece type: {piece_type}")
            self.log(f"[SERVO] Valid types: {', '.join(self.GRIP_POSITIONS.keys())}")
            return

        # Clamp to valid servo range (gripper limited to 90°)
        grip_angle = max(0, min(90, grip_angle))

        # Update the position
        old_angle = self.GRIP_POSITIONS[piece_type]
        self.GRIP_POSITIONS[piece_type] = grip_angle

        self.log(f"[SERVO] ✓ Calibrated {piece_type.upper()} grip: {old_angle}° → {grip_angle}°")
        self.log(f"[SERVO] Test with: servos.grip_piece('{piece_type}')")

    def calibrate_lift(self, piece_type: str, lift_height: int):
        """
        Calibrate lift height for a specific piece type.
        Use this to find the optimal height to clear each piece.

        Args:
            piece_type: 'king', 'queen', 'rook', 'bishop', 'knight', or 'pawn'
            lift_height: Optimal lift height in degrees (0-180)

        Example:
            # Test lifting a king
            lift_piece('king')  # Uses current setting (175°)

            # If piece hits other pieces or lifts too high, calibrate:
            servos.calibrate_lift('king', 170)  # Adjust to 170°
            servos.lift_piece('king')  # Now uses 170°
        """
        piece_type = piece_type.lower()

        if piece_type not in self.LIFT_HEIGHTS:
            self.log(f"[SERVO] ✗ Unknown piece type: {piece_type}")
            self.log(f"[SERVO] Valid types: {', '.join(self.LIFT_HEIGHTS.keys())}")
            return

        # Clamp to valid servo range
        lift_height = max(0, min(180, lift_height))

        # Update the position
        old_height = self.LIFT_HEIGHTS[piece_type]
        self.LIFT_HEIGHTS[piece_type] = lift_height

        self.log(f"[SERVO] ✓ Calibrated {piece_type.upper()} lift: {old_height}° → {lift_height}°")
        self.log(f"[SERVO] Test with: servos.lift_piece('{piece_type}')")

    def save_calibration(self, filepath: str = "config/servo_calibration.yaml"):
        """
        Save all calibrated positions (grip + lift) to file.
        Call this after calibrating all pieces to persist settings.

        Args:
            filepath: Path to save calibration data
        """
        import yaml
        import os

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Save calibration data
        data = {
            'grip_positions': self.GRIP_POSITIONS,
            'lift_heights': self.LIFT_HEIGHTS,
            'notes': 'Calibrated grip positions and lift heights for each chess piece type'
        }

        with open(filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

        self.log(f"[SERVO] ✓ Calibration saved to: {filepath}")

    def load_calibration(self, filepath: str = "config/servo_calibration.yaml"):
        """
        Load all calibrated positions (grip + lift) from file.
        Call this on startup to restore your calibrated settings.

        Args:
            filepath: Path to load calibration data from
        """
        import yaml
        import os

        if not os.path.exists(filepath):
            self.log(f"[SERVO] No calibration file found: {filepath}")
            self.log(f"[SERVO] Using default positions")
            return

        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)

        if 'grip_positions' in data:
            self.GRIP_POSITIONS.update(data['grip_positions'])
            self.log(f"[SERVO] ✓ Grip positions loaded")

        if 'lift_heights' in data:
            self.LIFT_HEIGHTS.update(data['lift_heights'])
            self.log(f"[SERVO] ✓ Lift heights loaded")

        self.log(f"[SERVO] ✓ Calibration loaded from: {filepath}")

    # ========== SPEED CONTROL ==========

    def set_speed(self, lift_speed: int = None, grip_speed: int = None):
        """
        Set movement speeds for lift and gripper.

        Args:
            lift_speed: Lift speed in degrees/sec (None = no change)
            grip_speed: Gripper speed in degrees/sec (None = no change)

        Example:
            set_speed(SPEED_SLOW, SPEED_SLOW)      # Both slow (30°/sec)
            set_speed(SPEED_MEDIUM, SPEED_SLOW)    # Lift medium, grip slow
            set_speed(grip_speed=SPEED_FAST)       # Only change grip speed
        """
        if lift_speed is not None:
            self.lift_speed = lift_speed
            self.log(f"[SERVO] Lift speed set to {lift_speed}°/sec")

        if grip_speed is not None:
            self.grip_speed = grip_speed
            self.log(f"[SERVO] Gripper speed set to {grip_speed}°/sec")

    # ========== STATUS ==========

    def get_status(self) -> dict:
        """Get current servo positions and settings."""
        return {
            'connected': self.is_connected,
            'lift_pos': self.lift_pos,
            'grip_pos': self.grip_pos,
            'lift_state': self._get_lift_state(),
            'grip_state': self._get_grip_state(),
            'lift_speed': self.lift_speed,
            'grip_speed': self.grip_speed,
            'smooth_movement': self.SMOOTH_MOVEMENT
        }

    def _get_lift_state(self) -> str:
        """Get human-readable lift state."""
        if self.lift_pos >= self.LIFT_UP_POS - 5:
            return "UP"
        elif self.lift_pos <= self.LIFT_DOWN_POS + 5:
            return "DOWN"
        else:
            return "MID"

    def _get_grip_state(self) -> str:
        """Get human-readable gripper state."""
        if self.grip_pos <= self.GRIP_OPEN_POS + 3:
            return "OPEN"
        elif self.grip_pos >= self.GRIP_CLOSED_POS - 3:
            return "CLOSED"
        else:
            return "PARTIAL"

    # ========== CLEANUP ==========

    def disconnect(self):
        """
        Clean up pigpio resources on shutdown.
        IMPORTANT: Always call this when shutting down to release GPIO pins.
        """
        if self.is_connected and self.pi:
            try:
                # Turn off servo signals (set pulsewidth to 0)
                self.pi.set_servo_pulsewidth(self.lift_pin, 0)
                self.pi.set_servo_pulsewidth(self.grip_pin, 0)

                # Stop pigpio connection
                self.pi.stop()
                self.pi = None

                self.is_connected = False
                self.log("[SERVO] Disconnected and cleaned up pigpio resources")

            except Exception as e:
                self.log(f"[SERVO] Cleanup error: {e}")
        else:
            self.log("[SERVO] Already disconnected")

    def __del__(self):
        """Destructor - ensure GPIO cleanup on object deletion."""
        if self.is_connected:
            self.disconnect()
