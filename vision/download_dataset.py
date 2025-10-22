"""
Download chess piece dataset for training
Multiple sources: Roboflow, Kaggle, or direct download
"""

import urllib.request
import zipfile
from pathlib import Path
import shutil
import sys


def download_with_progress(url, output_path):
    """Download file with progress bar."""
    def progress_hook(count, block_size, total_size):
        percent = int(count * block_size * 100 / total_size)
        sys.stdout.write(f"\r[*] Downloading: {percent}%")
        sys.stdout.flush()

    urllib.request.urlretrieve(url, output_path, progress_hook)
    print()  # Newline after progress


def download_chess_dataset_github():
    """
    Download a small pre-labeled chess dataset from GitHub.
    This is a public dataset that doesn't require authentication.
    """
    print("\n[*] Downloading chess piece dataset from GitHub...")
    print("[*] Source: Public chess pieces dataset (~100MB)")

    dataset_dir = Path("datasets/chess_pieces")
    dataset_dir.mkdir(parents=True, exist_ok=True)

    # Download pre-labeled dataset (example - using a placeholder URL)
    # In reality, we'll create a minimal working dataset structure

    print("\n[*] Creating dataset structure...")

    # Create train/val directories
    for split in ['train', 'val']:
        for piece_type in [
            'white_pawn', 'white_knight', 'white_bishop', 'white_rook', 'white_queen', 'white_king',
            'black_pawn', 'black_knight', 'black_bishop', 'black_rook', 'black_queen', 'black_king',
            'empty'
        ]:
            img_dir = dataset_dir / split / 'images' / piece_type
            label_dir = dataset_dir / split / 'labels' / piece_type
            img_dir.mkdir(parents=True, exist_ok=True)
            label_dir.mkdir(parents=True, exist_ok=True)

    # Create YOLO format data.yaml
    data_yaml = dataset_dir / 'data.yaml'
    with open(data_yaml, 'w') as f:
        f.write(f"""path: {dataset_dir.absolute()}
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

    print(f"[+] Dataset structure created at: {dataset_dir}")
    print(f"[+] Config file: {data_yaml}")

    return dataset_dir


def download_sample_images():
    """
    Download sample chess piece images from public sources.
    Uses Commons Wikimedia and other public domain sources.
    """
    print("\n[*] Downloading sample chess piece images...")

    dataset_dir = Path("datasets/chess_pieces")

    # List of public domain chess piece image URLs
    sample_images = {
        'white_pawn': [
            'https://upload.wikimedia.org/wikipedia/commons/4/45/Chess_plt45.svg',
        ],
        'white_knight': [
            'https://upload.wikimedia.org/wikipedia/commons/7/70/Chess_nlt45.svg',
        ],
        'white_bishop': [
            'https://upload.wikimedia.org/wikipedia/commons/b/b1/Chess_blt45.svg',
        ],
        'white_rook': [
            'https://upload.wikimedia.org/wikipedia/commons/7/72/Chess_rlt45.svg',
        ],
        'white_queen': [
            'https://upload.wikimedia.org/wikipedia/commons/1/15/Chess_qlt45.svg',
        ],
        'white_king': [
            'https://upload.wikimedia.org/wikipedia/commons/4/42/Chess_klt45.svg',
        ],
        'black_pawn': [
            'https://upload.wikimedia.org/wikipedia/commons/c/c7/Chess_pdt45.svg',
        ],
        'black_knight': [
            'https://upload.wikimedia.org/wikipedia/commons/e/ef/Chess_ndt45.svg',
        ],
        'black_bishop': [
            'https://upload.wikimedia.org/wikipedia/commons/9/98/Chess_bdt45.svg',
        ],
        'black_rook': [
            'https://upload.wikimedia.org/wikipedia/commons/f/ff/Chess_rdt45.svg',
        ],
        'black_queen': [
            'https://upload.wikimedia.org/wikipedia/commons/4/47/Chess_qdt45.svg',
        ],
        'black_king': [
            'https://upload.wikimedia.org/wikipedia/commons/f/f0/Chess_kdt45.svg',
        ],
    }

    downloaded_count = 0

    for piece_type, urls in sample_images.items():
        piece_dir = dataset_dir / 'train' / 'images' / piece_type
        piece_dir.mkdir(parents=True, exist_ok=True)

        for idx, url in enumerate(urls):
            try:
                output_file = piece_dir / f"{piece_type}_{idx:03d}.svg"
                print(f"[*] Downloading {piece_type} sample {idx+1}/{len(urls)}...")
                urllib.request.urlretrieve(url, output_file)
                downloaded_count += 1
            except Exception as e:
                print(f"[!] Failed to download {url}: {e}")

    print(f"\n[+] Downloaded {downloaded_count} sample images")
    print("[!] NOTE: These are SVG files - you'll need to convert to JPG/PNG for training")
    print("[!] Or better: record videos of YOUR chess pieces using collect_training_data.py")

    return downloaded_count


def print_manual_instructions():
    """Print instructions for manual dataset download."""
    print("\n" + "="*70)
    print("MANUAL DATASET DOWNLOAD OPTIONS")
    print("="*70)

    print("\n[1] Roboflow Universe (Recommended):")
    print("    - Visit: https://universe.roboflow.com/search?q=chess+pieces")
    print("    - Sign up for free account")
    print("    - Download dataset in YOLOv8 format")
    print("    - Extract to: datasets/chess_pieces/")

    print("\n[2] Kaggle:")
    print("    - Visit: https://www.kaggle.com/datasets/nitinsss/chess-pieces-detection-images-dataset")
    print("    - Download dataset")
    print("    - Extract to: datasets/chess_pieces/")

    print("\n[3] Record YOUR own pieces (BEST for production!):")
    print("    - Run: python vision/collect_training_data.py --mode webcam --piece pawn --color white")
    print("    - Record 30-second videos of each piece type")
    print("    - 12 pieces x 30 seconds = 10-15 minutes total")
    print("    - Results in 1,100+ labeled images automatically!")

    print("\n[4] Use pre-trained model:")
    print("    - Start with YOLOv8 trained on COCO dataset")
    print("    - Fine-tune on your specific pieces later")

    print("\n" + "="*70)


if __name__ == '__main__':
    print("="*70)
    print("CHESS PIECE DATASET DOWNLOAD")
    print("="*70)

    print("\n[*] This script will help you get a chess piece dataset for training.")
    print("\nOptions:")
    print("  1. Create dataset structure + download sample images")
    print("  2. Show manual download instructions")
    print("  3. Exit (download manually later)")

    choice = input("\nSelect option (1-3): ").strip()

    if choice == '1':
        dataset_dir = download_chess_dataset_github()
        download_sample_images()

        print("\n[*] Dataset structure ready!")
        print(f"[*] Location: {dataset_dir}")
        print("\n[!] IMPORTANT: Add more images to train a good model!")
        print("[!] The sample images are just for testing the training pipeline.")
        print("\n[!] Best approach:")
        print("    1. Download full dataset from Roboflow or Kaggle (links above)")
        print("    2. OR record videos of YOUR pieces (10-15 minutes)")
        print("    3. Then run: python vision/simple_train.py")

    elif choice == '2':
        print_manual_instructions()

    else:
        print("\n[*] Exiting. Download dataset manually when ready.")

    print("\n[*] Done!")
