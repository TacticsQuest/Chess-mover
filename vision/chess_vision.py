"""
Complete Chess Vision System for Pi AI Camera

Integrates:
1. Board detection (ArUco markers)
2. Board warping and square extraction
3. Piece classification (99.372% accuracy model)
4. Move detection and validation
5. Board state tracking (FEN notation)

Usage:
    from vision.chess_vision import ChessVision

    cv = ChessVision(camera_index=0)
    cv.calibrate()  # One-time calibration with ArUco markers
    board_state = cv.scan_board()  # Get current board state
    print(f"FEN: {board_state['fen']}")
"""

import cv2
import numpy as np
from typing import Optional, Dict, List, Tuple
from pathlib import Path

from .board_finder import BoardFinder, BoardGeometry
from .piece_classifier import PieceClassifier, PieceType, PieceColor
from .move_verifier import MoveVerifier


class ChessVision:
    """
    Complete chess vision system using Pi AI Camera.

    Features:
    - Automatic board detection with ArUco markers
    - 99.372% accurate piece classification
    - Real-time board scanning
    - Move detection and validation
    - FEN notation export
    """

    def __init__(self,
                 camera_index: int = 0,
                 model_path: str = "models/chess_classifier_best.onnx",
                 geom_path: str = "config/board_geometry.yml",
                 warp_size: int = 800,
                 conf_thresh: float = 0.80):
        """
        Initialize chess vision system.

        Args:
            camera_index: Camera device index (0 for Pi AI Camera)
            model_path: Path to ONNX piece classification model
            geom_path: Path to save/load board geometry
            warp_size: Size of warped board image (default 800x800)
            conf_thresh: Confidence threshold for piece classification
        """
        self.camera_index = camera_index
        self.geom_path = Path(geom_path)
        self.geom: Optional[BoardGeometry] = None

        # Initialize components
        self.board_finder = BoardFinder(warp_size=warp_size)
        self.piece_classifier = PieceClassifier(
            onnx_path=model_path,
            conf_thresh=conf_thresh
        )
        self.move_verifier = MoveVerifier()

        # Board state tracking
        self.current_state: Optional[Dict] = None
        self.previous_state: Optional[Dict] = None

        # Create config directory if needed
        self.geom_path.parent.mkdir(parents=True, exist_ok=True)

        # Try to load existing geometry
        if self.geom_path.exists():
            self._load_geometry()

        print(f"[ChessVision] Initialized")
        print(f"  Camera: {camera_index}")
        print(f"  Model: {model_path}")
        print(f"  Geometry: {geom_path} {'(loaded)' if self.geom else '(not found)'}")

    def calibrate(self,
                  manual_points: Optional[List[Tuple[float, float]]] = None,
                  save: bool = True) -> bool:
        """
        Calibrate board geometry using ArUco markers or manual points.

        Args:
            manual_points: Optional list of 4 corner points [(x,y), ...]
                          Order: top-left, top-right, bottom-right, bottom-left
            save: Save geometry to file after calibration

        Returns:
            True if calibration successful, False otherwise

        Example:
            # Automatic calibration with ArUco markers
            cv.calibrate()

            # Manual calibration with corner points
            cv.calibrate(manual_points=[(100, 50), (700, 50), (700, 650), (100, 650)])
        """
        # Capture frame from camera
        frame = self._capture_frame()
        if frame is None:
            print("[ERROR] Failed to capture frame for calibration")
            return False

        if manual_points:
            # Manual calibration
            src = np.float32(manual_points)
            dst = np.float32([
                [0, 0],
                [self.board_finder.warp_w, 0],
                [self.board_finder.warp_w, self.board_finder.warp_h],
                [0, self.board_finder.warp_h]
            ])
            H = cv2.getPerspectiveTransform(src, dst)
            self.geom = BoardGeometry(H=H, size=(self.board_finder.warp_w, self.board_finder.warp_h))
            print(f"[ChessVision] Manual calibration complete")
        else:
            # Automatic calibration with ArUco markers
            geom = self.board_finder.detect_homography_aruco(frame)
            if geom is None:
                print("[ERROR] ArUco markers not found")
                print("[INFO] Make sure all 4 markers (IDs 0, 1, 2, 3) are visible")
                return False

            self.geom = geom
            print(f"[ChessVision] ArUco calibration complete")

        # Save geometry
        if save and self.geom:
            self._save_geometry()

        return True

    def scan_board(self, update_state: bool = True) -> Optional[Dict]:
        """
        Scan current board state and classify all pieces.

        Args:
            update_state: Update internal state tracking (default True)

        Returns:
            Board state dictionary with:
            {
                "predictions": [[{class, type, color}, ...], ...],  # 8x8 grid
                "confidences": [[float, ...], ...],  # 8x8 grid
                "fen": str,  # FEN notation (piece placement)
                "frame": np.ndarray,  # Original camera frame
                "warped": np.ndarray  # Warped board image
            }

        Example:
            state = cv.scan_board()
            print(f"Position: {state['fen']}")
            print(f"e4: {state['predictions'][4][4]['class']}")
        """
        if self.geom is None:
            print("[ERROR] Board not calibrated. Run calibrate() first.")
            return None

        # Capture frame
        frame = self._capture_frame()
        if frame is None:
            print("[ERROR] Failed to capture frame")
            return None

        # Warp perspective to get top-down view
        warped = self.board_finder.warp(frame, self.geom)

        # Split into 64 squares
        tiles = self.board_finder.split_into_64(warped)

        # Classify each square
        predictions, confidences = self.piece_classifier.predict_batch(tiles)

        # Generate FEN notation
        fen = self.piece_classifier.get_board_state_fen(predictions)

        # Create state dictionary
        state = {
            "predictions": predictions,
            "confidences": confidences,
            "fen": fen,
            "frame": frame,
            "warped": warped,
            "tiles": tiles
        }

        # Update state tracking
        if update_state:
            self.previous_state = self.current_state
            self.current_state = state

        return state

    def detect_move(self) -> Optional[Dict]:
        """
        Detect move between previous and current board state.

        Returns:
            Move dictionary with:
            {
                "from": (row, col),
                "to": (row, col),
                "piece": {class, type, color},
                "captured": {class, type, color} or None,
                "notation": str  # e.g., "e2e4"
            }

        Example:
            cv.scan_board()  # Scan before move
            # ... player makes move ...
            cv.scan_board()  # Scan after move
            move = cv.detect_move()
            print(f"Move: {move['notation']}")
        """
        if self.previous_state is None or self.current_state is None:
            print("[ERROR] Need at least 2 scans to detect move")
            return None

        # Extract label grids for move verifier
        prev_labels = self._predictions_to_labels(self.previous_state["predictions"])
        curr_labels = self._predictions_to_labels(self.current_state["predictions"])

        # Detect move using move verifier
        move_rc = self.move_verifier.derive_move(prev_labels, curr_labels)

        if move_rc is None:
            print("[WARN] No move detected or ambiguous changes")
            return None

        from_rc, to_rc = move_rc

        # Get piece information
        piece_moved = self.previous_state["predictions"][from_rc[0]][from_rc[1]]
        piece_captured = self.previous_state["predictions"][to_rc[0]][to_rc[1]]

        # Convert to chess notation (a1-h8)
        notation = self._rc_to_notation(from_rc) + self._rc_to_notation(to_rc)

        return {
            "from": from_rc,
            "to": to_rc,
            "piece": piece_moved,
            "captured": piece_captured if piece_captured["color"] != PieceColor.EMPTY else None,
            "notation": notation
        }

    def visualize_board(self, state: Optional[Dict] = None, show_confidence: bool = False) -> np.ndarray:
        """
        Create visualization of board state with piece labels.

        Args:
            state: Board state (uses current_state if None)
            show_confidence: Show confidence scores on squares

        Returns:
            Annotated image

        Example:
            state = cv.scan_board()
            vis = cv.visualize_board(state, show_confidence=True)
            cv2.imshow("Board", vis)
        """
        if state is None:
            state = self.current_state

        if state is None:
            print("[ERROR] No board state to visualize")
            return np.zeros((800, 800, 3), dtype=np.uint8)

        # Start with warped board image
        vis = state["warped"].copy()
        h, w = vis.shape[:2]
        tile_h, tile_w = h // 8, w // 8

        # Overlay predictions
        for r in range(8):
            for c in range(8):
                pred = state["predictions"][r][c]
                conf = state["confidences"][r][c]

                # Skip empty squares
                if pred["color"] == PieceColor.EMPTY:
                    continue

                # Determine text position (center of square)
                x = c * tile_w + tile_w // 2
                y = r * tile_h + tile_h // 2

                # Create label text
                class_name = pred["class"]
                if show_confidence:
                    label = f"{class_name}\n{conf:.0%}"
                else:
                    label = class_name

                # Draw background rectangle for text
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.4
                thickness = 1

                for i, line in enumerate(label.split('\n')):
                    (text_w, text_h), _ = cv2.getTextSize(line, font, font_scale, thickness)
                    text_x = x - text_w // 2
                    text_y = y - text_h // 2 + i * 20

                    # Background rectangle
                    cv2.rectangle(vis,
                                (text_x - 2, text_y - text_h - 2),
                                (text_x + text_w + 2, text_y + 4),
                                (255, 255, 255), -1)

                    # Text
                    cv2.putText(vis, line, (text_x, text_y),
                              font, font_scale, (0, 0, 0), thickness)

        return vis

    def _capture_frame(self) -> Optional[np.ndarray]:
        """Capture single frame from camera."""
        cap = cv2.VideoCapture(self.camera_index)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return None
        return frame

    def _save_geometry(self):
        """Save board geometry to file."""
        if self.geom is None:
            return
        self.board_finder.save_geom(str(self.geom_path), self.geom)
        print(f"[ChessVision] Geometry saved to {self.geom_path}")

    def _load_geometry(self):
        """Load board geometry from file."""
        try:
            self.geom = self.board_finder.load_geom(str(self.geom_path))
            print(f"[ChessVision] Geometry loaded from {self.geom_path}")
        except Exception as e:
            print(f"[WARN] Failed to load geometry: {e}")
            self.geom = None

    def _predictions_to_labels(self, predictions: List[List[Dict]]) -> List[List[int]]:
        """Convert predictions to simple label grid for move verifier."""
        from .square_classifier import Label

        labels = [[Label.EMPTY] * 8 for _ in range(8)]
        for r in range(8):
            for c in range(8):
                color = predictions[r][c]["color"]
                if color == PieceColor.WHITE:
                    labels[r][c] = Label.WHITE
                elif color == PieceColor.BLACK:
                    labels[r][c] = Label.BLACK
                else:
                    labels[r][c] = Label.EMPTY

        return labels

    def _rc_to_notation(self, rc: Tuple[int, int]) -> str:
        """Convert (row, col) to chess notation (e.g., (4, 4) -> 'e4')."""
        r, c = rc
        file = chr(ord('a') + c)
        rank = str(8 - r)
        return f"{file}{rank}"
