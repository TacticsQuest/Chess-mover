# Vision Training Strategy for Chess Mover Machine

## Recommended Approach: Single Chess Set Training

### Why Train on ONE Chess Set?

**For the Chess Mover Machine, training on your specific chess set provides:**
- ✅ **98-99% accuracy** (vs 90-95% for multi-set)
- ✅ **Faster training** (1-2 hours vs 6-8 hours)
- ✅ **Fewer images needed** (100-200 vs 1000+ per piece)
- ✅ **More reliable** for automated gameplay
- ✅ **Easier to debug** errors

### The Key Insight

```
Your Machine = Fixed Environment
├── Same chess set always
├── Same board location
├── Same lighting setup
└── Same camera angle

→ Perfect for specialized model! ✓
```

## Training Workflow

### Step 1: Prepare Your Environment

```bash
# 1. Set up consistent lighting
- Use LED strips or desk lamp
- Same brightness every session
- Minimize shadows on board

# 2. Position camera
- Mount at consistent angle (directly overhead recommended)
- Same height every time (~30-40cm above board)
- Minimize movement/vibration

# 3. Clean your chess pieces
- Fingerprints can confuse vision
- Consistent appearance
```

### Step 2: Get Initial Dataset (3 options - pick ONE)

#### Option A: Use Existing Online Datasets (FASTEST! ⚡)

**Pre-trained datasets available:**
- **Roboflow Universe**: 50+ chess piece datasets
  - https://universe.roboflow.com/search?q=chess+pieces
  - Already annotated and labeled
  - Download in YOLO, COCO, or Pascal VOC format
  - 1,000-10,000+ images per dataset

- **Kaggle Chess Datasets**:
  - "Chess Pieces Detection" - 5,000+ images
  - "Chess Piece Recognition" - 3,000+ images
  - Ready to use for training

- **Benefits**:
  - ✅ **Instant dataset** - download in minutes
  - ✅ **Pre-labeled** - no annotation needed
  - ✅ **Large variety** - multiple chess sets
  - ✅ **Start training immediately**

```bash
# Download from Roboflow (example)
pip install roboflow

python
from roboflow import Roboflow
rf = Roboflow(api_key="your_key")
project = rf.workspace().project("chess-pieces-dataset")
dataset = project.version(1).download("yolov8")

# Dataset ready to use!
# Then: Fine-tune with your specific pieces (50-100 images)
```

#### Option B: Record Video of Your Pieces (EASIER! 🎥)

**Much faster than taking 1,000 photos!**

```bash
# Record 30-60 second video per piece type
# Just rotate piece slowly while recording
# Script extracts frames automatically

# Example: Collect white pawn images from video
python vision/collect_training_data.py \
    --mode webcam \
    --piece pawn \
    --color white \
    --duration 30

# This extracts ~90 images from 30-second video!
# Total time for all 12 pieces: ~10-15 minutes
```

**Alternative: Use phone/camera to record video files**
```bash
# Record video on phone, transfer to computer
python vision/collect_training_data.py \
    --mode video \
    --video my_white_pawn.mp4 \
    --piece pawn \
    --color white \
    --interval 10 \
    --max-images 200
```

#### Option C: Manual Photo Capture (ORIGINAL METHOD)

```python
# Run data collection script
python vision/collect_training_data.py \
    --mode manual \
    --piece pawn \
    --color white \
    --max-images 100

# For each piece type:
# ├── Place piece on different squares (light and dark)
# ├── Rotate piece slightly between captures
# ├── Take 100-150 images
# └── Capture button: SPACE, Done: ESC

# Total images needed:
# - 12 piece types × 100 images = 1,200 images
# - Collection time: ~1-2 hours
```

### Recommended Hybrid Approach (BEST! 🎯)

**Combine online dataset + your specific pieces:**

1. **Download base dataset** from Roboflow/Kaggle (10 minutes)
2. **Record short videos** of YOUR pieces (10-15 minutes)
3. **Fine-tune model** on your pieces (1-2 hours training)
4. **Result**: Best of both worlds!
   - General piece recognition from online data
   - Specialized accuracy on YOUR pieces
   - 98-99% accuracy on your board

### Step 3: Label and Organize

```
datasets/
└── my_pieces/
    ├── train/
    │   ├── white_pawn/
    │   │   ├── img_001.jpg
    │   │   ├── img_002.jpg
    │   │   └── ... (80 images)
    │   ├── white_knight/
    │   ├── white_bishop/
    │   ├── ... (all 12 piece types)
    │   └── empty/  (images of empty squares)
    │
    └── val/
        ├── white_pawn/  (20 validation images)
        └── ... (all 12 piece types)
```

### Step 4: Train the Model

```python
# Train on YOUR pieces only
python vision/train_model.py \
    --data datasets/my_pieces/config.yaml \
    --epochs 100 \
    --img-size 224 \
    --batch-size 32

# Training time: 1-2 hours on desktop GPU
# Result: piece_classifier.pt (trained model)
```

### Step 5: Test Accuracy

```python
# Test on validation images
python vision/test_model.py --model piece_classifier.pt

# Expected results:
# ├── Overall accuracy: 98-99%
# ├── Per-class accuracy:
# │   ├── White Pawn: 99.2%
# │   ├── White Knight: 98.8%
# │   ├── White Bishop: 99.1%
# │   └── ... (all pieces > 98%)
# └── Misclassifications: < 1%

# If accuracy is lower:
# → Collect more images of problem pieces
# → Check lighting consistency
# → Verify image quality
```

### Step 6: Deploy to Raspberry Pi

```bash
# Convert to Hailo format
hailo model-zoo compile \
    --ckpt piece_classifier.onnx \
    --hw-arch hailo8l \
    --performance

# Copy to Pi
scp piece_classifier.hef pi@raspberrypi:/home/pi/chess_mover/models/

# Test on actual board
python vision/test_live.py --model models/piece_classifier.hef
```

## When to Retrain

### ✅ Retrain if:
- You change to a different chess set
- You move machine to room with very different lighting
- Accuracy drops below 95%
- You modify camera position significantly

### ❌ Don't retrain for:
- Different board positions (model handles this)
- Playing different games
- Normal lighting variations (model is robust)
- Moving board a few inches

## Multi-Set Training (Not Recommended)

**Only use if you frequently swap chess sets.**

### Drawbacks:
```
Accuracy Impact:
├── Single set: 99% → ~1 error per 100 moves
└── Multi set: 92% → ~8 errors per 100 moves

Training Time:
├── Single set: 1-2 hours
└── Multi set: 6-8 hours

Dataset Size:
├── Single set: 1,200 images
└── Multi set: 10,000+ images

Complexity:
├── Single set: Simple, clear boundaries
└── Multi set: Overlapping features, confusion
```

## Advanced: Hybrid Approach

If you need flexibility:

```python
# Train two models:
# 1. Specific model (primary): 99% accuracy on YOUR pieces
# 2. General model (fallback): 90% accuracy on ANY pieces

class HybridClassifier:
    def __init__(self):
        self.specific = load_model("my_pieces.hef")
        self.general = load_model("general_pieces.hef")

    def classify(self, square_image):
        # Try specific model first
        result1 = self.specific.predict(square_image)

        if result1.confidence > 0.95:
            return result1  # High confidence

        # Low confidence? Check general model
        result2 = self.general.predict(square_image)

        if result1.piece == result2.piece:
            return result1  # Both agree
        else:
            # Conflict - need manual verification
            return None
```

## Data Augmentation

**Increase training data artificially:**

```python
# Apply transformations to existing images
augmentation_pipeline = [
    RandomBrightness(0.8, 1.2),  # Lighting variation
    RandomRotation(-15, 15),      # Slight rotation
    RandomBlur(0, 2),             # Camera blur
    GaussianNoise(0, 0.02)        # Sensor noise
]

# This multiplies your dataset:
# 100 real images → 500 augmented images
# Still trains on YOUR specific pieces!
```

## Troubleshooting Low Accuracy

### Problem: Knight/Bishop Confusion

```python
# Issue: Knights and bishops look similar from above
# Solution: Collect more images from slight angle
angles = [0°, 5°, -5°]  # Camera tilt variations
```

### Problem: Light/Dark Square Confusion

```python
# Issue: Piece looks different on light vs dark squares
# Solution: Ensure 50/50 split in training data
images_on_light_squares = 50
images_on_dark_squares = 50
```

### Problem: Pawn/Rook Confusion

```python
# Issue: Similar shapes when viewed from above
# Solution: Capture height information or side profile
camera_angles = ["overhead", "slight_angle"]
```

## Expected Performance

### Single-Set Training (Recommended):

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| Overall Accuracy | 98-99% | 95-98% | <95% |
| Per-class Accuracy | >98% | >95% | <95% |
| Inference Speed (Hailo) | 40-80 FPS | 20-40 FPS | <20 FPS |
| Training Time | 1-2 hours | 2-4 hours | >4 hours |
| Dataset Size | 1,200 images | 800-1,200 | <800 |

### Multi-Set Training (If needed):

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| Overall Accuracy | 92-95% | 88-92% | <88% |
| Per-class Accuracy | >90% | >85% | <85% |
| Inference Speed (Hailo) | 40-80 FPS | 20-40 FPS | <20 FPS |
| Training Time | 6-8 hours | 4-6 hours | >8 hours |
| Dataset Size | 10,000+ images | 5,000-10,000 | <5,000 |

## Cost-Benefit Analysis

```
Single-Set Approach:
├── Time investment: ~4-5 hours total
│   ├── Image collection: 2 hours
│   ├── Training: 2 hours
│   └── Testing/deployment: 1 hour
├── Accuracy: 98-99%
└── Maintenance: Retrain if chess set changes (~3 hours)

Multi-Set Approach:
├── Time investment: ~20-30 hours total
│   ├── Image collection: 15-20 hours (multiple sets)
│   ├── Training: 6-8 hours
│   └── Testing/deployment: 2 hours
├── Accuracy: 90-95%
└── Maintenance: Occasional retraining for new set styles

Recommendation: Single-Set for 5x less work and higher accuracy! ✓
```

## Real-World Testing Checklist

Before deploying your trained model:

```python
✓ Test on all 64 squares
✓ Test with different lighting (morning, afternoon, evening)
✓ Test with board rotated 180° (if applicable)
✓ Test after moving pieces multiple times
✓ Test empty board detection
✓ Test full starting position detection
✓ Test mid-game positions
✓ Test with camera vibration/movement
✓ Verify inference speed (should be 40+ FPS with Hailo)
✓ Check for consistent misclassifications (retrain if needed)
```

## Summary

**For Chess Mover Machine:**
1. ✅ **Train on YOUR specific chess set**
2. ✅ Collect 100-150 images per piece type
3. ✅ Train for 1-2 hours on desktop GPU
4. ✅ Deploy to Raspberry Pi with Hailo NPU
5. ✅ Expect 98-99% accuracy
6. ✅ Retrain only if chess set changes

**Avoid:**
- ❌ Training on multiple chess sets (unless required)
- ❌ Over-complicating the dataset
- ❌ Accepting accuracy below 95%

**The result:** A highly accurate, specialized vision system that reliably detects pieces on YOUR board in YOUR environment - exactly what you need!
