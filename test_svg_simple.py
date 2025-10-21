"""Quick test to see if we can render SVG with cairo."""
import cairo
import os

svg_file = 'assets/pieces/wK.svg'

if os.path.exists(svg_file):
    print(f"✓ Found {svg_file}")

    # Try to render with cairo
    try:
        # Read SVG content
        with open(svg_file, 'r') as f:
            svg_data = f.read()

        print(f"✓ Read SVG ({len(svg_data)} bytes)")
        print("✗ Cairo doesn't have built-in SVG support without librsvg")

    except Exception as e:
        print(f"✗ Error: {e}")
else:
    print(f"✗ File not found: {svg_file}")
