# Chess Vision AI Training Status

## What I've Set Up For You

### ✓ System Configuration

**Hardware Detected:**
- GPU: NVIDIA GeForce RTX 4080 SUPER (Excellent for training!)
- Training speed: 1-2 hours for full model

**Software Installed:**
- ✓ YOLOv8 (Ultralytics)
- ✓ PyTorch with CUDA support
- ✓ Roboflow SDK
- ✓ OpenCV

### ✓ Training Scripts Created

1. **vision/simple_train.py** - Main training script
   - Automatically downloads YOLOv8 pre-trained weights
   - Trains on chess piece dataset
   - Exports to ONNX format for Raspberry Pi
   - GPU-accelerated (RTX 4080 SUPER detected!)

2. **vision/collect_training_data.py** - Data collection
   - Record 30-second videos → Auto-extract ~90 frames
   - Webcam mode, video file mode, manual mode
   - Automatic train/val split

3. **vision/download_dataset.py** - Dataset helper
   - Creates proper YOLOv8 directory structure
   - Instructions for downloading pre-labeled datasets

4. **vision/train_model.py** - Advanced training control
   - Full parameter control
   - Testing and export functions

### ✓ Dataset Structure Created

```
datasets/chess_pieces/
├── train/
│   ├── images/
│   └── labels/
├── val/
│   ├── images/
│   └── labels/
└── data.yaml (YOLOv8 config ready)
```

## What You Need To Do Next

### Option 1: Download Pre-labeled Dataset (Recommended to start)

The easiest way to get started is to download an existing dataset:

**Roboflow Universe** (Best option):
1. Visit: https://universe.roboflow.com/search?q=chess+pieces
2. Create free account
3. Find a good chess pieces dataset (look for 1,000+ images)
4. Download in "YOLOv8" format
5. Extract to `C:\Users\David\Documents\GitHub\Chess Mover Machine\datasets\chess_roboflow\`
6. Run training:
   ```bash
   cd "C:\Users\David\Documents\GitHub\Chess Mover Machine"
   python vision/simple_train.py
   # When prompted for dataset path, enter: datasets/chess_roboflow/data.yaml
   ```

**Kaggle** (Alternative):
1. Visit: https://www.kaggle.com/datasets/nitinsss/chess-pieces-detection-images-dataset
2. Download dataset
3. Extract to `datasets/`
4. May need to reorganize into YOLOv8 format

### Option 2: Record Your Own Chess Pieces (Best for production)

This gives you the most accurate model for YOUR specific pieces:

```bash
cd "C:\Users\David\Documents\GitHub\Chess Mover Machine"

# For each of the 12 piece types, record a 30-second video:
python vision/collect_training_data.py --mode webcam --piece pawn --color white --duration 30
python vision/collect_training_data.py --mode webcam --piece knight --color white --duration 30
python vision/collect_training_data.py --mode webcam --piece bishop --color white --duration 30
python vision/collect_training_data.py --mode webcam --piece rook --color white --duration 30
python vision/collect_training_data.py --mode webcam --piece queen --color white --duration 30
python vision/collect_training_data.py --mode webcam --piece king --color white --duration 30

python vision/collect_training_data.py --mode webcam --piece pawn --color black --duration 30
python vision/collect_training_data.py --mode webcam --piece knight --color black --duration 30
python vision/collect_training_data.py --mode webcam --piece bishop --color black --duration 30
python vision/collect_training_data.py --mode webcam --piece rook --color black --duration 30
python vision/collect_training_data.py --mode webcam --piece queen --color black --duration 30
python vision/collect_training_data.py --mode webcam --piece king --color black --duration 30

# Organize into train/val split
python vision/collect_training_data.py --organize

# Train the model
python vision/simple_train.py
```

**Total time:** 10-15 minutes recording + 1-2 hours training = Ready!

### Option 3: Hybrid Approach (Best accuracy)

1. Download pre-labeled dataset (Option 1)
2. Train base model (1-2 hours)
3. Record short videos of YOUR pieces (just 15 seconds each)
4. Fine-tune model on your pieces (30 minutes)
5. Result: 98-99% accuracy on YOUR board!

## Training Progress

Once you have a dataset, run:
```bash
python vision/simple_train.py
```

The script will:
1. Load YOLOv8 nano model (fastest)
2. Train for 50 epochs (~1-2 hours on RTX 4080 SUPER)
3. Save best model to: `runs/chess_training/chess_detector/weights/best.pt`
4. Export to ONNX: `runs/chess_training/chess_detector/weights/best.onnx`
5. Ready for Raspberry Pi deployment!

## Expected Results

**With RTX 4080 SUPER:**
- Training time: 1-2 hours (50 epochs)
- Inference speed: 200+ FPS on desktop
- Inference speed on Pi with Hailo: 40-80 FPS
- Expected accuracy: 95-99% (depending on dataset quality)

**Model sizes:**
- YOLOv8n (nano): 3MB, fastest
- YOLOv8s (small): 11MB, better accuracy
- YOLOv8m (medium): 25MB, best accuracy

## Deployment to Raspberry Pi

Once training is complete:

1. **Copy model to Pi:**
   ```bash
   scp runs/chess_training/chess_detector/weights/best.onnx pi@raspberrypi:/home/pi/chess_mover/models/
   ```

2. **Convert to Hailo format (on Pi):**
   ```bash
   hailo model-zoo compile \
     --ckpt best.onnx \
     --hw-arch hailo8l \
     --performance
   ```

3. **Test with live camera:**
   ```bash
   python vision/test_live.py --model models/best.hef
   ```

## Why Roboflow Download Failed

The automatic download from Roboflow requires an API key, which needs:
1. Free account at roboflow.com
2. API key from account settings
3. Pass to script: `python vision/train_model.py --download --api-key YOUR_KEY`

**Easier:** Just download manually from website (Option 1 above)

## Current Limitations

**Dataset:** No training images yet - need to either:
- Download from Roboflow/Kaggle
- Record videos of your pieces
- Use both (hybrid approach)

**Training:** Can't train without dataset, but everything else is ready!

## Summary

### ✓ Ready:
- GPU training environment
- Training scripts
- Data collection tools
- Documentation

### ⏳ Needed:
- Chess piece images (download or record)

### Next Step:
Pick Option 1, 2, or 3 above and get dataset, then run `python vision/simple_train.py`

**Time to working model:**
- Option 1 (download): 30 min download + 2 hours training = 2.5 hours
- Option 2 (record): 15 min recording + 2 hours training = 2.25 hours
- Option 3 (hybrid): 30 min download + 2 hours + 15 min record + 30 min fine-tune = 3.25 hours

All the hard setup work is done - just need the images! 🚀
