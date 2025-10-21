"""
Convert SVG piece images to PNG at multiple sizes for performance.
This script uses cairosvg if available, otherwise falls back to other methods.
"""

import os
from PIL import Image

# Try importing various SVG libraries
svg_method = None

try:
    import cairosvg
    svg_method = 'cairosvg'
    print("Using cairosvg")
except:
    pass

if not svg_method:
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM
        svg_method = 'svglib'
        print("Using svglib")
    except:
        pass

if not svg_method:
    print("ERROR: No SVG library available!")
    print("Please install one of: cairosvg (with GTK), svglib+reportlab")
    exit(1)

# Sizes to generate (pixels)
SIZES = [40, 60, 80, 100, 120]

# Piece codes
PIECES = ['wK', 'wQ', 'wR', 'wB', 'wN', 'wP', 'bK', 'bQ', 'bR', 'bB', 'bN', 'bP']

# Directories
SVG_DIR = 'assets/pieces'
PNG_DIR = 'assets/pieces/png'

# Create PNG directory
os.makedirs(PNG_DIR, exist_ok=True)

def convert_svg(svg_path, png_path, size):
    """Convert SVG to PNG at specified size."""
    if svg_method == 'cairosvg':
        import cairosvg
        cairosvg.svg2png(url=svg_path, write_to=png_path,
                        output_width=size, output_height=size)
    elif svg_method == 'svglib':
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM
        drawing = svg2rlg(svg_path)
        # Scale drawing
        scale = size / max(drawing.width, drawing.height)
        drawing.width = size
        drawing.height = size
        drawing.scale(scale, scale)
        # Render and save
        renderPM.drawToFile(drawing, png_path, fmt='PNG')

# Convert all pieces at all sizes
for piece in PIECES:
    svg_file = os.path.join(SVG_DIR, f'{piece}.svg')
    if not os.path.exists(svg_file):
        print(f"Missing: {svg_file}")
        continue

    for size in SIZES:
        png_file = os.path.join(PNG_DIR, f'{piece}_{size}.png')
        try:
            convert_svg(svg_file, png_file, size)
            print(f"✓ Created {png_file}")
        except Exception as e:
            print(f"✗ Failed {png_file}: {e}")

print("\nConversion complete!")
