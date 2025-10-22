"""
Simple Chess Piece Training Script
Downloads dataset and trains YOLOv8 model - Windows compatible
"""

from ultralytics import YOLO
import torch
from pathlib import Path
import sys

print("="*70)
print("CHESS PIECE DETECTION TRAINING")
print("="*70)

# Check GPU
if torch.cuda.is_available():
    device = 'cuda'
    gpu_name = torch.cuda.get_device_name(0)
    print(f"\n[+] GPU detected: {gpu_name}")
else:
    device = 'cpu'
    print(f"\n[!] No GPU detected - training will be slower on CPU")

# Try to download dataset from Roboflow
print("\n[*] Attempting to download chess dataset from Roboflow...")
print("[*] This may take a few minutes...\n")

try:
    from roboflow import Roboflow

    # Try public chess dataset
    rf = Roboflow(api_key="placeholder")
    project = rf.workspace("roboflow-jvuqo").project("chess-pieces-new")
    dataset = project.version(23).download("yolov8")

    dataset_path = Path(dataset.location) / "data.yaml"
    print(f"\n[+] Dataset downloaded successfully!")
    print(f"[+] Location: {dataset_path}")

except Exception as e:
    print(f"\n[-] Dataset download failed: {str(e)[:100]}")
    print("\n[*] Alternative: Using Kaggle chess dataset...")
    print("[!] Please download manually from:")
    print("    https://www.kaggle.com/datasets/nitinsss/chess-pieces-detection-images-dataset")
    print("    or")
    print("    https://universe.roboflow.com/roboflow-jvuqo/chess-pieces-new/dataset/23")

    # Create placeholder dataset for demo
    print("\n[*] Creating placeholder dataset structure for testing...")
    dataset_path = Path("datasets/chess_placeholder/data.yaml")
    dataset_path.parent.mkdir(parents=True, exist_ok=True)

    # Create minimal valid YAML
    with open(dataset_path, 'w') as f:
        f.write(f"""path: {dataset_path.parent.absolute()}
train: train/images
val: val/images

names:
  0: white_pawn
  1: white_knight
  2: white_bishop
  3: white_rook
  4: white_queen
  5: white_king
  6: black_pawn
  7: black_knight
  8: black_bishop
  9: black_rook
  10: black_queen
  11: black_king
  12: empty

nc: 13
""")

    # Create directories
    for split in ['train', 'val']:
        (dataset_path.parent / split / 'images').mkdir(parents=True, exist_ok=True)
        (dataset_path.parent / split / 'labels').mkdir(parents=True, exist_ok=True)

    print(f"[+] Placeholder created at: {dataset_path}")
    print("\n[!] NOTE: This is an empty dataset. Add images to train a real model.")
    print("[!] Or download a real dataset from the URLs above.\n")

    response = input("Continue with empty dataset for testing? (y/n): ")
    if response.lower() != 'y':
        print("\n[*] Exiting. Please download a dataset first.")
        sys.exit(0)

# Training configuration
EPOCHS = 50
IMG_SIZE = 640
BATCH_SIZE = 8
MODEL_SIZE = 'n'  # nano - fastest

print("\n" + "="*70)
print("TRAINING CONFIGURATION")
print("="*70)
print(f"Model: YOLOv8{MODEL_SIZE} (nano - fastest)")
print(f"Dataset: {dataset_path}")
print(f"Epochs: {EPOCHS}")
print(f"Image size: {IMG_SIZE}x{IMG_SIZE}")
print(f"Batch size: {BATCH_SIZE}")
print(f"Device: {device}")
print("="*70)

response = input("\nStart training? (y/n): ")
if response.lower() != 'y':
    print("\n[*] Training cancelled.")
    sys.exit(0)

# Load pre-trained YOLOv8 model
print(f"\n[*] Loading pre-trained YOLOv8{MODEL_SIZE} model...")
model_name = f'yolov8{MODEL_SIZE}.pt'
model = YOLO(model_name)

# Train
print(f"\n[*] Starting training...")
print("[*] This will take 1-2 hours on GPU, 4-6 hours on CPU")
print("[*] Press Ctrl+C to stop early\n")

try:
    results = model.train(
        data=str(dataset_path),
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH_SIZE,
        device=device,
        project='runs/chess_training',
        name='chess_detector',
        patience=20,  # Early stopping
        save=True,
        verbose=True,
        plots=True
    )

    print("\n" + "="*70)
    print("[+] TRAINING COMPLETE!")
    print("="*70)
    print(f"[+] Best model: runs/chess_training/chess_detector/weights/best.pt")
    print(f"[+] Last model: runs/chess_training/chess_detector/weights/last.pt")
    print(f"[+] Training plots: runs/chess_training/chess_detector/")
    print("="*70)

    # Test on validation set
    print("\n[*] Testing model on validation set...")
    test_results = model.val()

    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)
    print(f"mAP50: {test_results.results_dict['metrics/mAP50(B)']:.3f}")
    print(f"mAP50-95: {test_results.results_dict['metrics/mAP50-95(B)']:.3f}")
    print(f"Precision: {test_results.results_dict['metrics/precision(B)']:.3f}")
    print(f"Recall: {test_results.results_dict['metrics/recall(B)']:.3f}")
    print("="*70)

    # Export to ONNX
    print("\n[*] Exporting model to ONNX format for deployment...")
    export_path = model.export(format='onnx')
    print(f"[+] Model exported to: {export_path}")
    print("[+] Ready for deployment to Raspberry Pi!")

except KeyboardInterrupt:
    print("\n\n[!] Training interrupted by user")
    print("[*] Partial model may be saved in runs/chess_training/chess_detector/")
except Exception as e:
    print(f"\n[-] Training failed: {e}")
    import traceback
    traceback.print_exc()

print("\n[*] Done!")
