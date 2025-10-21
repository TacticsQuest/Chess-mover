"""
Test script to verify storage layout configuration is loaded correctly.
"""

from logic.profiles import Settings
from logic.board_map import StorageLayout

# Load settings
settings = Settings()

print("=" * 60)
print("STORAGE LAYOUT CONFIGURATION TEST")
print("=" * 60)
print()

# Get active profile name
active_name = settings.get_active_profile_name()
print(f"Active Profile: {active_name}")
print()

# Load the active profile
profile = settings.get_profile_by_name(active_name)

if profile:
    board_config = profile['board']

    print("Board Configuration:")
    print(f"  Files: {board_config.get('files', 8)}")
    print(f"  Ranks: {board_config.get('ranks', 8)}")
    print(f"  Size: {board_config.get('width_mm', 400)}mm × {board_config.get('height_mm', 400)}mm")
    print()

    # Check for storage_layout field
    if 'storage_layout' in board_config:
        layout_str = board_config['storage_layout']
        print(f"Storage Layout (raw): '{layout_str}'")

        # Try to convert to enum
        try:
            layout_enum = StorageLayout(layout_str)
            print(f"Storage Layout (enum): {layout_enum}")
            print(f"  - Enum name: {layout_enum.name}")
            print(f"  - Enum value: {layout_enum.value}")
        except ValueError as e:
            print(f"ERROR: Could not convert to StorageLayout enum: {e}")
    else:
        print("Storage Layout: NOT FOUND (defaults to NONE)")
        print(f"  - Default: {StorageLayout.NONE}")

    print()

    # Check for play_area field
    if 'play_area' in board_config:
        play_area = board_config['play_area']
        print("Play Area:")
        print(f"  Files: {play_area.get('min_file', 0)} to {play_area.get('max_file', 7)}")
        print(f"  Ranks: {play_area.get('min_rank', 0)} to {play_area.get('max_rank', 7)}")
    else:
        print("Play Area: NOT FOUND (entire board is playing area)")

    print()

# Test all profiles
print("=" * 60)
print("ALL PROFILES:")
print("=" * 60)

for name in settings.get_profile_names():
    profile = settings.get_profile_by_name(name)
    board = profile['board']

    layout_str = board.get('storage_layout', 'none')
    files = board.get('files', 8)
    ranks = board.get('ranks', 8)

    active_marker = " (ACTIVE)" if name == active_name else ""

    print(f"\n{name}{active_marker}")
    print(f"  Grid: {files}×{ranks}")
    print(f"  Storage: {layout_str}")

    if 'play_area' in board:
        pa = board['play_area']
        print(f"  Play Area: Files {pa.get('min_file')}-{pa.get('max_file')}, Ranks {pa.get('min_rank')}-{pa.get('max_rank')}")

print()
print("=" * 60)
print("TEST COMPLETE")
print("=" * 60)
