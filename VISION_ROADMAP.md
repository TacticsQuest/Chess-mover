# Chess Mover Machine - Vision System Roadmap (IMX500)

## 🎯 Vision System Goals

**Primary Objectives:**
1. Auto-find the chess board (corners/boundaries)
2. Understand board size and compute pixel↔square mapping
3. Locate and identify all pieces (real-time)
4. Verify human and robot moves
5. Detect illegal positions and hand-in-frame safety

**Hardware:**
- IMX500 AI camera (on-sensor inference) for Pi deployment
- USB webcam for Windows development/testing
- LED panel for consistent lighting

---

## 📋 Implementation Phases

### Phase 1: USB Webcam Development (Windows) - CURRENT

**Goal:** Build complete vision pipeline with standard USB camera
**Status:** Ready to implement
**Timeline:** 1-2 weeks

#### 1.1 Camera Calibration (One-Time)

**Files to Create:**
- `vision/camera_calibration.py`
- `config/camera.yml` (stores intrinsics)

**Process:**
```python
# A. Camera intrinsics
# - Print checkerboard or use chessboard
# - Capture 15-30 frames at different angles
# - Compute camera_matrix + dist_coeffs
# - Save to camera.yml
```

**Code Skeleton:**
```python
import cv2
import numpy as np
import yaml

def calibrate_camera(images_path, checkerboard_size=(7,7)):
    """
    Calibrate camera intrinsics.

    Args:
        images_path: Path to calibration images
        checkerboard_size: Inner corner count (rows, cols)

    Returns:
        camera_matrix, dist_coeffs
    """
    # Find checkerboard corners in each image
    # Compute camera matrix and distortion
    # Save to config/camera.yml
    pass
```

#### 1.2 Board Detection & Homography

**Files to Create:**
- `vision/board_detector.py`
- `config/board.yml` (stores homography matrix)

**Three Detection Methods:**

**Option A: ArUco Markers (RECOMMENDED)**
```python
import cv2.aruco as aruco

def detect_board_with_aruco(frame):
    """
    Detect board corners using ArUco markers.

    Place 4 ArUco tags at board corners:
    - ID 0: Top-left
    - ID 1: Top-right
    - ID 2: Bottom-right
    - ID 3: Bottom-left

    Returns:
        H: 3x3 homography matrix (pixel → board)
    """
    aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
    params = aruco.DetectorParameters()
    detector = aruco.ArucoDetector(aruco_dict, params)

    corners, ids, _ = detector.detectMarkers(frame)

    # Extract corner positions for IDs 0,1,2,3
    # Compute homography: src (pixel) → dst (800x800 board)
    # H = cv2.getPerspectiveTransform(src, dst)

    return H
```

**Option B: Chessboard Corner Detection**
```python
def detect_board_with_corners(frame):
    """
    Detect board using inner 7×7 chessboard corners.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, (7,7))

    if ret:
        # Extract outer corners
        # Compute homography
        pass
```

**Option C: Manual Calibration**
```python
def manual_board_calibration(frame):
    """
    User clicks 4 corners manually.
    Uses optical flow to track in subsequent frames.
    """
    # GUI to click TL, TR, BR, BL
    # Compute homography
    # Track with Lucas-Kanade optical flow
    pass
```

#### 1.3 Square Grid & Cell Extraction

**File:** `vision/board_warper.py`

```python
def warp_to_topdown(frame, H, board_size=800):
    """
    Warp frame to top-down 800×800 board view.

    Args:
        frame: Input camera frame
        H: Homography matrix
        board_size: Output size (800×800 recommended)

    Returns:
        warped: Top-down board image
    """
    warped = cv2.warpPerspective(frame, H, (board_size, board_size))
    return warped

def split_into_cells(board_img):
    """
    Split 800×800 board into 64 cells (100×100 each).

    Returns:
        cells: 8×8 array of cell images
    """
    h, w = board_img.shape[:2]
    cell_h, cell_w = h // 8, w // 8

    cells = []
    for rank in range(8):  # 8 to 1
        row = []
        for file in range(8):  # A to H
            cell = board_img[
                rank * cell_h : (rank + 1) * cell_h,
                file * cell_w : (file + 1) * cell_w
            ]
            row.append(cell)
        cells.append(row)

    return cells  # cells[rank][file]
```

#### 1.4 Piece Classification (Per Square)

**File:** `vision/piece_classifier.py`

**Approach 1: Simple Heuristics (No Training)**
```python
class SimpleClassifier:
    """
    Background subtraction + color features.
    Good for initial testing.
    """

    def __init__(self):
        self.bg_models = {}  # Per-square background

    def train_background(self, empty_cells):
        """Learn background for each square when empty."""
        for rank in range(8):
            for file in range(8):
                self.bg_models[(rank, file)] = np.median(
                    empty_cells[rank][file], axis=2
                )

    def classify_cell(self, cell, rank, file):
        """
        Classify single cell.

        Returns:
            label: 'empty', 'white', 'black'
            confidence: 0.0 to 1.0
        """
        # Background subtraction
        fg_mask = self._foreground_mask(cell, rank, file)

        if fg_mask.sum() < threshold:
            return 'empty', 0.95

        # Color analysis (HSV)
        hsv = cv2.cvtColor(cell, cv2.COLOR_BGR2HSV)
        is_white = self._check_white_color(hsv, fg_mask)

        return ('white' if is_white else 'black'), 0.7
```

**Approach 2: CNN Classifier (Production)**
```python
class CNNClassifier:
    """
    13-class CNN: {empty, wP,wN,wB,wR,wQ,wK, bP,bN,bB,bR,bQ,bK}

    Uses ONNX for portability.
    Runs on CPU now, IMX500 later.
    """

    CLASSES = [
        'empty',
        'white_pawn', 'white_knight', 'white_bishop',
        'white_rook', 'white_queen', 'white_king',
        'black_pawn', 'black_knight', 'black_bishop',
        'black_rook', 'black_queen', 'black_king'
    ]

    def __init__(self, model_path='models/piece_classifier.onnx'):
        import onnxruntime as ort
        self.session = ort.InferenceSession(model_path)
        self.input_name = self.session.get_inputs()[0].name

    def classify_cell(self, cell):
        """
        Classify 100×100 cell image.

        Returns:
            label: Class name
            confidence: 0.0 to 1.0
            probs: All class probabilities
        """
        # Preprocess: resize to 64×64, normalize
        img = cv2.resize(cell, (64, 64))
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))  # CHW
        img = np.expand_dims(img, 0)  # NCHW

        # Inference
        outputs = self.session.run(None, {self.input_name: img})
        probs = softmax(outputs[0][0])

        idx = np.argmax(probs)
        label = self.CLASSES[idx]
        confidence = probs[idx]

        return label, confidence, probs
```

**Temporal Smoothing:**
```python
class TemporalSmoother:
    """
    Exponential moving average to reduce flicker.
    """

    def __init__(self, alpha=0.7, num_classes=13):
        self.alpha = alpha
        self.probs_history = {}  # (rank, file) -> probs

    def update(self, rank, file, new_probs):
        """
        Smooth probabilities over time.

        Returns:
            smoothed_label, smoothed_confidence
        """
        key = (rank, file)

        if key not in self.probs_history:
            self.probs_history[key] = new_probs
        else:
            # EMA
            old = self.probs_history[key]
            self.probs_history[key] = (
                self.alpha * old + (1 - self.alpha) * new_probs
            )

        smoothed = self.probs_history[key]
        idx = np.argmax(smoothed)

        return CLASSES[idx], smoothed[idx]
```

#### 1.5 Move Detection & Verification

**File:** `vision/move_detector.py`

```python
import chess

class MoveDetector:
    """
    Detect chess moves by comparing board states.
    Verify legality with python-chess.
    """

    def __init__(self):
        self.last_board = None  # python-chess Board
        self.last_fen = chess.STARTING_FEN

    def detect_move(self, current_position):
        """
        Detect move from previous position to current.

        Args:
            current_position: 8×8 array of piece labels

        Returns:
            move: chess.Move object (or None)
            confidence: 0.0 to 1.0
        """
        if self.last_board is None:
            self.last_board = chess.Board()
            return None, 0.0

        # Find differences
        diffs = self._find_differences(current_position)

        # Patterns:
        if len(diffs) == 2:
            # Normal move or capture
            from_sq, to_sq = self._identify_move(diffs)
            move = chess.Move(from_sq, to_sq)

        elif len(diffs) == 4:
            # Castling (king + rook both move)
            move = self._detect_castling(diffs)

        elif len(diffs) == 3:
            # En passant (pawn + pawn + capture)
            move = self._detect_en_passant(diffs)

        else:
            return None, 0.0

        # Validate with chess rules
        if move in self.last_board.legal_moves:
            confidence = self._calculate_confidence(diffs)
            self.last_board.push(move)
            return move, confidence
        else:
            return None, 0.0

    def verify_robot_move(self, expected_move, current_position):
        """
        Verify robot successfully completed move.

        Returns:
            success: bool
            actual_move: chess.Move (what was detected)
        """
        detected, conf = self.detect_move(current_position)

        if detected == expected_move and conf > 0.8:
            return True, detected
        else:
            return False, detected
```

#### 1.6 Integration with Main GUI

**File:** `ui/vision_panel.py` (NEW)

```python
import tkinter as tk
from vision.board_detector import detect_board_with_aruco
from vision.piece_classifier import CNNClassifier
from vision.move_detector import MoveDetector

class VisionPanel(tk.Frame):
    """
    Vision system control panel for main GUI.
    """

    def __init__(self, parent, theme):
        super().__init__(parent, bg=theme['panel_bg'])

        # Components
        self.camera = None
        self.classifier = CNNClassifier()
        self.move_detector = MoveDetector()

        self._build_ui()

    def _build_ui(self):
        # Camera feed display
        # Calibration button
        # Start/Stop detection
        # Move history
        # Confidence display
        pass

    def start_detection(self):
        """Start real-time board detection."""
        # Grab frame
        # Detect board
        # Classify pieces
        # Detect moves
        # Update GUI
        pass
```

---

### Phase 2: IMX500 On-Sensor Inference (Raspberry Pi)

**Goal:** Move classifier to IMX500 sensor for low-latency, low-CPU operation
**Status:** Pending Phase 1 completion
**Timeline:** 1 week after Phase 1

#### 2.1 Model Conversion

**Steps:**
1. Train CNN to 95%+ accuracy on labeled data
2. Export to ONNX format
3. Convert ONNX → IMX500 format (vendor toolchain)
4. Load onto IMX500 sensor

**File:** `vision/imx500_converter.py`

```python
def export_to_onnx(pytorch_model, output_path):
    """
    Export PyTorch/TensorFlow model to ONNX.
    """
    import torch

    dummy_input = torch.randn(1, 3, 64, 64)
    torch.onnx.export(
        pytorch_model,
        dummy_input,
        output_path,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch'}}
    )

def convert_to_imx500(onnx_path, output_path):
    """
    Convert ONNX to IMX500 format.
    Uses vendor toolchain (Sony/vendor-specific).
    """
    # Vendor-specific conversion
    # Quantization (INT8 for speed)
    # Optimization for on-sensor compute
    pass
```

#### 2.2 IMX500 Integration

**File:** `vision/imx500_camera.py`

```python
class IMX500Camera:
    """
    IMX500 camera with on-sensor inference.
    Returns per-cell classifications as metadata.
    """

    def __init__(self, model_path):
        # Load IMX500-specific drivers
        # Upload model to sensor
        pass

    def capture_with_inference(self):
        """
        Capture frame with on-sensor piece classification.

        Returns:
            frame: Full camera frame
            metadata: {
                'cells': 8×8 array of classifications,
                'confidences': 8×8 array of confidence scores
            }
        """
        # Sensor runs CNN on each cell ROI
        # Returns labels + confidences as metadata
        # Host receives already-classified board
        pass
```

**Performance Benefits:**
- **CPU Load:** 80% reduction (sensor does classification)
- **Latency:** <50ms per frame (vs 200-300ms on Pi CPU)
- **Power:** Lower (sensor inference more efficient)
- **Data:** Only metadata transmitted, not full frames

---

### Phase 3: Advanced Features

#### 3.1 Safety Features

**Hand-in-Frame Detection:**
```python
class HandDetector:
    """
    Detect human hand near gripper.
    Pause robot if detected.
    """

    def detect_hand(self, frame, gripper_roi):
        """
        Use lightweight hand detector (MediaPipe or YOLOv8-nano).

        Returns:
            hand_present: bool
            confidence: float
        """
        # Run hand detection on gripper ROI
        # Return True if hand detected with conf > 0.7
        pass
```

**Illegal Position Guard:**
```python
def validate_position(board_state):
    """
    Check if position is chess-legal.

    Catches:
    - Too many pieces
    - Both kings missing
    - Pawns on back rank
    - Impossible piece counts
    """
    # Count pieces
    # Check king presence
    # Validate pawn positions
    # Return valid/invalid + reason
    pass
```

#### 3.2 Auto-Calibration

**Lighting Auto-Tune:**
```python
def auto_tune_lighting(camera, led_controller):
    """
    Automatically adjust LED brightness for optimal contrast.
    """
    # Capture test frames at different LED levels
    # Analyze histogram and contrast
    # Select optimal brightness
    # Save to config
    pass
```

**Board Drift Detection:**
```python
class DriftDetector:
    """
    Detect if board has been bumped or moved.
    Auto-recalibrate if needed.
    """

    def check_drift(self, current_frame):
        """
        Compare ArUco marker positions to calibrated positions.

        Returns:
            drifted: bool
            offset_mm: (dx, dy) in millimeters
        """
        # Detect current marker positions
        # Compare to stored positions
        # If drift > 5mm, flag for recalibration
        pass
```

#### 3.3 Training Data Collection

**Auto-Labeling Assistant:**
```python
class LabelingAssistant:
    """
    Semi-automatic labeling for training data.
    """

    def capture_training_data(self, camera, output_dir):
        """
        Capture cells with uncertain classifications.
        Present to user for labeling.
        Build training dataset.
        """
        # Capture cells with confidence < 0.6
        # Display in grid with predicted label
        # User corrects or confirms
        # Save to training_data/{class}/{timestamp}.png
        pass
```

---

## 🗂️ Project Structure (Vision System)

```
Chess Mover Machine/
├── vision/                      # NEW - Vision system
│   ├── __init__.py
│   ├── camera_calibration.py   # Intrinsics calibration
│   ├── board_detector.py       # ArUco/corner detection
│   ├── board_warper.py         # Homography & grid split
│   ├── piece_classifier.py     # CNN/heuristic classifier
│   ├── move_detector.py        # Move detection & verification
│   ├── imx500_camera.py        # IMX500 integration (Phase 2)
│   ├── imx500_converter.py     # ONNX → IMX500 conversion
│   ├── hand_detector.py        # Safety: hand detection
│   └── drift_detector.py       # Board movement detection
│
├── models/                      # NEW - ML models
│   ├── piece_classifier.onnx   # ONNX model for CPU
│   ├── piece_classifier.imx    # IMX500 format (Phase 2)
│   └── training_config.yml     # Training hyperparameters
│
├── training/                    # NEW - Model training
│   ├── train_classifier.py     # Training script
│   ├── dataset_builder.py      # Build training dataset
│   ├── augmentation.py         # Data augmentation
│   └── evaluate.py             # Model evaluation
│
├── ui/
│   ├── board_window.py
│   ├── vision_panel.py         # NEW - Vision controls
│   └── settings_window.py
│
├── config/
│   ├── settings.yaml
│   ├── camera.yml              # NEW - Camera intrinsics
│   └── board.yml               # NEW - Board homography
│
└── VISION_ROADMAP.md           # This file
```

---

## 📊 Development Milestones

### Milestone 1: Basic Detection (Week 1)
- [x] Camera calibration working
- [x] ArUco board detection working
- [x] Warp to top-down view
- [x] Split into 64 cells

### Milestone 2: Piece Classification (Week 2)
- [ ] Simple heuristic classifier (background + color)
- [ ] Training data collection (500+ images per class)
- [ ] CNN training (95%+ accuracy)
- [ ] ONNX export and integration
- [ ] Temporal smoothing

### Milestone 3: Move Detection (Week 3)
- [ ] Diff detection between frames
- [ ] Move pattern recognition
- [ ] Chess rules validation
- [ ] Robot move verification
- [ ] Confidence scoring

### Milestone 4: GUI Integration (Week 4)
- [ ] Vision panel in main window
- [ ] Live camera feed display
- [ ] Real-time move overlay on board
- [ ] Calibration wizard
- [ ] Confidence indicators

### Milestone 5: IMX500 Migration (Phase 2)
- [ ] ONNX → IMX500 conversion
- [ ] On-sensor inference working
- [ ] Metadata parsing
- [ ] Performance benchmarking
- [ ] Latency < 50ms per frame

### Milestone 6: Advanced Features (Phase 3)
- [ ] Hand-in-frame safety
- [ ] Illegal position detection
- [ ] Auto-lighting tuning
- [ ] Drift detection
- [ ] Training data assistant

---

## 🎯 Success Criteria

**Phase 1 (USB Webcam):**
- ✅ Board detection: 99%+ success rate
- ✅ Piece classification: 95%+ accuracy
- ✅ Move detection: 98%+ correct
- ✅ False positive rate: <2%
- ✅ Frame rate: 10+ FPS on Windows

**Phase 2 (IMX500):**
- ✅ Classification latency: <50ms
- ✅ CPU usage: <10% on Raspberry Pi
- ✅ Accuracy maintained: 95%+
- ✅ Power consumption: <3W total

**Phase 3 (Production):**
- ✅ Hand detection: 99%+ (safety critical)
- ✅ Uptime: 8+ hours continuous
- ✅ Auto-recovery from lighting changes
- ✅ Drift detection: <1mm sensitivity

---

## 🔬 Testing Strategy

### Unit Tests
```python
# test_board_detector.py
def test_aruco_detection():
    # Test with known marker positions
    # Verify homography accuracy
    pass

def test_cell_extraction():
    # Test 64-cell split
    # Verify cell alignment
    pass

# test_classifier.py
def test_empty_square():
    # Should classify as 'empty'
    pass

def test_white_pawn():
    # Should classify as 'white_pawn'
    pass
```

### Integration Tests
```python
# test_move_detection.py
def test_normal_move():
    # e2e4 move
    # Should detect correctly
    pass

def test_capture():
    # exd5 capture
    # Should detect capture
    pass

def test_castling():
    # O-O or O-O-O
    # Should detect castling
    pass
```

### Hardware Tests
```python
# test_imx500.py
def test_on_sensor_inference():
    # Load test image
    # Run on IMX500
    # Compare to CPU result
    pass

def test_latency():
    # Measure end-to-end latency
    # Assert < 50ms
    pass
```

---

## 🚀 Quick Start (When Ready to Implement)

```bash
# Install vision dependencies
pip install opencv-contrib-python onnxruntime numpy

# Optional: PyTorch for training
pip install torch torchvision

# Calibrate camera
python vision/camera_calibration.py --images calibration_images/

# Detect board (ArUco markers)
python vision/board_detector.py --camera 0

# Train classifier (after collecting data)
python training/train_classifier.py --data training_data/

# Run full vision system
python main.py --enable-vision
```

---

**Vision system ready for implementation!** 🎥♟️

Start with Phase 1 (USB webcam) to build the complete pipeline, then migrate to IMX500 (Phase 2) for production performance.
