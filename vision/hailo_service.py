"""
Hailo Vision Service for Chess Piece Detection

Uses Raspberry Pi AI Camera with Hailo neural network accelerator
for real-time chess piece detection and move verification.
"""

from typing import Optional, Dict, List, Tuple
import numpy as np
import cv2
from dataclasses import dataclass
from enum import Enum


class PieceType(Enum):
    """Chess piece types."""
    PAWN = "pawn"
    KNIGHT = "knight"
    BISHOP = "bishop"
    ROOK = "rook"
    QUEEN = "queen"
    KING = "king"
    EMPTY = "empty"


class PieceColor(Enum):
    """Piece colors."""
    WHITE = "white"
    BLACK = "black"


@dataclass
class DetectedPiece:
    """Detected chess piece."""
    type: PieceType
    color: Optional[PieceColor]
    square: str  # e.g., "e4"
    confidence: float


@dataclass
class BoardState:
    """Complete board state from vision."""
    pieces: Dict[str, DetectedPiece]
    board_corners: List[Tuple[int, int]]
    confidence: float
    timestamp: float


class HailoVisionService:
    """
    Vision service using Raspberry Pi AI Camera with Hailo accelerator.

    This implementation provides a mock interface for development before
    hardware is available. Replace with actual Hailo SDK calls when ready.
    """

    def __init__(self, model_path: Optional[str] = None, mock_mode: bool = True):
        """
        Initialize Hailo device and load model.

        Args:
            model_path: Path to compiled Hailo model (.hef file)
            mock_mode: If True, use mock implementation for testing
        """
        self.mock_mode = mock_mode
        self.model_path = model_path

        if not mock_mode:
            self._init_hailo_device()
            self._init_camera()
        else:
            print("[VISION] Running in MOCK mode (no hardware)")

    def _init_hailo_device(self):
        """Initialize Hailo NPU device and load model."""
        try:
            # This will be implemented when Hailo SDK is available
            # from hailo_platform import HailoRT, Device
            # self.device = Device()
            # self.model = self.device.create_infer_model(self.model_path)
            raise NotImplementedError("Hailo SDK integration pending")
        except ImportError:
            print("[VISION] Hailo SDK not available, running in mock mode")
            self.mock_mode = True

    def _init_camera(self):
        """Initialize Pi Camera with optimal settings."""
        try:
            # This will be implemented when Pi Camera is available
            # from picamera2 import Picamera2
            # self.camera = Picamera2()
            # config = self.camera.create_still_configuration(
            #     main={"size": (1920, 1080)},
            #     buffer_count=2
            # )
            # self.camera.configure(config)
            # self.camera.start()
            raise NotImplementedError("Pi Camera integration pending")
        except ImportError:
            print("[VISION] Pi Camera library not available, using OpenCV")
            self.camera = cv2.VideoCapture(0)

    def capture_frame(self) -> np.ndarray:
        """
        Capture a single frame from the camera.

        Returns:
            RGB image as numpy array
        """
        if self.mock_mode:
            # Return blank image for testing
            return np.zeros((1080, 1920, 3), dtype=np.uint8)

        if hasattr(self, 'camera') and hasattr(self.camera, 'capture_array'):
            # Pi Camera
            return self.camera.capture_array()
        else:
            # OpenCV camera
            ret, frame = self.camera.read()
            if ret:
                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return np.zeros((1080, 1920, 3), dtype=np.uint8)

    def detect_board(self) -> Dict:
        """
        Detect chessboard corners and orientation.

        Returns:
            dict with:
                - corners: List of 4 corner points (top-left, top-right, bottom-right, bottom-left)
                - transform_matrix: 3x3 perspective transform matrix
                - confidence: Detection confidence score (0-1)
        """
        frame = self.capture_frame()

        if self.mock_mode:
            # Return mock corners for 8x8 board
            height, width = frame.shape[:2]
            margin = 100
            corners = [
                (margin, margin),  # top-left
                (width - margin, margin),  # top-right
                (width - margin, height - margin),  # bottom-right
                (margin, height - margin)  # bottom-left
            ]
            return {
                'corners': corners,
                'transform_matrix': self._get_transform_matrix(corners),
                'confidence': 0.95
            }

        # Real implementation would use Hailo NPU here
        corners = self._detect_corners_opencv(frame)

        return {
            'corners': corners,
            'transform_matrix': self._get_transform_matrix(corners),
            'confidence': self._calculate_confidence(corners)
        }

    def _detect_corners_opencv(self, frame: np.ndarray) -> List[Tuple[int, int]]:
        """
        Detect chessboard corners using OpenCV (fallback method).

        Args:
            frame: Input image

        Returns:
            List of 4 corner points
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

        # Try to find chessboard corners
        ret, corners = cv2.findChessboardCorners(gray, (7, 7), None)

        if ret:
            # Extract outer corners
            corners = corners.reshape(-1, 2)
            top_left = corners[0]
            top_right = corners[6]
            bottom_right = corners[-1]
            bottom_left = corners[-7]

            return [
                tuple(top_left.astype(int)),
                tuple(top_right.astype(int)),
                tuple(bottom_right.astype(int)),
                tuple(bottom_left.astype(int))
            ]

        # If chessboard not found, return default corners
        height, width = frame.shape[:2]
        margin = 100
        return [
            (margin, margin),
            (width - margin, margin),
            (width - margin, height - margin),
            (margin, height - margin)
        ]

    def _get_transform_matrix(self, corners: List[Tuple[int, int]]) -> np.ndarray:
        """
        Calculate perspective transform matrix from corners.

        Args:
            corners: List of 4 corner points

        Returns:
            3x3 perspective transform matrix
        """
        # Source points (detected corners)
        src_pts = np.float32(corners)

        # Destination points (perfect square, 640x640)
        dst_pts = np.float32([
            [0, 0],
            [640, 0],
            [640, 640],
            [0, 640]
        ])

        return cv2.getPerspectiveTransform(src_pts, dst_pts)

    def _calculate_confidence(self, corners: List[Tuple[int, int]]) -> float:
        """
        Calculate confidence score based on corner detection quality.

        Args:
            corners: Detected corner points

        Returns:
            Confidence score (0-1)
        """
        # Simple heuristic: check if corners form a reasonable quadrilateral
        if len(corners) != 4:
            return 0.0

        # Calculate area
        pts = np.array(corners)
        area = cv2.contourArea(pts)

        # Check if area is reasonable (not too small, not too large)
        if area < 10000 or area > 1000000:
            return 0.5

        return 0.95

    def capture_board_state(self) -> BoardState:
        """
        Capture complete board state including all pieces.

        Returns:
            BoardState object with all detected pieces
        """
        import time

        # Detect board
        board_info = self.detect_board()

        # Capture and warp frame
        frame = self.capture_frame()
        warped = cv2.warpPerspective(
            frame,
            board_info['transform_matrix'],
            (640, 640)
        )

        # Detect all pieces
        pieces = self.detect_all_pieces(warped)

        return BoardState(
            pieces=pieces,
            board_corners=board_info['corners'],
            confidence=board_info['confidence'],
            timestamp=time.time()
        )

    def detect_all_pieces(self, board_image: np.ndarray) -> Dict[str, DetectedPiece]:
        """
        Detect all pieces on the warped board image.

        Args:
            board_image: Warped 640x640 board image

        Returns:
            Dictionary mapping square names to DetectedPiece objects
        """
        pieces = {}
        square_size = 80  # 640 / 8

        for rank in range(8):
            for file in range(8):
                # Extract square image
                x = file * square_size
                y = rank * square_size
                square_img = board_image[y:y+square_size, x:x+square_size]

                # Classify piece
                piece = self._classify_piece(square_img)

                if piece.type != PieceType.EMPTY:
                    square_name = chr(ord('a') + file) + str(8 - rank)
                    pieces[square_name] = piece

        return pieces

    def _classify_piece(self, square_image: np.ndarray) -> DetectedPiece:
        """
        Classify piece in a single square.

        Args:
            square_image: Image of a single chess square

        Returns:
            DetectedPiece object
        """
        if self.mock_mode:
            # Mock classification - return empty square
            return DetectedPiece(
                type=PieceType.EMPTY,
                color=None,
                square="",
                confidence=1.0
            )

        # Real implementation would use Hailo NPU here
        # For now, use simple heuristics or placeholder

        # Calculate average brightness
        gray = cv2.cvtColor(square_image, cv2.COLOR_RGB2GRAY)
        avg_brightness = np.mean(gray)

        # Simple heuristic: if too bright or too dark, probably empty
        if avg_brightness > 180 or avg_brightness < 75:
            return DetectedPiece(
                type=PieceType.EMPTY,
                color=None,
                square="",
                confidence=0.9
            )

        # Placeholder: detect as white pawn with low confidence
        return DetectedPiece(
            type=PieceType.PAWN,
            color=PieceColor.WHITE,
            square="",
            confidence=0.5
        )

    def verify_move(self, expected_move: str, timeout: float = 5.0) -> Tuple[bool, str]:
        """
        Verify that a physical move matches expected move.

        Args:
            expected_move: UCI format move (e.g., "e2e4")
            timeout: Maximum time to wait for move detection (seconds)

        Returns:
            Tuple of (success: bool, message: str)
        """
        import time

        # Parse expected move
        from_square = expected_move[:2]
        to_square = expected_move[2:4]

        # Capture state before move
        before = self.capture_board_state()

        # Wait for piece to be moved
        time.sleep(timeout / 2)

        # Capture state after move
        after = self.capture_board_state()

        # Check from square is now empty
        if from_square in after.pieces:
            return (False, f"Piece still detected on {from_square}")

        # Check to square has a piece
        if to_square not in after.pieces:
            return (False, f"No piece detected on {to_square}")

        # Check piece type matches (if we had it before)
        if from_square in before.pieces:
            before_piece = before.pieces[from_square]
            after_piece = after.pieces[to_square]

            if before_piece.type != after_piece.type:
                return (False, f"Piece type mismatch: expected {before_piece.type}, got {after_piece.type}")

        return (True, "Move verified successfully")

    def get_position_differences(self, expected_state: Dict[str, str]) -> List[str]:
        """
        Compare current physical position with expected logical position.

        Args:
            expected_state: Dictionary mapping squares to piece names
                          (e.g., {"e4": "white_pawn", "d5": "black_pawn"})

        Returns:
            List of error messages describing differences
        """
        current = self.capture_board_state()
        differences = []

        # Check each square
        all_squares = set(expected_state.keys()) | set(current.pieces.keys())

        for square in all_squares:
            expected = expected_state.get(square)
            detected = current.pieces.get(square)

            if expected and not detected:
                differences.append(f"{square}: Expected {expected}, detected empty")
            elif not expected and detected:
                differences.append(f"{square}: Expected empty, detected {detected.color.value}_{detected.type.value}")
            elif expected and detected:
                detected_name = f"{detected.color.value}_{detected.type.value}"
                if expected != detected_name:
                    differences.append(f"{square}: Expected {expected}, detected {detected_name}")

        return differences

    def calibrate(self) -> bool:
        """
        Run calibration routine to optimize detection.

        Returns:
            True if calibration successful
        """
        print("[VISION] Starting calibration...")

        # Detect board
        board_info = self.detect_board()

        if board_info['confidence'] < 0.8:
            print(f"[VISION] ✗ Board detection confidence too low: {board_info['confidence']:.2f}")
            return False

        print(f"[VISION] ✓ Board detected with confidence: {board_info['confidence']:.2f}")

        # Test piece detection on all 64 squares
        frame = self.capture_frame()
        warped = cv2.warpPerspective(
            frame,
            board_info['transform_matrix'],
            (640, 640)
        )

        pieces = self.detect_all_pieces(warped)
        print(f"[VISION] ✓ Detected {len(pieces)} pieces on board")

        print("[VISION] ✓ Calibration complete")
        return True

    def close(self):
        """Release camera and cleanup resources."""
        if hasattr(self, 'camera'):
            if hasattr(self.camera, 'close'):
                self.camera.close()
            elif hasattr(self.camera, 'release'):
                self.camera.release()

        if not self.mock_mode and hasattr(self, 'device'):
            # Cleanup Hailo device
            pass
