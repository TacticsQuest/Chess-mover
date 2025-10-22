"""
Chess Piece Detection Model Training

Trains YOLOv8 model on chess piece datasets for the Chess Mover Machine.
Supports both online datasets and custom datasets.
"""

import argparse
from pathlib import Path
import yaml
import sys


def download_roboflow_dataset(api_key: str = None):
    """
    Download chess piece dataset from Roboflow.

    Args:
        api_key: Roboflow API key (optional, can use public datasets)

    Returns:
        Path to downloaded dataset
    """
    try:
        from roboflow import Roboflow

        print("\n Downloading chess dataset from Roboflow...")
        print("   Using public chess pieces dataset...\n")

        # Use public dataset (no API key required for some datasets)
        # If this fails, we'll use a different approach
        try:
            rf = Roboflow(api_key=api_key or "placeholder")
            project = rf.workspace("roboflow-jvuqo").project("chess-pieces-new")
            dataset = project.version(23).download("yolov8")

            print(f" Dataset downloaded to: {dataset.location}")
            return Path(dataset.location)

        except Exception as e:
            print(f"️  Roboflow download failed: {e}")
            print("   Trying alternative dataset source...")

            # Alternative: Try a different public dataset
            rf = Roboflow(api_key="public")
            project = rf.workspace("joseph-nelson").project("chess-pieces-new")
            dataset = project.version(23).download("yolov8")

            print(f" Dataset downloaded to: {dataset.location}")
            return Path(dataset.location)

    except ImportError:
        print(" Roboflow library not installed. Install with: pip install roboflow")
        return None
    except Exception as e:
        print(f" Error downloading dataset: {e}")
        print("\n Alternative: You can manually download from:")
        print("   https://universe.roboflow.com/roboflow-jvuqo/chess-pieces-new/dataset/23")
        return None


def create_sample_dataset():
    """
    Create a small sample dataset for testing (if download fails).
    This is a fallback option.
    """
    print("\n Creating sample dataset for testing...")

    dataset_dir = Path("datasets/sample_chess")
    dataset_dir.mkdir(parents=True, exist_ok=True)

    # Create directory structure
    for split in ['train', 'val']:
        (dataset_dir / split / 'images').mkdir(parents=True, exist_ok=True)
        (dataset_dir / split / 'labels').mkdir(parents=True, exist_ok=True)

    # Create config
    config = {
        'path': str(dataset_dir.absolute()),
        'train': 'train/images',
        'val': 'val/images',
        'names': {
            0: 'white_pawn',
            1: 'white_knight',
            2: 'white_bishop',
            3: 'white_rook',
            4: 'white_queen',
            5: 'white_king',
            6: 'black_pawn',
            7: 'black_knight',
            8: 'black_bishop',
            9: 'black_rook',
            10: 'black_queen',
            11: 'black_king',
            12: 'empty'
        },
        'nc': 13
    }

    config_path = dataset_dir / 'data.yaml'
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    print(f" Sample dataset created at: {dataset_dir}")
    print("️  Note: This is an empty dataset structure.")
    print("   Please add images or download a real dataset to train.\n")

    return dataset_dir


def train_model(data_yaml: Path, epochs: int = 100, img_size: int = 640, batch_size: int = 16, model_size: str = 'n'):
    """
    Train YOLOv8 model on chess piece dataset.

    Args:
        data_yaml: Path to dataset configuration YAML
        epochs: Number of training epochs
        img_size: Image size for training
        batch_size: Training batch size
        model_size: YOLOv8 model size ('n', 's', 'm', 'l', 'x')
    """
    try:
        from ultralytics import YOLO
        import torch

        print("\n Starting YOLOv8 training...")
        print(f"   Model: YOLOv8{model_size}")
        print(f"   Dataset: {data_yaml}")
        print(f"   Epochs: {epochs}")
        print(f"   Image size: {img_size}")
        print(f"   Batch size: {batch_size}")

        # Check for GPU
        if torch.cuda.is_available():
            device = 'cuda'
            gpu_name = torch.cuda.get_device_name(0)
            print(f"   Device: GPU ({gpu_name})")
        else:
            device = 'cpu'
            print(f"   Device: CPU (training will be slower)")

        print("\n" + "="*60)

        # Load pre-trained YOLOv8 model
        model_name = f'yolov8{model_size}.pt'
        print(f"\n Loading pre-trained {model_name}...")
        model = YOLO(model_name)

        # Train the model
        print(f"\n Training started...\n")
        results = model.train(
            data=str(data_yaml),
            epochs=epochs,
            imgsz=img_size,
            batch=batch_size,
            device=device,
            project='runs/chess_training',
            name='chess_detector',
            patience=20,  # Early stopping patience
            save=True,
            verbose=True,
            plots=True
        )

        print("\n" + "="*60)
        print(" Training complete!")
        print(f"   Best model saved to: runs/chess_training/chess_detector/weights/best.pt")
        print(f"   Last model saved to: runs/chess_training/chess_detector/weights/last.pt")

        return results

    except ImportError as e:
        print(f" Error: Missing library - {e}")
        print("   Install with: pip install ultralytics torch")
        return None
    except Exception as e:
        print(f" Training failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_model(model_path: Path, data_yaml: Path):
    """
    Test trained model on validation set.

    Args:
        model_path: Path to trained model weights
        data_yaml: Path to dataset configuration
    """
    try:
        from ultralytics import YOLO

        print(f"\n Testing model: {model_path}")
        print(f"   Dataset: {data_yaml}\n")

        # Load model
        model = YOLO(str(model_path))

        # Validate on test set
        results = model.val(data=str(data_yaml))

        print("\n" + "="*60)
        print(" Test Results:")
        print(f"   mAP50: {results.results_dict['metrics/mAP50(B)']:.3f}")
        print(f"   mAP50-95: {results.results_dict['metrics/mAP50-95(B)']:.3f}")
        print(f"   Precision: {results.results_dict['metrics/precision(B)']:.3f}")
        print(f"   Recall: {results.results_dict['metrics/recall(B)']:.3f}")
        print("="*60 + "\n")

        return results

    except Exception as e:
        print(f" Testing failed: {e}")
        return None


def export_model(model_path: Path, format: str = 'onnx'):
    """
    Export trained model to different formats.

    Args:
        model_path: Path to trained model weights
        format: Export format ('onnx', 'torchscript', 'tflite', etc.)
    """
    try:
        from ultralytics import YOLO

        print(f"\n Exporting model to {format.upper()} format...")

        model = YOLO(str(model_path))
        export_path = model.export(format=format)

        print(f" Model exported to: {export_path}")
        print(f"   Ready for deployment to Raspberry Pi!\n")

        return export_path

    except Exception as e:
        print(f" Export failed: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Train chess piece detection model')
    parser.add_argument('--download', action='store_true', help='Download dataset from Roboflow')
    parser.add_argument('--api-key', type=str, help='Roboflow API key (optional)')
    parser.add_argument('--data', type=str, help='Path to dataset YAML file')
    parser.add_argument('--epochs', type=int, default=100, help='Number of training epochs')
    parser.add_argument('--img-size', type=int, default=640, help='Image size')
    parser.add_argument('--batch-size', type=int, default=16, help='Batch size')
    parser.add_argument('--model-size', type=str, default='n', choices=['n', 's', 'm', 'l', 'x'],
                        help='YOLOv8 model size (n=nano, s=small, m=medium, l=large, x=xlarge)')
    parser.add_argument('--test', action='store_true', help='Test trained model')
    parser.add_argument('--model', type=str, help='Path to model weights for testing/export')
    parser.add_argument('--export', type=str, choices=['onnx', 'torchscript', 'tflite'],
                        help='Export model to format')

    args = parser.parse_args()

    # Download dataset if requested
    if args.download:
        dataset_dir = download_roboflow_dataset(args.api_key)
        if dataset_dir:
            data_yaml = dataset_dir / 'data.yaml'
            print(f"\n Dataset ready at: {data_yaml}")

            # Ask if user wants to train immediately
            response = input("\n Start training now? (y/n): ")
            if response.lower() == 'y':
                train_model(data_yaml, args.epochs, args.img_size, args.batch_size, args.model_size)
        else:
            print("\n️  Dataset download failed. Creating sample structure...")
            dataset_dir = create_sample_dataset()
        return

    # Test model if requested
    if args.test:
        if not args.model:
            print(" Error: --model required for testing")
            return
        if not args.data:
            print(" Error: --data required for testing")
            return

        test_model(Path(args.model), Path(args.data))
        return

    # Export model if requested
    if args.export:
        if not args.model:
            print(" Error: --model required for export")
            return

        export_model(Path(args.model), args.export)
        return

    # Train model
    if args.data:
        data_yaml = Path(args.data)
        if not data_yaml.exists():
            print(f" Error: Dataset YAML not found: {data_yaml}")
            return

        train_model(data_yaml, args.epochs, args.img_size, args.batch_size, args.model_size)
    else:
        print(" Error: Please specify --data or use --download")
        print("\nUsage examples:")
        print("  1. Download dataset and train:")
        print("     python vision/train_model.py --download")
        print("\n  2. Train on existing dataset:")
        print("     python vision/train_model.py --data datasets/my_chess/data.yaml")
        print("\n  3. Test trained model:")
        print("     python vision/train_model.py --test --model runs/chess_training/chess_detector/weights/best.pt --data datasets/my_chess/data.yaml")
        print("\n  4. Export to ONNX:")
        print("     python vision/train_model.py --export onnx --model runs/chess_training/chess_detector/weights/best.pt")


if __name__ == '__main__':
    main()
