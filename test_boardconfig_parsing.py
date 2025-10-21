"""
Test that BoardConfig is correctly parsed from settings with storage_layout field.
"""

from logic.profiles import Settings
from logic.board_map import BoardConfig, PlayArea, StorageLayout

def cfg_to_board(d: dict) -> BoardConfig:
    """
    Convert dictionary from YAML to BoardConfig object.
    This is the same logic as in board_window.py
    """
    # Parse play_area if present
    play_area = None
    if 'play_area' in d:
        pa = d['play_area']
        play_area = PlayArea(
            min_file=int(pa.get('min_file', 0)),
            max_file=int(pa.get('max_file', 7)),
            min_rank=int(pa.get('min_rank', 0)),
            max_rank=int(pa.get('max_rank', 7))
        )

    # Parse storage_layout if present
    storage_layout = StorageLayout.NONE
    if 'storage_layout' in d:
        layout_str = d['storage_layout'].lower()
        storage_layout = StorageLayout(layout_str)

    return BoardConfig(
        files=int(d.get('files', 8)),
        ranks=int(d.get('ranks', 8)),
        width_mm=float(d.get('width_mm', 400.0)),
        height_mm=float(d.get('height_mm', 400.0)),
        origin_x_mm=float(d.get('origin_x_mm', 0.0)),
        origin_y_mm=float(d.get('origin_y_mm', 0.0)),
        play_area=play_area,
        storage_layout=storage_layout
    )

# Load settings
settings = Settings()

print("=" * 70)
print("BOARDCONFIG PARSING TEST")
print("=" * 70)

# Test all profiles
for name in settings.get_profile_names():
    profile = settings.get_profile_by_name(name)
    board_dict = profile['board']

    print(f"\n{'=' * 70}")
    print(f"Profile: {name}")
    print('=' * 70)

    # Parse to BoardConfig
    board_cfg = cfg_to_board(board_dict)

    print(f"\nBoardConfig Object:")
    print(f"  Files: {board_cfg.files}")
    print(f"  Ranks: {board_cfg.ranks}")
    print(f"  Size: {board_cfg.width_mm}mm x {board_cfg.height_mm}mm")
    print(f"  Origin: ({board_cfg.origin_x_mm}, {board_cfg.origin_y_mm})")
    print(f"  Storage Layout: {board_cfg.storage_layout.name} (value: '{board_cfg.storage_layout.value}')")

    if board_cfg.play_area:
        print(f"\n  Play Area:")
        print(f"    Files: {board_cfg.play_area.min_file} to {board_cfg.play_area.max_file}")
        print(f"    Ranks: {board_cfg.play_area.min_rank} to {board_cfg.play_area.max_rank}")
    else:
        print(f"\n  Play Area: None (entire board is playing area)")

    # Test helper methods
    print(f"\n  Helper Methods:")
    print(f"    Home Square: {board_cfg.get_home_square()}")
    print(f"    Playing Area Offset: {board_cfg.get_playing_area_offset()}")
    print(f"    Square Size: {board_cfg.square_size_x():.2f}mm x {board_cfg.square_size_y():.2f}mm")

    # Test a few squares to see if is_playing_square works correctly
    print(f"\n  Square Classification Tests:")
    test_squares = [
        (0, 0, "a1"),  # Bottom-left
        (3, 3, "d4"),  # Center of 8x8
        (7, 7, "h8"),  # Top-right of 8x8
        (0, 8, "a9"),  # Rank 9 (storage in TOP layout)
        (0, 9, "a10"), # Rank 10 (storage in TOP layout)
        (0, 0, "a1"),  # Perimeter corner (storage in PERIMETER layout)
        (9, 9, "j10"), # Perimeter top-right
    ]

    for file_idx, rank_idx, notation in test_squares:
        if file_idx < board_cfg.files and rank_idx < board_cfg.ranks:
            is_playing = board_cfg.is_playing_square(file_idx, rank_idx)
            status = "PLAYING" if is_playing else "STORAGE"
            print(f"    {notation} ({file_idx}, {rank_idx}): {status}")

print(f"\n{'=' * 70}")
print("TEST COMPLETE")
print('=' * 70)
