"""
Chess Piece Classifier using trained YOLOv8n-cls model (99.372% accuracy)

This classifier identifies chess pieces on individual squares using the
custom-trained model from your physical chess set.

Classes:
- black_bishop, black_king, black_knight, black_pawn, black_queen, black_rook
- white_bishop, white_king, white_knight, white_pawn, white_queen, white_rook
- empty (no piece)

Model: YOLOv8n-cls trained on 1,503 images with 13 piece classes
Accuracy: 99.372% on validation set (162 images)
"""

import numpy as np
import cv2
from enum import IntEnum
from typing import Tuple, List
import os

try:
    import onnxruntime as ort
except ImportError:
    ort = None


class PieceType(IntEnum):
    """Chess piece types"""
    EMPTY = 0
    PAWN = 1
    KNIGHT = 2
    BISHOP = 3
    ROOK = 4
    QUEEN = 5
    KING = 6


class PieceColor(IntEnum):
    """Chess piece colors"""
    EMPTY = 0
    WHITE = 1
    BLACK = 2


class PieceClassifier:
    """
    Chess piece classifier using ONNX model.

    Features:
    - 99.372% accuracy on validation set
    - 13 classes (12 piece types + empty)
    - Fast inference (YOLOv8n-cls)
    - Works on Pi AI Camera (ARM64)
    """

    # Class names from training (alphabetically sorted by YOLOv8)
    CLASS_NAMES = [
        'black_bishop', 'black_king', 'black_knight', 'black_pawn',
        'black_queen', 'black_rook', 'white_bishop', 'white_king',
        'white_knight', 'white_pawn', 'white_queen', 'white_rook', 'empty'
    ]

    def __init__(self, onnx_path: str = "models/chess_classifier_best.onnx",
                 conf_thresh: float = 0.80):
        """
        Initialize piece classifier.

        Args:
            onnx_path: Path to ONNX model file
            conf_thresh: Confidence threshold for classification (0-1)
                        Default 0.80 for high accuracy (model achieves 99.372%)
        """
        self.onnx_path = onnx_path
        self.conf_thresh = conf_thresh
        self.sess = None
        self.input_name = None
        self.output_name = None
        self.input_shape = (224, 224)  # YOLOv8n-cls default

        # Load model if available
        if os.path.exists(onnx_path):
            self._load_model()
        else:
            print(f"[WARN] Model not found at {onnx_path}")
            print(f"[WARN] Using heuristic fallback (empty/white/black only)")

    def _load_model(self):
        """Load ONNX model for inference."""
        if not ort:
            print("[WARN] onnxruntime not installed. Install with: pip install onnxruntime")
            return

        try:
            # Use CPUExecutionProvider for Pi AI Camera compatibility
            self.sess = ort.InferenceSession(
                self.onnx_path,
                providers=['CPUExecutionProvider']
            )
            self.input_name = self.sess.get_inputs()[0].name
            self.output_name = self.sess.get_outputs()[0].name
            print(f"[INFO] Loaded model: {self.onnx_path}")
            print(f"[INFO] Input: {self.input_name}, Output: {self.output_name}")
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            self.sess = None

    def preprocess(self, img_bgr: np.ndarray) -> np.ndarray:
        """
        Preprocess image for model inference.

        Args:
            img_bgr: BGR image from OpenCV (any size)

        Returns:
            Preprocessed image tensor (1, 3, 224, 224)
        """
        # Resize to model input size
        img_resized = cv2.resize(img_bgr, self.input_shape, interpolation=cv2.INTER_LINEAR)

        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)

        # Normalize to [0, 1]
        img_norm = img_rgb.astype(np.float32) / 255.0

        # Transpose to (C, H, W) and add batch dimension
        img_chw = np.transpose(img_norm, (2, 0, 1))  # (H, W, C) -> (C, H, W)
        img_batch = np.expand_dims(img_chw, axis=0)  # (1, C, H, W)

        return img_batch

    def predict_single(self, img_bgr: np.ndarray) -> Tuple[str, float, PieceType, PieceColor]:
        """
        Classify a single chess piece image.

        Args:
            img_bgr: BGR image of a chess square

        Returns:
            (class_name, confidence, piece_type, piece_color)

        Example:
            class_name, conf, ptype, pcolor = clf.predict_single(square_img)
            print(f"Detected: {class_name} ({conf:.1%})")
        """
        if self.sess is None:
            # Fallback to heuristic (empty/white/black only)
            return self._heuristic_fallback(img_bgr)

        # Preprocess image
        input_tensor = self.preprocess(img_bgr)

        # Run inference
        outputs = self.sess.run([self.output_name], {self.input_name: input_tensor})
        probs = outputs[0][0]  # Shape: (num_classes,)

        # Get top prediction
        class_idx = np.argmax(probs)
        confidence = float(probs[class_idx])
        class_name = self.CLASS_NAMES[class_idx]

        # Parse piece type and color
        piece_type, piece_color = self._parse_class_name(class_name)

        # Check confidence threshold
        if confidence < self.conf_thresh:
            # Low confidence - treat as empty or fallback to heuristic
            print(f"[WARN] Low confidence: {class_name} ({confidence:.2%}) < {self.conf_thresh:.0%}")
            return self._heuristic_fallback(img_bgr)

        return class_name, confidence, piece_type, piece_color

    def predict_batch(self, tiles_bgr: List[List[np.ndarray]]) -> Tuple[List[List[dict]], List[List[float]]]:
        """
        Classify all 64 squares on the chess board.

        Args:
            tiles_bgr: 8x8 list of BGR images (one per square)

        Returns:
            (predictions, confidences)
            - predictions[r][c] = {"class": str, "type": PieceType, "color": PieceColor}
            - confidences[r][c] = confidence score (0-1)

        Example:
            preds, confs = clf.predict_batch(tiles)
            print(f"e4: {preds[4][4]['class']} ({confs[4][4]:.1%})")
        """
        predictions = [[None] * 8 for _ in range(8)]
        confidences = [[0.0] * 8 for _ in range(8)]

        for r in range(8):
            for c in range(8):
                class_name, conf, ptype, pcolor = self.predict_single(tiles_bgr[r][c])

                predictions[r][c] = {
                    "class": class_name,
                    "type": ptype,
                    "color": pcolor
                }
                confidences[r][c] = float(conf)

        return predictions, confidences

    def _parse_class_name(self, class_name: str) -> Tuple[PieceType, PieceColor]:
        """
        Parse class name to piece type and color.

        Args:
            class_name: e.g., "white_pawn", "black_king", "empty"

        Returns:
            (piece_type, piece_color)
        """
        if class_name == "empty":
            return PieceType.EMPTY, PieceColor.EMPTY

        # Split "white_pawn" -> ["white", "pawn"]
        parts = class_name.split("_", 1)
        if len(parts) != 2:
            return PieceType.EMPTY, PieceColor.EMPTY

        color_str, piece_str = parts

        # Parse color
        if color_str == "white":
            piece_color = PieceColor.WHITE
        elif color_str == "black":
            piece_color = PieceColor.BLACK
        else:
            piece_color = PieceColor.EMPTY

        # Parse piece type
        piece_type_map = {
            "pawn": PieceType.PAWN,
            "knight": PieceType.KNIGHT,
            "bishop": PieceType.BISHOP,
            "rook": PieceType.ROOK,
            "queen": PieceType.QUEEN,
            "king": PieceType.KING,
        }
        piece_type = piece_type_map.get(piece_str, PieceType.EMPTY)

        return piece_type, piece_color

    def _heuristic_fallback(self, img_bgr: np.ndarray) -> Tuple[str, float, PieceType, PieceColor]:
        """
        Fallback heuristic for empty/white/black detection.
        Used when model is not available or confidence is too low.

        Args:
            img_bgr: BGR image of a chess square

        Returns:
            (class_name, confidence, piece_type, piece_color)
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
        L, A, B = cv2.split(lab)

        # Detect edges to determine if square is occupied
        edges = cv2.Canny(L, 40, 120)
        occupied_score = (edges.mean() / 255.0) * 0.6 + (np.var(L) / (255.0 * 255.0)) * 0.4

        # Empty square detection
        if occupied_score < 0.02:
            return "empty", 0.95, PieceType.EMPTY, PieceColor.EMPTY

        # Extract center region (where piece is likely to be)
        h, w = img_bgr.shape[:2]
        center = img_bgr[h//4: 3*h//4, w//4: 3*w//4]

        # Determine color based on brightness (V channel in HSV)
        hsv_center = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)
        v = hsv_center[..., 2].mean()

        if v > 115:
            # Bright piece -> White
            conf = min(0.95, 0.5 + (v - 115) / 140)
            # Heuristic can't determine piece type, so return generic white
            return "white_unknown", conf, PieceType.PAWN, PieceColor.WHITE
        else:
            # Dark piece -> Black
            conf = min(0.95, 0.5 + (115 - v) / 115)
            # Heuristic can't determine piece type, so return generic black
            return "black_unknown", conf, PieceType.PAWN, PieceColor.BLACK

    def get_board_state_fen(self, predictions: List[List[dict]]) -> str:
        """
        Convert board predictions to FEN notation (piece placement only).

        Args:
            predictions: 8x8 predictions from predict_batch()

        Returns:
            FEN string (piece placement part only)

        Example:
            preds, _ = clf.predict_batch(tiles)
            fen = clf.get_board_state_fen(preds)
            print(f"Position: {fen}")
        """
        piece_chars = {
            (PieceColor.WHITE, PieceType.PAWN): 'P',
            (PieceColor.WHITE, PieceType.KNIGHT): 'N',
            (PieceColor.WHITE, PieceType.BISHOP): 'B',
            (PieceColor.WHITE, PieceType.ROOK): 'R',
            (PieceColor.WHITE, PieceType.QUEEN): 'Q',
            (PieceColor.WHITE, PieceType.KING): 'K',
            (PieceColor.BLACK, PieceType.PAWN): 'p',
            (PieceColor.BLACK, PieceType.KNIGHT): 'n',
            (PieceColor.BLACK, PieceType.BISHOP): 'b',
            (PieceColor.BLACK, PieceType.ROOK): 'r',
            (PieceColor.BLACK, PieceType.QUEEN): 'q',
            (PieceColor.BLACK, PieceType.KING): 'k',
        }

        fen_rows = []
        for r in range(8):
            fen_row = ""
            empty_count = 0

            for c in range(8):
                pred = predictions[r][c]
                pcolor = pred["color"]
                ptype = pred["type"]

                if pcolor == PieceColor.EMPTY or ptype == PieceType.EMPTY:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        fen_row += str(empty_count)
                        empty_count = 0

                    piece_char = piece_chars.get((pcolor, ptype), '?')
                    fen_row += piece_char

            if empty_count > 0:
                fen_row += str(empty_count)

            fen_rows.append(fen_row)

        return "/".join(fen_rows)
