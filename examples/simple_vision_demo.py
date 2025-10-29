#!/usr/bin/env python3
"""
Simple demo of chess vision system with Pi AI Camera

This demonstrates the basic usage of the ChessVision class
to scan the board and detect pieces.

Usage:
    python examples/simple_vision_demo.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vision.chess_vision import ChessVision
import cv2


def main():
    """Simple vision demo."""
    print("=" * 70)
    print("  Chess Vision Demo")
    print("  Using 99.372% Accurate Piece Classifier")
    print("=" * 70)

    # Initialize vision system
    print("\n[1/4] Initializing vision system...")
    cv = ChessVision(
        camera_index=0,
        model_path="models/chess_classifier_best.onnx",
        conf_thresh=0.80
    )
    print("✓ Vision system initialized")

    # Calibrate board (if not already calibrated)
    if cv.geom is None:
        print("\n[2/4] Calibrating board...")
        print("Place ArUco markers on board corners (IDs 0, 1, 2, 3)")
        input("Press Enter when ready...")

        success = cv.calibrate()
        if not success:
            print("✗ Calibration failed!")
            return
        print("✓ Board calibrated")
    else:
        print("\n[2/4] Board already calibrated ✓")

    # Scan board
    print("\n[3/4] Scanning board...")
    state = cv.scan_board()

    if state is None:
        print("✗ Failed to scan board")
        return

    print("✓ Board scanned successfully")

    # Display results
    print("\n[4/4] Results:")
    print("-" * 70)

    # FEN notation
    print(f"\nFEN (piece placement):")
    print(f"  {state['fen']}")

    # Piece count
    piece_count = sum(1 for r in range(8) for c in range(8)
                     if state['predictions'][r][c]['class'] != 'empty')
    print(f"\nTotal pieces detected: {piece_count}")

    # Average confidence
    import numpy as np
    avg_conf = np.mean(state['confidences'])
    print(f"Average confidence: {avg_conf:.1%}")

    # Sample squares
    print(f"\nSample squares:")
    for square_name in ['a1', 'e1', 'e4', 'e8', 'h8']:
        # Convert notation to row, col
        col = ord(square_name[0]) - ord('a')
        row = 8 - int(square_name[1])

        pred = state['predictions'][row][col]
        conf = state['confidences'][row][col]

        print(f"  {square_name}: {pred['class']:15s} ({conf:.1%})")

    # Visualize
    print("\n" + "=" * 70)
    print("Creating visualization...")
    vis = cv.visualize_board(state, show_confidence=True)

    # Save
    output_path = Path("board_scan.jpg")
    cv2.imwrite(str(output_path), vis)
    print(f"✓ Saved to {output_path}")

    # Display (if possible)
    try:
        print("\nDisplaying visualization (press any key to close)...")
        cv2.imshow("Chess Board", vis)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except:
        print("(Display not available - running in headless mode)")

    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
