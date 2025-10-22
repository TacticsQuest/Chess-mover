"""
Data Collection Script for Chess Vision Training

Supports both video-based and manual image collection methods.
Video collection is recommended for faster dataset creation.
"""

import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import argparse


class ChessDataCollector:
    """Collect training images for chess piece detection."""

    def __init__(self, output_dir: str = "datasets/chess"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def collect_from_video(
        self,
        video_path: str,
        piece_type: str,
        color: str,
        frame_interval: int = 10,
        max_images: int = 200
    ):
        """
        Extract training images from video file.

        This is MUCH easier than taking individual photos!

        Instructions:
        1. Record 30-60 second video of each piece
        2. Rotate piece slowly while recording
        3. Move piece to different squares (light and dark)
        4. Vary lighting slightly if possible
        5. This script extracts frames automatically

        Args:
            video_path: Path to video file (MP4, AVI, MOV, etc.)
            piece_type: 'pawn', 'knight', 'bishop', 'rook', 'queen', 'king', 'empty'
            color: 'white' or 'black' (or None for empty squares)
            frame_interval: Extract every Nth frame (10 = ~3 images/second at 30fps)
            max_images: Maximum images to extract
        """
        piece_dir = self._get_piece_directory(piece_type, color)
        piece_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n📹 Extracting frames from video: {video_path}")
        print(f"   Piece: {color} {piece_type}" if color else f"   Type: {piece_type}")
        print(f"   Frame interval: {frame_interval} (every {frame_interval} frames)")
        print(f"   Max images: {max_images}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Error: Could not open video file: {video_path}")
            return

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0

        print(f"   Video: {total_frames} frames, {fps:.1f} FPS, {duration:.1f}s duration")
        print(f"   Expected images: ~{min(total_frames // frame_interval, max_images)}\n")

        frame_count = 0
        saved_count = 0

        while saved_count < max_images:
            ret, frame = cap.read()
            if not ret:
                break

            # Extract every Nth frame
            if frame_count % frame_interval == 0:
                filename = f"{piece_type}_{saved_count:04d}_{datetime.now():%Y%m%d_%H%M%S}.jpg"
                filepath = piece_dir / filename
                cv2.imwrite(str(filepath), frame)
                saved_count += 1

                if saved_count % 10 == 0:
                    print(f"   ✓ Extracted {saved_count}/{max_images} images...")

            frame_count += 1

        cap.release()

        print(f"\n✅ Extracted {saved_count} images from video")
        print(f"   Saved to: {piece_dir}\n")

    def collect_from_webcam_video(
        self,
        piece_type: str,
        color: str,
        duration_seconds: int = 30,
        frame_interval: int = 10
    ):
        """
        Record live video from webcam and extract frames.

        Even easier than recording separately!

        Instructions:
        1. Press SPACE to start recording
        2. Rotate piece slowly for 30 seconds
        3. Move to different squares (light/dark)
        4. Recording stops automatically
        5. Frames are extracted automatically

        Args:
            piece_type: 'pawn', 'knight', 'bishop', 'rook', 'queen', 'king', 'empty'
            color: 'white' or 'black' (or None for empty)
            duration_seconds: How long to record
            frame_interval: Extract every Nth frame
        """
        piece_dir = self._get_piece_directory(piece_type, color)
        piece_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n🎥 Live video collection mode")
        print(f"   Piece: {color} {piece_type}" if color else f"   Type: {piece_type}")
        print(f"   Duration: {duration_seconds} seconds")
        print(f"   Expected images: ~{duration_seconds * 30 // frame_interval}")
        print(f"\n   Instructions:")
        print(f"   1. Position piece on board")
        print(f"   2. Press SPACE to start recording")
        print(f"   3. Slowly rotate and move piece")
        print(f"   4. Recording stops automatically\n")

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Error: Could not open webcam")
            return

        # Wait for user to press SPACE
        recording = False
        start_time = None
        frame_count = 0
        saved_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Display frame with instructions
            display_frame = frame.copy()
            if not recording:
                cv2.putText(
                    display_frame,
                    "Press SPACE to start recording",
                    (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )
            else:
                elapsed = (datetime.now().timestamp() - start_time)
                remaining = max(0, duration_seconds - elapsed)
                cv2.putText(
                    display_frame,
                    f"Recording... {remaining:.1f}s remaining",
                    (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2
                )
                cv2.putText(
                    display_frame,
                    f"Images: {saved_count}",
                    (50, 100),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )

            cv2.imshow('Video Collection', display_frame)
            key = cv2.waitKey(1)

            if key == ord(' ') and not recording:
                # Start recording
                recording = True
                start_time = datetime.now().timestamp()
                print("🔴 Recording started...")

            elif recording:
                # Save frames at interval
                if frame_count % frame_interval == 0:
                    filename = f"{piece_type}_{saved_count:04d}_{datetime.now():%Y%m%d_%H%M%S}.jpg"
                    filepath = piece_dir / filename
                    cv2.imwrite(str(filepath), frame)
                    saved_count += 1

                frame_count += 1

                # Stop after duration
                if (datetime.now().timestamp() - start_time) >= duration_seconds:
                    break

            elif key == 27:  # ESC to cancel
                break

        cap.release()
        cv2.destroyAllWindows()

        print(f"\n✅ Collected {saved_count} images")
        print(f"   Saved to: {piece_dir}\n")

    def collect_manual(
        self,
        piece_type: str,
        color: str,
        num_images: int = 100
    ):
        """
        Manual image collection (original method).

        Use this if you prefer more control over each image.

        Args:
            piece_type: 'pawn', 'knight', 'bishop', 'rook', 'queen', 'king', 'empty'
            color: 'white' or 'black' (or None for empty)
            num_images: Number of images to collect
        """
        piece_dir = self._get_piece_directory(piece_type, color)
        piece_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n📸 Manual collection mode")
        print(f"   Piece: {color} {piece_type}" if color else f"   Type: {piece_type}")
        print(f"   Target: {num_images} images")
        print(f"\n   Instructions:")
        print(f"   - Place piece on different squares")
        print(f"   - Rotate slightly between captures")
        print(f"   - Press SPACE to capture")
        print(f"   - Press ESC to finish\n")

        cap = cv2.VideoCapture(0)
        count = 0

        while count < num_images:
            ret, frame = cap.read()
            if not ret:
                break

            # Display with counter
            display_frame = frame.copy()
            cv2.putText(
                display_frame,
                f"Images: {count}/{num_images} (SPACE=capture, ESC=done)",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.imshow('Manual Collection', display_frame)
            key = cv2.waitKey(1)

            if key == ord(' '):  # Space to capture
                filename = f"{piece_type}_{count:04d}_{datetime.now():%Y%m%d_%H%M%S}.jpg"
                cv2.imwrite(str(piece_dir / filename), frame)
                count += 1
                print(f"   ✓ Captured {count}/{num_images}")

            elif key == 27:  # ESC to exit
                break

        cap.release()
        cv2.destroyAllWindows()

        print(f"\n✅ Collected {count} images")
        print(f"   Saved to: {piece_dir}\n")

    def _get_piece_directory(self, piece_type: str, color: Optional[str]) -> Path:
        """Get output directory for piece type."""
        if color:
            return self.output_dir / "pieces" / f"{color}_{piece_type}"
        else:
            return self.output_dir / "pieces" / piece_type

    def organize_for_training(self, train_split: float = 0.8):
        """
        Organize collected images into train/val split.

        This prepares the dataset for model training.

        Args:
            train_split: Fraction of images for training (rest for validation)
        """
        print(f"\n📁 Organizing dataset for training...")
        print(f"   Train/val split: {train_split:.0%} / {1-train_split:.0%}\n")

        pieces_dir = self.output_dir / "pieces"
        if not pieces_dir.exists():
            print("❌ No pieces directory found")
            return

        # Create train/val directories
        train_dir = self.output_dir / "train"
        val_dir = self.output_dir / "val"
        train_dir.mkdir(exist_ok=True)
        val_dir.mkdir(exist_ok=True)

        # Process each piece type
        for piece_subdir in pieces_dir.iterdir():
            if not piece_subdir.is_dir():
                continue

            piece_name = piece_subdir.name
            print(f"   Processing: {piece_name}")

            # Get all images
            images = list(piece_subdir.glob("*.jpg"))
            np.random.shuffle(images)

            # Split
            split_idx = int(len(images) * train_split)
            train_images = images[:split_idx]
            val_images = images[split_idx:]

            # Copy to train/val directories
            train_piece_dir = train_dir / piece_name
            val_piece_dir = val_dir / piece_name
            train_piece_dir.mkdir(exist_ok=True)
            val_piece_dir.mkdir(exist_ok=True)

            for img in train_images:
                import shutil
                shutil.copy(img, train_piece_dir / img.name)

            for img in val_images:
                import shutil
                shutil.copy(img, val_piece_dir / img.name)

            print(f"      ✓ Train: {len(train_images)}, Val: {len(val_images)}")

        print(f"\n✅ Dataset organized!")
        print(f"   Train: {train_dir}")
        print(f"   Val: {val_dir}\n")

    def create_dataset_config(self):
        """Create YAML config file for training."""
        config_content = f"""# Chess Piece Dataset Configuration
# Generated by collect_training_data.py

path: {self.output_dir.absolute()}
train: train
val: val

# Classes
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

nc: 13  # number of classes
"""

        config_path = self.output_dir / "config.yaml"
        config_path.write_text(config_content)

        print(f"✅ Created dataset config: {config_path}")


def main():
    parser = argparse.ArgumentParser(description="Collect chess training data")
    parser.add_argument(
        '--mode',
        choices=['video', 'webcam', 'manual'],
        default='webcam',
        help='Collection mode (default: webcam)'
    )
    parser.add_argument(
        '--video',
        type=str,
        help='Path to video file (for video mode)'
    )
    parser.add_argument(
        '--piece',
        type=str,
        required=True,
        choices=['pawn', 'knight', 'bishop', 'rook', 'queen', 'king', 'empty'],
        help='Piece type to collect'
    )
    parser.add_argument(
        '--color',
        type=str,
        choices=['white', 'black'],
        help='Piece color (not needed for empty)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='datasets/my_chess_set',
        help='Output directory'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=30,
        help='Video duration in seconds (webcam mode)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=10,
        help='Frame extraction interval'
    )
    parser.add_argument(
        '--max-images',
        type=int,
        default=200,
        help='Maximum images to extract'
    )
    parser.add_argument(
        '--organize',
        action='store_true',
        help='Organize collected images into train/val split'
    )

    args = parser.parse_args()

    collector = ChessDataCollector(args.output)

    if args.organize:
        collector.organize_for_training()
        collector.create_dataset_config()
        return

    if args.mode == 'video':
        if not args.video:
            print("❌ Error: --video required for video mode")
            return
        collector.collect_from_video(
            args.video,
            args.piece,
            args.color,
            frame_interval=args.interval,
            max_images=args.max_images
        )

    elif args.mode == 'webcam':
        collector.collect_from_webcam_video(
            args.piece,
            args.color,
            duration_seconds=args.duration,
            frame_interval=args.interval
        )

    elif args.mode == 'manual':
        collector.collect_manual(
            args.piece,
            args.color,
            num_images=args.max_images
        )


if __name__ == '__main__':
    main()
