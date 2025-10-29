#!/usr/bin/env python3
"""
Test script for Pi AI Camera with trained chess piece classifier (99.372% accuracy)

This script tests the complete vision pipeline:
1. Camera capture
2. Board detection and calibration
3. Piece classification with trained model
4. Board state recognition
5. Move detection

Usage:
    # Interactive test
    python test_pi_ai_camera.py

    # Automatic test (headless)
    python test_pi_ai_camera.py --auto

Requirements:
    - Pi AI Camera connected
    - ArUco markers on board corners (IDs 0, 1, 2, 3)
    - Trained model at models/chess_classifier_best.onnx
"""

import sys
import cv2
import numpy as np
from pathlib import Path

# Add vision module to path
sys.path.insert(0, str(Path(__file__).parent))

from vision.chess_vision import ChessVision


def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_camera():
    """Test 1: Camera capture"""
    print_section("TEST 1: Camera Capture")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("✗ Failed to open camera")
        return False

    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("✗ Failed to capture frame")
        return False

    h, w = frame.shape[:2]
    print(f"✓ Camera working: {w}x{h}")
    return True


def test_model():
    """Test 2: Model loading"""
    print_section("TEST 2: Model Loading")

    model_path = Path("models/chess_classifier_best.onnx")
    if not model_path.exists():
        print(f"✗ Model not found: {model_path}")
        print("  Run training first: python vision/train_classifier.py")
        return False

    print(f"✓ Model found: {model_path}")
    print(f"  Size: {model_path.stat().st_size / 1024 / 1024:.1f} MB")

    # Try loading with onnxruntime
    try:
        import onnxruntime as ort
        sess = ort.InferenceSession(str(model_path), providers=['CPUExecutionProvider'])
        inputs = sess.get_inputs()
        outputs = sess.get_outputs()
        print(f"✓ Model loaded successfully")
        print(f"  Input: {inputs[0].name}, shape: {inputs[0].shape}")
        print(f"  Output: {outputs[0].name}, shape: {outputs[0].shape}")
        return True
    except ImportError:
        print("⚠ onnxruntime not installed (pip install onnxruntime)")
        return False
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        return False


def test_calibration(cv: ChessVision, auto: bool = False):
    """Test 3: Board calibration"""
    print_section("TEST 3: Board Calibration")

    if auto:
        print("Running automatic calibration...")
        success = cv.calibrate()
    else:
        print("\nPlace ArUco markers on board corners:")
        print("  ID 0: Top-left")
        print("  ID 1: Top-right")
        print("  ID 2: Bottom-right")
        print("  ID 3: Bottom-left")
        input("\nPress Enter when ready...")

        success = cv.calibrate()

    if success:
        print("✓ Calibration successful")
        return True
    else:
        print("✗ Calibration failed")
        print("  Make sure all 4 ArUco markers are visible")
        return False


def test_piece_classification(cv: ChessVision):
    """Test 4: Piece classification"""
    print_section("TEST 4: Piece Classification")

    print("Scanning board...")
    state = cv.scan_board()

    if state is None:
        print("✗ Failed to scan board")
        return False

    print("✓ Board scanned successfully")

    # Print board state
    print("\nBoard State (FEN):")
    print(f"  {state['fen']}")

    # Print piece counts
    predictions = state['predictions']
    piece_counts = {}
    total_pieces = 0

    for r in range(8):
        for c in range(8):
            pred = predictions[r][c]
            class_name = pred['class']
            if class_name != 'empty':
                piece_counts[class_name] = piece_counts.get(class_name, 0) + 1
                total_pieces += 1

    print(f"\nPieces Detected: {total_pieces}")
    for piece, count in sorted(piece_counts.items()):
        print(f"  {piece}: {count}")

    # Show average confidence
    avg_conf = np.mean(state['confidences'])
    print(f"\nAverage Confidence: {avg_conf:.1%}")

    # Show low confidence warnings
    low_conf_squares = []
    for r in range(8):
        for c in range(8):
            conf = state['confidences'][r][c]
            if conf < 0.80 and predictions[r][c]['class'] != 'empty':
                square = chr(ord('a') + c) + str(8 - r)
                low_conf_squares.append((square, conf, predictions[r][c]['class']))

    if low_conf_squares:
        print("\n⚠ Low Confidence Squares:")
        for square, conf, class_name in low_conf_squares:
            print(f"  {square}: {class_name} ({conf:.1%})")

    return True


def test_move_detection(cv: ChessVision, auto: bool = False):
    """Test 5: Move detection"""
    print_section("TEST 5: Move Detection")

    # Scan initial position
    print("Scanning initial position...")
    state1 = cv.scan_board()
    if state1 is None:
        print("✗ Failed to scan initial position")
        return False

    print("✓ Initial position scanned")
    print(f"  FEN: {state1['fen']}")

    if not auto:
        input("\nMake a move, then press Enter...")

    # Scan after move
    print("Scanning after move...")
    state2 = cv.scan_board()
    if state2 is None:
        print("✗ Failed to scan after move")
        return False

    print("✓ Position after move scanned")
    print(f"  FEN: {state2['fen']}")

    # Detect move
    move = cv.detect_move()
    if move is None:
        print("⚠ No move detected (or ambiguous changes)")
        return False

    print("\n✓ Move detected:")
    print(f"  From: {move['notation'][:2]} (row {move['from'][0]}, col {move['from'][1]})")
    print(f"  To: {move['notation'][2:]} (row {move['to'][0]}, col {move['to'][1]})")
    print(f"  Piece: {move['piece']['class']}")
    if move['captured']:
        print(f"  Captured: {move['captured']['class']}")
    print(f"  Notation: {move['notation']}")

    return True


def test_visualization(cv: ChessVision):
    """Test 6: Visualization"""
    print_section("TEST 6: Visualization")

    state = cv.scan_board()
    if state is None:
        print("✗ Failed to scan board")
        return False

    # Create visualization
    vis = cv.visualize_board(state, show_confidence=True)

    # Save visualization
    output_path = Path("test_board_visualization.jpg")
    cv2.imwrite(str(output_path), vis)
    print(f"✓ Visualization saved: {output_path}")

    # Display if not headless
    try:
        cv2.imshow("Board Visualization", vis)
        cv2.waitKey(3000)  # Show for 3 seconds
        cv2.destroyAllWindows()
        print("✓ Visualization displayed")
    except:
        print("⚠ Display not available (headless mode)")

    return True


def run_tests(auto: bool = False):
    """Run all tests."""
    print("=" * 70)
    print("  Pi AI Camera Chess Vision Test Suite")
    print("  Model: YOLOv8n-cls (99.372% accuracy)")
    print("=" * 70)

    results = {}

    # Test 1: Camera
    results['camera'] = test_camera()
    if not results['camera']:
        print("\n✗ TEST FAILED: Camera not working")
        return

    # Test 2: Model
    results['model'] = test_model()
    if not results['model']:
        print("\n✗ TEST FAILED: Model not available")
        return

    # Initialize ChessVision
    print_section("Initializing ChessVision")
    cv = ChessVision(
        camera_index=0,
        model_path="models/chess_classifier_best.onnx",
        conf_thresh=0.80
    )

    # Test 3: Calibration
    results['calibration'] = test_calibration(cv, auto)
    if not results['calibration']:
        print("\n✗ TEST FAILED: Calibration failed")
        return

    # Test 4: Piece Classification
    results['classification'] = test_piece_classification(cv)

    # Test 5: Move Detection (optional, requires user interaction)
    if not auto:
        print("\n" + "=" * 70)
        test_move = input("Test move detection? (y/N): ").lower() == 'y'
        if test_move:
            results['move_detection'] = test_move_detection(cv, auto)
        else:
            results['move_detection'] = None
    else:
        results['move_detection'] = None

    # Test 6: Visualization
    results['visualization'] = test_visualization(cv)

    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)

    for test_name, result in results.items():
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "⊘ SKIP"
        print(f"  {test_name:20s}: {status}")

    print(f"\n  Total: {passed} passed, {failed} failed, {skipped} skipped")

    if failed == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠ {failed} test(s) failed")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Pi AI Camera chess vision")
    parser.add_argument('--auto', action='store_true',
                       help="Run in automatic mode (no user interaction)")
    args = parser.parse_args()

    try:
        run_tests(auto=args.auto)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
