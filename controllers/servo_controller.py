"""
Servo Controller for Chess Mover Machine

Controls:
1. Lift Servo (Rack & Pinion) - Vertical movement
2. Gripper Servo - Open/Close for piece gripping

Phase 1 (Windows): Stubs for testing UI
Phase 3 (Raspberry Pi): Real PCA9685 PWM control
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

    # Servo positions (PWM values for PCA9685)
    # These will be calibrated in Phase 3
    LIFT_UP_POS = 180      # Degrees (fully up)
    LIFT_DOWN_POS = 90     # Degrees (at board level)
    LIFT_MID_POS = 135     # Degrees (halfway)

    GRIP_OPEN_POS = 0      # Degrees (fully open)
    GRIP_CLOSED_POS = 45   # Degrees (closed on piece)

    # Step size for incremental movement
    LIFT_STEP = 5          # Degrees per step
    GRIP_STEP = 3          # Degrees per step

    def __init__(self, log_fn=print):
        self.log = log_fn

        # Current positions
        self.lift_pos = self.LIFT_UP_POS  # Start in up position
        self.grip_pos = self.GRIP_OPEN_POS  # Start open

        # Hardware connection (Phase 3)
        self.pca9685 = None
        self.lift_channel = 0  # PCA9685 channel for lift servo
        self.grip_channel = 1  # PCA9685 channel for gripper servo

        # State tracking
        self.is_connected = False

    def connect(self):
        """
        Initialize PCA9685 connection (Phase 3 only).
        For Phase 1 (Windows), this is a stub.
        """
        try:
            # Phase 3: Uncomment this when on Raspberry Pi
            # from adafruit_servokit import ServoKit
            # self.pca9685 = ServoKit(channels=16)
            # self.is_connected = True
            # self.log("[SERVO] Connected to PCA9685")

            # Phase 1: Stub
            self.log("[SERVO] connect() - stub (Phase 1)")
            self.is_connected = False  # Set to True in Phase 3

        except Exception as e:
            self.log(f"[SERVO] Connection failed: {e}")
            self.is_connected = False

    def _set_servo(self, channel: int, angle: int):
        """
        Set servo to specific angle.

        Args:
            channel: PCA9685 channel (0-15)
            angle: Angle in degrees (0-180)
        """
        # Clamp angle to valid range
        angle = max(0, min(180, angle))

        if self.is_connected and self.pca9685:
            # Phase 3: Real hardware
            self.pca9685.servo[channel].angle = angle
            self.log(f"[SERVO] Channel {channel} → {angle}°")
        else:
            # Phase 1: Stub
            self.log(f"[SERVO] Channel {channel} → {angle}° (stub)")

    # ========== LIFT SERVO (Rack & Pinion) ==========

    def lift_up(self):
        """Raise lift to maximum height."""
        self.lift_pos = self.LIFT_UP_POS
        self._set_servo(self.lift_channel, self.lift_pos)
        self.log(f"[SERVO] Lift UP → {self.lift_pos}°")

    def lift_down(self):
        """Lower lift to board level."""
        self.lift_pos = self.LIFT_DOWN_POS
        self._set_servo(self.lift_channel, self.lift_pos)
        self.log(f"[SERVO] Lift DOWN → {self.lift_pos}°")

    def lift_mid(self):
        """Move lift to middle position."""
        self.lift_pos = self.LIFT_MID_POS
        self._set_servo(self.lift_channel, self.lift_pos)
        self.log(f"[SERVO] Lift MID → {self.lift_pos}°")

    def lift_increment(self, direction: int):
        """
        Move lift incrementally.

        Args:
            direction: +1 for up, -1 for down
        """
        new_pos = self.lift_pos + (direction * self.LIFT_STEP)

        # Clamp to valid range
        new_pos = max(self.LIFT_DOWN_POS, min(self.LIFT_UP_POS, new_pos))

        if new_pos != self.lift_pos:
            self.lift_pos = new_pos
            self._set_servo(self.lift_channel, self.lift_pos)
            self.log(f"[SERVO] Lift → {self.lift_pos}° ({'up' if direction > 0 else 'down'})")
        else:
            self.log(f"[SERVO] Lift at limit ({self.lift_pos}°)")

    # ========== GRIPPER SERVO ==========

    def grip_open(self):
        """Open gripper fully."""
        self.grip_pos = self.GRIP_OPEN_POS
        self._set_servo(self.grip_channel, self.grip_pos)
        self.log(f"[SERVO] Gripper OPEN → {self.grip_pos}°")

    def grip_close(self):
        """
        Close gripper on piece.
        Uses controlled force to avoid damaging pieces.
        """
        self.grip_pos = self.GRIP_CLOSED_POS
        self._set_servo(self.grip_channel, self.grip_pos)
        self.log(f"[SERVO] Gripper CLOSE → {self.grip_pos}°")

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
            self._set_servo(self.grip_channel, self.grip_pos)
            action = 'closing' if direction > 0 else 'opening'
            self.log(f"[SERVO] Gripper → {self.grip_pos}° ({action})")
        else:
            limit = 'closed' if direction > 0 else 'open'
            self.log(f"[SERVO] Gripper at limit ({limit}, {self.grip_pos}°)")

    # ========== STATUS ==========

    def get_status(self) -> dict:
        """Get current servo positions."""
        return {
            'connected': self.is_connected,
            'lift_pos': self.lift_pos,
            'grip_pos': self.grip_pos,
            'lift_state': self._get_lift_state(),
            'grip_state': self._get_grip_state()
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
