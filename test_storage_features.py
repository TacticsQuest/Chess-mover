"""
Comprehensive test for storage layout features.
Run this to verify all storage layout functionality works correctly.
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from logic.profiles import Settings
from logic.board_map import BoardConfig, PlayArea, StorageLayout
from logic.board_state import BoardState, Piece, PieceType, PieceColor

print("=" * 70)
print("  STORAGE LAYOUT FEATURE TESTS")
print("=" * 70)

test_count = 0
pass_count = 0

def test(name, condition, details=""):
    """Helper to track test results."""
    global test_count, pass_count
    test_count += 1
    if condition:
        pass_count += 1
        print(f"[PASS] {name}")
        if details:
            print(f"       {details}")
    else:
        print(f"[FAIL] {name}")
        if details:
            print(f"       {details}")

# Load settings
settings = Settings()

# ============================================================================
print("\n" + "=" * 70)
print("TEST 1: Profile Configuration")
print("=" * 70)

# Test each profile exists
for profile_name in ["Standard Chess 400mm", "Board with Top Storage", "Board with Perimeter Storage"]:
    profile = settings.get_profile_by_name(profile_name)
    test(f"Profile '{profile_name}' exists", profile is not None)

# Test active profile
active = settings.get_active_profile_name()
test("Active profile is set", active is not None, f"Active: {active}")
test("Active profile is Perimeter Storage", active == "Board with Perimeter Storage")

# ============================================================================
print("\n" + "=" * 70)
print("TEST 2: Storage Layout Configurations")
print("=" * 70)

# Parse function (same as board_window.py)
def parse_board_config(d: dict) -> BoardConfig:
    play_area = None
    if 'play_area' in d:
        pa = d['play_area']
        play_area = PlayArea(
            min_file=int(pa.get('min_file', 0)),
            max_file=int(pa.get('max_file', 7)),
            min_rank=int(pa.get('min_rank', 0)),
            max_rank=int(pa.get('max_rank', 7))
        )

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

# Test Standard Board
profile = settings.get_profile_by_name("Standard Chess 400mm")
cfg = parse_board_config(profile['board'])
test("Standard - Grid is 8×8", cfg.files == 8 and cfg.ranks == 8)
test("Standard - Layout is NONE", cfg.storage_layout == StorageLayout.NONE)
test("Standard - No play_area defined", cfg.play_area is None)

# Test Top Storage
profile = settings.get_profile_by_name("Board with Top Storage")
cfg = parse_board_config(profile['board'])
test("Top Storage - Grid is 8×10", cfg.files == 8 and cfg.ranks == 10)
test("Top Storage - Layout is TOP", cfg.storage_layout == StorageLayout.TOP)
test("Top Storage - Play area is ranks 0-7",
     cfg.play_area and cfg.play_area.min_rank == 0 and cfg.play_area.max_rank == 7)

# Test Perimeter Storage
profile = settings.get_profile_by_name("Board with Perimeter Storage")
cfg = parse_board_config(profile['board'])
test("Perimeter - Grid is 10×10", cfg.files == 10 and cfg.ranks == 10)
test("Perimeter - Layout is PERIMETER", cfg.storage_layout == StorageLayout.PERIMETER)
test("Perimeter - Play area is center 8×8",
     cfg.play_area and
     cfg.play_area.min_file == 1 and cfg.play_area.max_file == 8 and
     cfg.play_area.min_rank == 1 and cfg.play_area.max_rank == 8)

# ============================================================================
print("\n" + "=" * 70)
print("TEST 3: Square Classification")
print("=" * 70)

# Standard Board - all playing
profile = settings.get_profile_by_name("Standard Chess 400mm")
cfg = parse_board_config(profile['board'])

a1_playing = cfg.is_playing_square(0, 0)
h8_playing = cfg.is_playing_square(7, 7)
test("Standard - a1 is playing", a1_playing)
test("Standard - h8 is playing", h8_playing)

# Top Storage
profile = settings.get_profile_by_name("Board with Top Storage")
cfg = parse_board_config(profile['board'])

a1_playing = cfg.is_playing_square(0, 0)
h8_playing = cfg.is_playing_square(7, 7)
a9_storage = not cfg.is_playing_square(0, 8)
a10_storage = not cfg.is_playing_square(0, 9)

test("Top Storage - a1 (rank 1) is playing", a1_playing)
test("Top Storage - h8 (rank 8) is playing", h8_playing)
test("Top Storage - a9 (rank 9) is storage", a9_storage)
test("Top Storage - a10 (rank 10) is storage", a10_storage)

# Perimeter Storage
profile = settings.get_profile_by_name("Board with Perimeter Storage")
cfg = parse_board_config(profile['board'])

# Corner squares should be storage
a1_storage = not cfg.is_playing_square(0, 0)
j1_storage = not cfg.is_playing_square(9, 0)
a10_storage = not cfg.is_playing_square(0, 9)
j10_storage = not cfg.is_playing_square(9, 9)

# Center should be playing (files 1-8, ranks 1-8)
b2_playing = cfg.is_playing_square(1, 1)
e5_playing = cfg.is_playing_square(4, 4)
i9_playing = cfg.is_playing_square(8, 8)

test("Perimeter - a1 corner is storage", a1_storage)
test("Perimeter - j1 corner is storage", j1_storage)
test("Perimeter - a10 corner is storage", a10_storage)
test("Perimeter - j10 corner is storage", j10_storage)
test("Perimeter - b2 center is playing", b2_playing)
test("Perimeter - e5 center is playing", e5_playing)
test("Perimeter - i9 center is playing", i9_playing)

# ============================================================================
print("\n" + "=" * 70)
print("TEST 4: Storage Capacity")
print("=" * 70)

# Count storage squares for each layout
configs = [
    ("Standard Chess 400mm", 0),
    ("Board with Top Storage", 16),  # 8 files × 2 ranks
    ("Board with Perimeter Storage", 36)  # 10×10 - 8×8
]

for profile_name, expected_storage in configs:
    profile = settings.get_profile_by_name(profile_name)
    cfg = parse_board_config(profile['board'])

    storage_count = sum(
        1 for f in range(cfg.files)
        for r in range(cfg.ranks)
        if not cfg.is_playing_square(f, r)
    )

    test(f"{profile_name} - {expected_storage} storage squares",
         storage_count == expected_storage,
         f"Expected: {expected_storage}, Got: {storage_count}")

# ============================================================================
print("\n" + "=" * 70)
print("TEST 5: Square Size Calculations")
print("=" * 70)

size_tests = [
    ("Standard Chess 400mm", 50.0, 50.0),
    ("Board with Top Storage", 50.0, 40.0),
    ("Board with Perimeter Storage", 40.0, 40.0)
]

for profile_name, expected_x, expected_y in size_tests:
    profile = settings.get_profile_by_name(profile_name)
    cfg = parse_board_config(profile['board'])

    sq_x = cfg.square_size_x()
    sq_y = cfg.square_size_y()

    test(f"{profile_name} - Square size {expected_x}×{expected_y}mm",
         abs(sq_x - expected_x) < 0.1 and abs(sq_y - expected_y) < 0.1,
         f"Got: {sq_x:.2f}×{sq_y:.2f}mm")

# ============================================================================
print("\n" + "=" * 70)
print("TEST 6: BoardState Integration")
print("=" * 70)

# Test with Perimeter Storage
profile = settings.get_profile_by_name("Board with Perimeter Storage")
cfg = parse_board_config(profile['board'])
board_state = BoardState()  # BoardState doesn't need config parameter

# Place piece in playing area
board_state.set_piece_virtual("e5", Piece(PieceType.PAWN, PieceColor.WHITE))
piece_e5 = board_state.get_piece_virtual("e5")
test("Place white pawn on e5 (playing area)",
     piece_e5 is not None and piece_e5.type == PieceType.PAWN)

# Place piece in storage (corner)
board_state.set_piece_virtual("a1", Piece(PieceType.ROOK, PieceColor.BLACK))
piece_a1 = board_state.get_piece_virtual("a1")
test("Place black rook on a1 (storage)",
     piece_a1 is not None and piece_a1.type == PieceType.ROOK)

# Place piece in storage (top edge)
board_state.set_piece_virtual("e10", Piece(PieceType.QUEEN, PieceColor.BLACK))
piece_e10 = board_state.get_piece_virtual("e10")
test("Place black queen on e10 (storage)",
     piece_e10 is not None and piece_e10.type == PieceType.QUEEN)

# Verify all pieces are tracked
all_pieces = [
    board_state.get_piece_virtual("e5"),
    board_state.get_piece_virtual("a1"),
    board_state.get_piece_virtual("e10")
]
test("All pieces tracked correctly",
     all(p is not None for p in all_pieces),
     f"Found {sum(1 for p in all_pieces if p is not None)}/3 pieces")

# ============================================================================
print("\n" + "=" * 70)
print("TEST 7: Workspace Constraints")
print("=" * 70)

workspace_w = 400.0
workspace_h = 415.0

for profile_name in ["Board with Top Storage", "Board with Perimeter Storage"]:
    profile = settings.get_profile_by_name(profile_name)
    cfg = parse_board_config(profile['board'])

    fits = cfg.width_mm <= workspace_w and cfg.height_mm <= workspace_h

    test(f"{profile_name} - Fits in {workspace_w}×{workspace_h}mm workspace",
         fits,
         f"Board: {cfg.width_mm}×{cfg.height_mm}mm")

# ============================================================================
print("\n" + "=" * 70)
print("TEST 8: Helper Methods")
print("=" * 70)

for profile_name in ["Standard Chess 400mm", "Board with Top Storage", "Board with Perimeter Storage"]:
    profile = settings.get_profile_by_name(profile_name)
    cfg = parse_board_config(profile['board'])

    home = cfg.get_home_square()
    test(f"{profile_name} - get_home_square() returns 'a1'",
         home == "a1",
         f"Returns: {home}")

    offset = cfg.get_playing_area_offset()
    test(f"{profile_name} - get_playing_area_offset() returns tuple",
         isinstance(offset, tuple) and len(offset) == 2,
         f"Returns: {offset}")

# ============================================================================
print("\n" + "=" * 70)
print("TEST 9: StorageLayout Enum")
print("=" * 70)

enum_tests = [
    ("none", StorageLayout.NONE),
    ("top", StorageLayout.TOP),
    ("bottom", StorageLayout.BOTTOM),
    ("perimeter", StorageLayout.PERIMETER)
]

for value, expected in enum_tests:
    layout = StorageLayout(value)
    test(f"StorageLayout('{value}') == {expected.name}",
         layout == expected,
         f"Value: {layout.value}, Name: {layout.name}")

# ============================================================================
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print(f"\nTotal Tests: {test_count}")
print(f"Passed: {pass_count}")
print(f"Failed: {test_count - pass_count}")
print(f"Success Rate: {(pass_count/test_count*100):.1f}%")

if pass_count == test_count:
    print("\n[SUCCESS] All storage layout features working correctly!")
    print("=" * 70)
    sys.exit(0)
else:
    print(f"\n[WARNING] {test_count - pass_count} test(s) failed")
    print("=" * 70)
    sys.exit(1)
