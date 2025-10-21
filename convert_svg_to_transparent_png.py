"""
Convert SVG chess piece images to transparent PNG at 128x128.
Uses Wand (ImageMagick) for high-quality SVG rasterization with alpha channel.
"""

import os
from pathlib import Path

try:
    from wand.image import Image as WandImage
except ImportError:
    print("ERROR: Wand library not installed!")
    print("Install with: pip install wand")
    exit(1)

# Configuration
SVG_DIR = Path("assets/pieces")
PNG_DIR = Path("assets/pieces/png")
SIZE = 128  # High-DPI size for crisp rendering
PIECES = ['wK', 'wQ', 'wR', 'wB', 'wN', 'wP', 'bK', 'bQ', 'bR', 'bB', 'bN', 'bP']

# Create PNG directory
PNG_DIR.mkdir(parents=True, exist_ok=True)

print(f"Converting SVG pieces to {SIZE}x{SIZE} PNG with transparency...")
print(f"Source: {SVG_DIR}")
print(f"Output: {PNG_DIR}\n")

success_count = 0
failed_count = 0

for piece in PIECES:
    svg_file = SVG_DIR / f"{piece}.svg"
    png_file = PNG_DIR / f"{piece}.png"

    if not svg_file.exists():
        print(f"[MISSING] {svg_file}")
        failed_count += 1
        continue

    try:
        # Load SVG with Wand/ImageMagick
        with WandImage(filename=str(svg_file), width=SIZE, height=SIZE) as img:
            # Ensure transparent background (RGBA mode)
            img.background_color = 'transparent'
            img.format = 'png'

            # Save as PNG with alpha channel
            img.save(filename=str(png_file))

        # Verify file was created
        if png_file.exists():
            file_size = png_file.stat().st_size
            print(f"[OK] {piece}.png ({file_size:,} bytes)")
            success_count += 1
        else:
            print(f"[FAIL] Failed to create {png_file}")
            failed_count += 1

    except Exception as e:
        print(f"[ERROR] Error converting {piece}: {e}")
        failed_count += 1

print(f"\n{'='*50}")
print(f"Conversion complete!")
print(f"  Success: {success_count}")
print(f"  Failed:  {failed_count}")
print(f"{'='*50}")

if success_count > 0:
    print(f"\n[OK] PNG files saved to: {PNG_DIR.absolute()}")
