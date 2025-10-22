# Raspberry Pi AI Camera Integration Guide

## Overview

This guide details how to integrate the Raspberry Pi AI Camera with Hailo neural network accelerator for chess piece detection and board vision in the Chess Mover Machine.

## Hardware Components

### Raspberry Pi AI Kit (2024)
- **Hailo-8L AI accelerator**: 13 TOPS neural network inference
- **AI HAT+**: 26 TOPS version available (better thermal management)
- **Performance**: 41-82 fps for YOLOv8s object detection (vs 2fps without Hailo)
- **Compatibility**: Requires Raspberry Pi 5

### Camera Options
- **Raspberry Pi Camera Module 3** (recommended)
- **Raspberry Pi High Quality Camera** (for better piece detection)
- **Resolution**: Minimum 1080p for reliable piece recognition

## Vision System Architecture

```
┌─────────────────────────────────────────┐
│         Raspberry Pi 5 + AI HAT+        │
│                                         │
│  ┌────────────┐      ┌──────────────┐  │
│  │   Camera   │─────>│ Hailo-8L NPU │  │
│  │  Module 3  │      │  (13 TOPS)   │  │
│  └────────────┘      └──────────────┘  │
│                            │            │
│                            ▼            │
│  ┌──────────────────────────────────┐  │
│  │  Neural Network Models           │  │
│  │  - Board Detection (YOLOv8)      │  │
│  │  - Piece Classification (CNN)    │  │
│  │  - Move Verification             │  │
│  └──────────────────────────────────┘  │
│                            │            │
│                            ▼            │
│  ┌──────────────────────────────────┐  │
│  │  Chess Mover Machine Integration │  │
│  │  - Position verification         │  │
│  │  - Move validation               │  │
│  │  - Error detection               │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## Implementation Strategy

### Phase 1: Hardware Setup & Testing (Pre-wiring)

#### 1.1 Model Selection & Training
```python
# Recommended models for Hailo optimization:
- YOLOv8n or YOLOv8s for board detection (optimized for Hailo)
- Custom CNN for piece classification (6 piece types x 2 colors)
- ResNet-18 or MobileNetV2 for real-time performance
```

#### 1.2 Dataset Requirements
- **Board detection**: 500+ images of chessboards from various angles
- **Piece detection**: 1000+ images per piece type (12 classes total)
- **Lighting conditions**: Multiple lighting scenarios (LED, natural, mixed)
- **Augmentation**: Rotations, brightness, contrast variations

#### 1.3 Model Training (Can be done now)
```python
# vision/train_model.py
import torch
from ultralytics import YOLO

# Train YOLOv8 for board detection
model = YOLO('yolov8n.pt')
results = model.train(
    data='chess_board.yaml',
    epochs=100,
    imgsz=640,
    device='cuda'  # Train on PC, deploy to Pi
)

# Export for Hailo optimization
model.export(format='onnx')
```

#### 1.4 Hailo Model Conversion
```bash
# Convert ONNX to Hailo format
hailo model-zoo compile \
  --ckpt yolov8n.onnx \
  --hw-arch hailo8l \
  --performance
```

### Phase 2: Integration with Existing Codebase

#### 2.1 Enhanced Vision Service
```python
# vision/hailo_service.py

from hailo_platform import HailoRT, Device
import cv2
import numpy as np

class HailoVisionService:
    """
    Vision service using Raspberry Pi AI Camera with Hailo accelerator.
    """

    def __init__(self, model_path: str):
        """
        Initialize Hailo device and load model.

        Args:
            model_path: Path to compiled Hailo model (.hef file)
        """
        self.device = Device()
        self.model = self.device.create_infer_model(model_path)
        self.camera = self._init_camera()

    def _init_camera(self):
        """Initialize Pi Camera with optimal settings."""
        from picamera2 import Picamera2

        camera = Picamera2()
        config = camera.create_still_configuration(
            main={"size": (1920, 1080)},
            buffer_count=2
        )
        camera.configure(config)
        camera.start()
        return camera

    def detect_board(self) -> dict:
        """
        Detect chessboard corners and orientation.

        Returns:
            dict with board corners and transformation matrix
        """
        frame = self.camera.capture_array()

        # Run inference on Hailo NPU
        input_data = self._preprocess(frame)
        output = self.model.run(input_data)

        # Post-process to get board corners
        corners = self._extract_corners(output)

        return {
            'corners': corners,
            'transform_matrix': self._get_transform_matrix(corners),
            'confidence': self._calculate_confidence(output)
        }

    def detect_pieces(self, board_image: np.ndarray) -> dict:
        """
        Detect all pieces on the board.

        Args:
            board_image: Warped board image (8x8 grid aligned)

        Returns:
            dict mapping squares to piece types
        """
        pieces = {}

        # Divide into 64 squares
        for rank in range(8):
            for file in range(8):
                square = self._extract_square(board_image, rank, file)

                # Classify piece using Hailo NPU
                piece_class = self._classify_piece(square)

                if piece_class != 'empty':
                    square_name = chr(ord('a') + file) + str(rank + 1)
                    pieces[square_name] = piece_class

        return pieces

    def verify_move(self, expected_move: str) -> bool:
        """
        Verify that a physical move matches expected move.

        Args:
            expected_move: UCI format move (e.g., "e2e4")

        Returns:
            True if move was executed correctly
        """
        # Capture before/after states
        before = self.capture_board_state()
        time.sleep(2)  # Wait for move execution
        after = self.capture_board_state()

        # Compare states
        return self._verify_move_diff(before, after, expected_move)

    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess image for model input."""
        # Resize to model input size
        resized = cv2.resize(frame, (640, 640))
        # Normalize
        normalized = resized / 255.0
        # Add batch dimension
        return np.expand_dims(normalized, axis=0)

    def _classify_piece(self, square_image: np.ndarray) -> str:
        """
        Classify piece in square using Hailo NPU.

        Returns:
            Piece type: 'white_pawn', 'black_king', 'empty', etc.
        """
        # Preprocess square image
        input_data = self._preprocess_square(square_image)

        # Run inference
        output = self.model.run(input_data)

        # Get prediction
        class_idx = np.argmax(output)
        confidence = output[class_idx]

        if confidence < 0.7:  # Threshold for empty square
            return 'empty'

        return self._class_idx_to_name(class_idx)
```

#### 2.2 Integration with Move Executor
```python
# logic/move_executor.py (additions)

class MoveExecutor:
    def __init__(self, ..., vision_service: Optional[HailoVisionService] = None):
        # ... existing code ...
        self.vision = vision_service

    def execute_move_with_verification(self, move_str: str) -> bool:
        """
        Execute move and verify with vision system.

        Args:
            move_str: UCI or SAN format move

        Returns:
            True if move executed and verified successfully
        """
        # Plan the move
        actions = self.plan_move(move_str)
        if not actions:
            return False

        # Capture initial board state
        if self.vision:
            initial_state = self.vision.capture_board_state()

        # Execute the move
        for action in actions:
            self._execute_action(action)

        # Verify move with vision
        if self.vision:
            return self.vision.verify_move(move_str)

        return True
```

### Phase 3: Performance Optimization

#### 3.1 Hailo-Specific Optimizations
```python
# Batch processing for multiple pieces
def detect_all_pieces_batch(self, board_image: np.ndarray) -> dict:
    """Detect all 64 squares in one batch inference."""
    # Extract all 64 squares
    squares = [self._extract_square(board_image, r, f)
               for r in range(8) for f in range(8)]

    # Stack into batch
    batch = np.stack(squares, axis=0)

    # Single inference call (much faster on Hailo)
    outputs = self.model.run(batch)

    # Parse results
    return self._parse_batch_results(outputs)
```

#### 3.2 Camera Settings for Optimal Detection
```python
# Optimal camera configuration
camera_config = {
    'resolution': (1920, 1080),
    'framerate': 30,
    'iso': 400,  # Fixed ISO for consistent exposure
    'shutter_speed': 10000,  # 1/100s
    'awb_mode': 'fluorescent',  # Consistent white balance
    'exposure_mode': 'sports'  # Fast shutter for moving pieces
}
```

### Phase 4: Error Detection & Recovery

#### 4.1 Move Verification
```python
def verify_move_execution(self, expected_from: str, expected_to: str) -> tuple:
    """
    Verify move was executed correctly.

    Returns:
        (success: bool, error_message: str)
    """
    # Capture current state
    current_state = self.vision.capture_board_state()

    # Check from square is empty
    if current_state.get(expected_from) != 'empty':
        return (False, f"Piece still on {expected_from}")

    # Check to square has correct piece
    expected_piece = self.chess_engine.piece_at(expected_to)
    actual_piece = current_state.get(expected_to)

    if not self._pieces_match(expected_piece, actual_piece):
        return (False, f"Wrong piece on {expected_to}")

    return (True, "Move verified")
```

#### 4.2 Automatic Error Correction
```python
def auto_correct_position(self) -> bool:
    """
    Detect position errors and attempt to correct them.

    Returns:
        True if position was corrected successfully
    """
    # Get current physical state
    physical_state = self.vision.capture_board_state()

    # Get expected logical state
    logical_state = self.chess_engine.get_board_state()

    # Find differences
    differences = self._find_differences(physical_state, logical_state)

    if not differences:
        return True

    # Attempt to correct each difference
    for square, (physical, logical) in differences.items():
        if not self._correct_square(square, physical, logical):
            return False

    return True
```

## Dataset Collection (Can Start Now)

### Data Collection Script
```python
# vision/collect_training_data.py

import cv2
from pathlib import Path
from datetime import datetime

class ChessDataCollector:
    """Collect training images for chess detection."""

    def __init__(self, output_dir: str = "datasets/chess"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def collect_board_images(self, num_images: int = 500):
        """
        Collect images of chessboards.

        Instructions:
        - Take photos from different angles (overhead, slight angle)
        - Different lighting conditions
        - Different board positions
        - Include some with pieces, some without
        """
        print(f"Collecting {num_images} board images...")
        print("Press SPACE to capture, ESC to exit")

        cap = cv2.VideoCapture(0)
        count = 0

        while count < num_images:
            ret, frame = cap.read()
            if not ret:
                break

            cv2.imshow('Data Collection', frame)
            key = cv2.waitKey(1)

            if key == ord(' '):  # Space to capture
                filename = f"board_{count:04d}_{datetime.now():%Y%m%d_%H%M%S}.jpg"
                cv2.imwrite(str(self.output_dir / filename), frame)
                count += 1
                print(f"Captured {count}/{num_images}")

            elif key == 27:  # ESC to exit
                break

        cap.release()
        cv2.destroyAllWindows()

    def collect_piece_images(self, piece_type: str, color: str, num_images: int = 100):
        """
        Collect images of individual pieces.

        Args:
            piece_type: 'pawn', 'knight', 'bishop', 'rook', 'queen', 'king'
            color: 'white' or 'black'
            num_images: Number of images to collect
        """
        piece_dir = self.output_dir / 'pieces' / f"{color}_{piece_type}"
        piece_dir.mkdir(parents=True, exist_ok=True)

        print(f"Collecting {num_images} images of {color} {piece_type}")
        print("Place piece on square and rotate/move for variety")

        # Similar capture loop as above
        # ... implementation ...
```

## Testing Plan (Before Hardware)

### Unit Tests
```python
# tests/test_vision_hailo.py

import pytest
from vision.hailo_service import HailoVisionService

def test_board_detection():
    """Test board corner detection."""
    vision = HailoVisionService('models/board_detect.hef')
    result = vision.detect_board()

    assert 'corners' in result
    assert len(result['corners']) == 4
    assert result['confidence'] > 0.8

def test_piece_classification():
    """Test piece type classification."""
    vision = HailoVisionService('models/piece_classify.hef')

    # Load test image of white pawn
    test_image = cv2.imread('tests/fixtures/white_pawn.jpg')
    result = vision._classify_piece(test_image)

    assert result == 'white_pawn'

def test_move_verification():
    """Test move verification."""
    vision = HailoVisionService('models/board_detect.hef')

    # Simulate e2-e4 move
    result = vision.verify_move('e2e4')

    assert result == True
```

## Performance Targets

### With Hailo AI Accelerator
- **Board detection**: < 50ms per frame
- **Piece classification**: < 100ms for all 64 squares (batch mode)
- **Move verification**: < 200ms total
- **Frame rate**: 30+ FPS for continuous monitoring
- **Accuracy**: > 98% for piece detection, > 99% for move verification

### Without Accelerator (Baseline)
- **Board detection**: 500-1000ms per frame
- **Piece classification**: 2-5 seconds for all 64 squares
- **Frame rate**: 2-5 FPS

## Cost Breakdown

- **Raspberry Pi 5 (8GB)**: $80
- **Raspberry Pi AI Kit (Hailo-8L)**: $70
- **Camera Module 3**: $25
- **Camera mount/positioning**: $20
- **Total**: ~$195

## Next Steps (Pre-wiring)

1. ✅ **Model Training** (can start now with existing chess datasets)
   - Download public chess datasets
   - Train YOLOv8 for board detection
   - Train CNN for piece classification
   - Convert models to ONNX format

2. ✅ **Software Development** (can do now)
   - Implement `HailoVisionService` class
   - Create data collection scripts
   - Write unit tests
   - Integration with existing codebase

3. ⏳ **Dataset Collection** (wait for camera)
   - Collect 500+ board images
   - Collect 100+ images per piece type
   - Various lighting conditions

4. ⏳ **Hardware Setup** (wait for Pi + AI Kit)
   - Install Raspberry Pi OS
   - Install Hailo SDK
   - Mount camera
   - Convert models to Hailo format

5. ⏳ **Integration Testing** (wait for hardware)
   - Test on actual chess board
   - Calibrate detection thresholds
   - Fine-tune model if needed

## Resources

### Documentation
- [Raspberry Pi AI Kit Setup](https://www.raspberrypi.com/documentation/accessories/ai-kit.html)
- [Hailo Model Zoo](https://github.com/hailo-ai/hailo_model_zoo)
- [Hailo RPi5 Examples](https://github.com/hailo-ai/hailo-rpi5-examples)

### Pre-trained Models
- YOLOv8 (Ultralytics): https://github.com/ultralytics/ultralytics
- Chess piece datasets: Roboflow Universe

### Code Examples
- [raspberry-chess](https://github.com/ale93111/raspberry-chess): YOLOv5 implementation
- [neural-chessboard](https://github.com/maciejczyzewski/neural-chessboard): CNN approach

## Conclusion

The Raspberry Pi AI Camera with Hailo accelerator offers excellent performance for real-time chess piece detection and move verification. The key advantages are:

1. **Performance**: 40-80x faster than CPU-only inference
2. **Power efficiency**: Low power consumption for always-on monitoring
3. **Cost effective**: ~$200 total hardware cost
4. **Proven technology**: Hailo is used in production AI applications

**We can start model training and software development immediately**, even before the hardware arrives. This will significantly reduce integration time once the hardware is available.
