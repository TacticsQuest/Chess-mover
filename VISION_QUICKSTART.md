# Vision System Quick Start Guide

> **TL;DR**: Use online datasets + 10 minutes of video = Ready to train! 🚀

## Fastest Path to Working Vision (< 1 hour setup)

### Method 1: Pre-trained Dataset (Recommended for Testing)

**Total time: ~30 minutes**

```bash
# 1. Install dependencies (5 min)
pip install roboflow ultralytics opencv-python

# 2. Download dataset from Roboflow (5 min)
python
from roboflow import Roboflow
rf = Roboflow(api_key="your_key")  # Free account at roboflow.com
project = rf.workspace("chess-detection").project("chess-pieces-v2")
dataset = project.version(1).download("yolov8")

# 3. Train model (15 min on GPU, 2 hours on CPU)
from ultralytics import YOLO
model = YOLO('yolov8n.pt')  # Nano model for speed
model.train(
    data='chess-pieces-v2/data.yaml',
    epochs=50,
    imgsz=640,
    batch=16
)

# 4. Test it!
results = model.predict('test_image.jpg')
```

**Result**: Working chess piece detector in 30 minutes! ✓

---

### Method 2: Custom Dataset with Video (Recommended for Production)

**Total time: ~2-3 hours**

#### Step 1: Record Videos (10-15 minutes)

**Equipment needed:**
- Webcam or phone camera
- Your chess set
- Good lighting

**Recording instructions:**
```bash
# For each piece type (12 total):
# 1. Place piece on board
# 2. Run collection script:

python vision/collect_training_data.py \
    --mode webcam \
    --piece pawn \
    --color white \
    --duration 30

# 3. While recording (30 seconds):
#    - Slowly rotate piece
#    - Move to different squares (light and dark)
#    - Camera extracts ~90 frames automatically

# Repeat for all 12 piece types:
# - white_pawn, white_knight, white_bishop, white_rook, white_queen, white_king
# - black_pawn, black_knight, black_bishop, black_rook, black_queen, black_king

# Also record empty squares:
python vision/collect_training_data.py \
    --mode webcam \
    --piece empty \
    --duration 20
```

**Total recording time: ~10-15 minutes**
**Total images collected: ~1,100 images** (90 per piece × 12 pieces)

#### Step 2: Organize Dataset (1 minute)

```bash
# Automatically split into train/val sets (80/20)
python vision/collect_training_data.py --organize

# Creates structure:
# datasets/my_chess_set/
# ├── train/          (880 images)
# │   ├── white_pawn/
# │   ├── white_knight/
# │   └── ...
# ├── val/            (220 images)
# │   ├── white_pawn/
# │   └── ...
# └── config.yaml
```

#### Step 3: Train Model (1-2 hours)

```bash
# Train on desktop GPU (or Raspberry Pi if patient)
python vision/train_model.py \
    --data datasets/my_chess_set/config.yaml \
    --epochs 100 \
    --img-size 224 \
    --batch-size 32

# Training time:
# - Desktop GPU: 1-2 hours
# - Laptop CPU: 4-6 hours
# - Raspberry Pi 5: 8-12 hours (but works!)
```

#### Step 4: Test Accuracy (5 minutes)

```bash
# Test on validation set
python vision/test_model.py --model runs/train/exp/weights/best.pt

# Expected results for single-set training:
# ✓ Overall accuracy: 98-99%
# ✓ Per-class accuracy: >98%
# ✓ Inference speed: 40-80 FPS (with Hailo NPU)
```

#### Step 5: Convert for Hailo NPU (10 minutes)

```bash
# Export to ONNX format
python vision/export_model.py \
    --model runs/train/exp/weights/best.pt \
    --format onnx

# Convert to Hailo format (requires Hailo SDK on Pi)
hailo model-zoo compile \
    --ckpt best.onnx \
    --hw-arch hailo8l \
    --performance

# Result: best.hef (Hailo Executable Format)
```

#### Step 6: Deploy to Raspberry Pi (5 minutes)

```bash
# Copy model to Pi
scp best.hef pi@raspberrypi:/home/pi/chess_mover/models/

# Test live detection
ssh pi@raspberrypi
cd /home/pi/chess_mover
python vision/test_live.py --model models/best.hef

# Should see:
# - 40-80 FPS inference speed
# - Real-time piece detection
# - Move verification working
```

---

### Method 3: Hybrid Approach (BEST for Production! 🎯)

**Combines best of both worlds:**

1. **Download base dataset** from Roboflow (general chess knowledge)
2. **Record videos of YOUR pieces** (specialization)
3. **Fine-tune** pre-trained model on your pieces

```bash
# Step 1: Download base dataset
from roboflow import Roboflow
rf = Roboflow(api_key="your_key")
project = rf.workspace("chess").project("pieces")
dataset = project.version(1).download("yolov8")

# Step 2: Train base model
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
model.train(
    data='pieces/data.yaml',
    epochs=50,
    name='base_model'
)

# Step 3: Collect YOUR pieces (just 50 images per type via video)
python vision/collect_training_data.py \
    --mode webcam \
    --piece pawn \
    --color white \
    --duration 15  # Only 15 seconds needed!

# Step 4: Fine-tune on YOUR pieces
model = YOLO('runs/train/base_model/weights/best.pt')
model.train(
    data='datasets/my_chess_set/config.yaml',
    epochs=30,
    name='fine_tuned'
)
```

**Result:**
- ✅ Generalizes to different chess sets (from base dataset)
- ✅ 98-99% accuracy on YOUR board (from fine-tuning)
- ✅ Only 10 minutes of video recording needed
- ✅ Faster training (fine-tuning is quicker)

---

## Available Online Datasets

### Roboflow Universe (Recommended)
- **50+ chess datasets** available
- **Already labeled** and ready to use
- **Multiple formats**: YOLO, COCO, Pascal VOC
- **Free tier available**
- URL: https://universe.roboflow.com/search?q=chess+pieces

**Top datasets:**
1. "Chess Pieces YOLO" - 5,000 images
2. "Chess Board Detection" - 3,000 images
3. "Chess Piece Recognition" - 8,000 images

### Kaggle
- "Chess Pieces Detection" - 5,000+ images
- "Chess Piece Recognition Dataset" - 3,000+ images
- URL: https://www.kaggle.com/search?q=chess+pieces

### Public GitHub Repos
- `neural-chessboard` dataset - 1,500 images
- `raspberry-chess` dataset - 2,000 images

---

## Video Recording Tips

### Best Practices

**Lighting:**
- Use consistent bright lighting
- Avoid harsh shadows
- LED desk lamp works great

**Camera Position:**
- Mount camera overhead (~30-40cm above board)
- Keep camera steady (use tripod or mount)
- Ensure entire square is visible

**Recording Motion:**
- **Slow rotation** - 360° over 30 seconds
- Move piece to 4-5 different squares per video
- Include both light and dark squares
- Small position variations (center, edge of square)

**What to Record:**
```
For each piece (30 seconds):
├── 0-10s:  Piece on light square, slow rotation
├── 10-20s: Move to dark square, slow rotation
└── 20-30s: Move to different light square, rotation
```

### Phone Recording Alternative

Can't use webcam? Record on phone and transfer:

```bash
# 1. Record video on phone (MP4 format)
# 2. Transfer to computer
# 3. Extract frames:

python vision/collect_training_data.py \
    --mode video \
    --video "/path/to/phone_video.mp4" \
    --piece pawn \
    --color white \
    --interval 5 \
    --max-images 200
```

---

## Training Performance Expectations

### Hardware Requirements

**Minimum (works but slow):**
- CPU: Any modern processor
- RAM: 8GB
- Storage: 5GB free
- Training time: 4-6 hours

**Recommended:**
- GPU: NVIDIA RTX 3060 or better
- RAM: 16GB
- Storage: 10GB free
- Training time: 1-2 hours

**Raspberry Pi 5:**
- Works for training (be patient!)
- Much faster with Hailo NPU for inference
- Can train overnight (8-12 hours)

### Model Size Options

**YOLOv8 variants:**
- `yolov8n` (nano): Fastest, 3MB, 40-80 FPS on Hailo
- `yolov8s` (small): Better accuracy, 11MB, 30-50 FPS
- `yolov8m` (medium): Best accuracy, 25MB, 20-30 FPS

**Recommendation**: Start with `yolov8n` for speed, upgrade to `yolov8s` if accuracy isn't sufficient.

---

## Troubleshooting

### Low Accuracy (<95%)

**Problem**: Model confuses similar pieces (knight/bishop)

**Solutions:**
1. Collect more images of problem pieces (100 → 200)
2. Ensure good lighting in training images
3. Record from slight angle (not just overhead)
4. Increase training epochs (50 → 100)

### Slow Inference

**Problem**: Detection takes >500ms per frame

**Solutions:**
1. Use smaller model (yolov8n instead of yolov8m)
2. Reduce image resolution (640 → 416)
3. Use Hailo NPU (40-80x speedup!)
4. Batch process squares instead of individual

### Empty Square Confusion

**Problem**: Model detects pieces on empty squares

**Solutions:**
1. Collect more empty square images (100 → 200)
2. Vary lighting in empty square images
3. Include both light and dark empty squares
4. Adjust confidence threshold (0.5 → 0.7)

---

## What You Can Do Now (Before Hardware Arrives)

### Immediate Actions (No Hardware Needed)

1. ✅ **Download datasets** from Roboflow/Kaggle
2. ✅ **Train base model** on desktop GPU
3. ✅ **Test with webcam** (any USB camera works)
4. ✅ **Develop detection code** using mock mode
5. ✅ **Create unit tests** for vision system
6. ✅ **Experiment with models** to find best architecture

### When Camera Arrives

1. Record videos of YOUR chess pieces (15 minutes)
2. Fine-tune model on your pieces (1-2 hours)
3. Test accuracy and adjust if needed
4. Deploy to Raspberry Pi

### When Hailo NPU Arrives

1. Convert trained model to Hailo format
2. Deploy to Raspberry Pi
3. Integrate with Chess Mover Machine
4. Enjoy 40-80 FPS real-time detection! 🚀

---

## Summary

**Fastest path to working vision:**

```
Option 1 (Testing): Download dataset → Train → Done (30 min)
Option 2 (Custom): Record 15 min video → Train → Done (2-3 hours)
Option 3 (Best):   Download + Record → Fine-tune → Done (1-2 hours)
```

**Recommended approach:**
1. Start with **Option 1** to learn the process
2. Move to **Option 3** for production deployment
3. Achieve 98-99% accuracy on your board
4. Deploy to Hailo NPU for real-time inference

**No hardware? No problem!**
- Download datasets now
- Train models on desktop
- Test with webcam
- Ready to deploy when hardware arrives

Happy training! 🎯
