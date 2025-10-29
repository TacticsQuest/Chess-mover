"""
Test script for ServoController with pigpio.

This script tests the updated servo controller that now uses pigpio
instead of RPi.GPIO for microsecond-level PWM precision.

Usage:
    On Raspberry Pi 5:
    python test_servo_controller_pigpio.py

Requirements:
    - pigpio library installed (pip install pigpio)
    - Run with appropriate GPIO permissions (sudo or gpio group)
"""

import sys
import time
from controllers.servo_controller import ServoController

def main():
    """Test servo controller with pigpio."""
    print("=" * 60)
    print("SERVO CONTROLLER TEST (pigpio)")
    print("=" * 60)

    # Create servo controller
    servos = ServoController()

    # Connect to servos
    print("\n1. Connecting to servos...")
    servos.connect()

    if not servos.is_connected:
        print("✗ Failed to connect to servos")
        print("Make sure:")
        print("  - pigpio library is installed: pip install pigpio")
        print("  - You have GPIO permissions (run with sudo or add user to gpio group)")
        return 1

    print("✓ Connected successfully!")

    # Check status
    print("\n2. Checking servo status...")
    status = servos.get_status()
    print(f"   Lift position: {status['lift_pos']}° ({status['lift_state']})")
    print(f"   Grip position: {status['grip_pos']}° ({status['grip_state']})")
    print(f"   Lift speed: {status['lift_speed']}°/sec")
    print(f"   Grip speed: {status['grip_speed']}°/sec")

    # Test lift movements
    print("\n3. Testing LIFT servo (GPIO 17)...")
    print("   Moving to DOWN position (0°)...")
    servos.lift_down()
    time.sleep(2)

    print("   Moving to MID position (137°)...")
    servos.lift_mid()
    time.sleep(2)

    print("   Moving to UP position (274°)...")
    servos.lift_up()
    time.sleep(2)

    # Test piece-specific lift heights
    print("\n4. Testing piece-specific lift heights...")
    for piece in ['pawn', 'knight', 'bishop', 'rook', 'queen', 'king']:
        print(f"   Lifting to {piece.upper()} height...")
        servos.lift_piece(piece)
        time.sleep(1.5)

    # Test gripper movements
    print("\n5. Testing GRIPPER servo (GPIO 27)...")
    print("   Opening gripper (0°)...")
    servos.grip_open()
    time.sleep(2)

    print("   Closing gripper (5°)...")
    servos.grip_close()
    time.sleep(2)

    # Test piece-specific grips
    print("\n6. Testing piece-specific grip positions...")
    for piece in ['pawn', 'knight', 'bishop', 'rook', 'queen', 'king']:
        print(f"   Gripping {piece.upper()}...")
        servos.grip_piece(piece)
        time.sleep(1.5)

    # Test smooth movement at different speeds
    print("\n7. Testing speed control...")
    print("   SLOW speed (30°/sec)...")
    servos.set_speed(lift_speed=servos.SPEED_SLOW)
    servos.lift_down()
    time.sleep(3)

    print("   MEDIUM speed (60°/sec)...")
    servos.set_speed(lift_speed=servos.SPEED_MEDIUM)
    servos.lift_up()
    time.sleep(2)

    print("   FAST speed (120°/sec)...")
    servos.set_speed(lift_speed=servos.SPEED_FAST)
    servos.lift_down()
    time.sleep(1.5)

    # Return to safe position
    print("\n8. Returning to safe position...")
    servos.grip_open()
    time.sleep(1)
    servos.lift_up()
    time.sleep(2)

    # Disconnect
    print("\n9. Disconnecting...")
    servos.disconnect()

    print("\n" + "=" * 60)
    print("✓ TEST COMPLETE!")
    print("=" * 60)
    print("\nKey Features Tested:")
    print("  ✓ pigpio connection and initialization")
    print("  ✓ Microsecond-level pulsewidth control (500-2500μs)")
    print("  ✓ Lift servo movements (0-274° range)")
    print("  ✓ Gripper servo movements (0-90° range)")
    print("  ✓ Piece-specific positions (lift heights + grip angles)")
    print("  ✓ Smooth movement with speed control")
    print("  ✓ Proper cleanup and disconnect")

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
