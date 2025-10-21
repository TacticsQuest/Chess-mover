# Storage Layout System

The Chess Mover Machine now supports flexible storage area configurations, allowing captured pieces to be stored in different areas around the playing board.

## Overview

Instead of a fixed 14×14 board with captured piece storage, the system now supports multiple storage layout configurations:

1. **NONE** - Standard 8×8 chess board (no storage area)
2. **TOP** - 8×10 board with 2 ranks of storage above the playing area
3. **BOTTOM** - 8×10 board with 2 ranks of storage below the playing area
4. **PERIMETER** - 10×10 board with 1-square border around the playing area

## Storage Layout Types

### NONE (Standard Board)
- **Grid Size**: 8×8
- **Playing Area**: Entire board (a1-h8)
- **Storage Area**: None
- **Square Size**: 50mm × 50mm (for 400mm board)
- **Use Case**: Standard chess without captured piece tracking

### TOP Storage
- **Grid Size**: 8×10
- **Playing Area**: Ranks 1-8 (standard chess area: a1-h8)
- **Storage Area**: Ranks 9-10 (16 squares: a9-h9, a10-h10)
- **Square Size**: 50mm × 40mm (for 400mm board)
- **Home Position**: a1 (bottom-left)
- **Use Case**: Maximum vertical storage within workspace constraints

### BOTTOM Storage
- **Grid Size**: 8×10
- **Playing Area**: Ranks 3-10 (shifted up 2 ranks)
- **Storage Area**: Ranks 1-2 (16 squares: a1-h1, a2-h2)
- **Square Size**: 50mm × 40mm (for 400mm board)
- **Home Position**: a1 (bottom-left storage area)
- **Use Case**: Storage below playing area (less common)

### PERIMETER Storage
- **Grid Size**: 10×10
- **Playing Area**: Center 8×8 (files b-i, ranks 2-9)
- **Storage Area**: All perimeter squares (36 squares total)
  - Bottom row: a1-j1
  - Top row: a10-j10
  - Left column: a2-a9
  - Right column: j2-j9
- **Square Size**: 40mm × 40mm (for 400mm board)
- **Home Position**: a1 (bottom-left perimeter)
- **Use Case**: Maximum storage capacity, pieces accessible from all sides

## Workspace Constraints

The storage layouts are designed to fit within the Creality Falcon 5W workspace:
- **Workspace**: 400mm × 415mm
- **Board**: 400mm × 400mm
- **Available Extra Space**: 15mm in Y direction

This limits practical storage options to:
- 2 ranks maximum in one direction (TOP/BOTTOM)
- 1 square perimeter border (PERIMETER)

## Configuration

### Profile Structure

Each profile in `config/settings.yaml` can specify a storage layout:

```yaml
- name: Board with Top Storage
  board:
    files: 8
    ranks: 10
    width_mm: 400.0
    height_mm: 400.0
    origin_x_mm: 0.0
    origin_y_mm: 0.0
    feedrate_mm_min: 2000
    storage_layout: top        # Storage layout type
    play_area:                  # Playing area definition
      min_file: 0               # Files a-h (0-indexed: 0-7)
      max_file: 7
      min_rank: 0               # Ranks 1-8 (0-indexed: 0-7)
      max_rank: 7
  pieces:
    # ... piece configurations
```

### Storage Layout Field

The `storage_layout` field accepts:
- `none` - No storage area
- `top` - Storage above playing area
- `bottom` - Storage below playing area
- `perimeter` - Storage around perimeter

### Play Area Field

The `play_area` field defines which squares are used for chess gameplay:
- `min_file`: Leftmost file (0 = a, 1 = b, ...)
- `max_file`: Rightmost file (inclusive)
- `min_rank`: Bottom rank (0 = rank 1, 1 = rank 2, ...)
- `max_rank`: Top rank (inclusive)

## Visual Indicators

The UI provides several visual indicators for storage layouts:

1. **Storage Layout Label**: Displayed at top of board workspace
   - "Standard Board (No Storage)"
   - "Storage: Top 2 Ranks"
   - "Storage: Bottom 2 Ranks"
   - "Storage: Perimeter Border"

2. **Square Colors**:
   - Playing squares: Standard light/dark chess pattern
   - Storage squares: Dark gray (#4a4a4a)
   - Occupied storage (when toggled): Even darker gray (#2a2a2a)

3. **File/Rank Labels**:
   - Playing area labels: Gray
   - Storage area labels: Orange and bold

4. **Show Occupied Storage Toggle**:
   - Button in Board Setup section
   - When ON: Occupied storage squares are darker
   - When OFF: All storage squares same color

## Code Architecture

### BoardConfig Class (`logic/board_map.py`)

```python
@dataclass
class BoardConfig:
    files: int
    ranks: int
    width_mm: float
    height_mm: float
    origin_x_mm: float
    origin_y_mm: float
    play_area: Optional[PlayArea] = None
    storage_layout: StorageLayout = StorageLayout.NONE

    def is_playing_square(self, file_idx: int, rank_idx: int) -> bool:
        """Check if square is in playing area."""
        if self.play_area is None:
            return True  # Entire board is playing area
        return (self.play_area.min_file <= file_idx <= self.play_area.max_file and
                self.play_area.min_rank <= rank_idx <= self.play_area.max_rank)

    def is_captured_piece_square(self, file_idx: int, rank_idx: int) -> bool:
        """Check if square is in storage area."""
        return not self.is_playing_square(file_idx, rank_idx)

    def get_home_square(self) -> str:
        """Get machine home position (0,0) square notation."""
        # All layouts currently use a1 as home
        return "a1"

    def get_playing_area_offset(self) -> tuple[int, int]:
        """Get offset from board origin to playing area bottom-left."""
        if self.play_area is None:
            return (0, 0)
        return (self.play_area.min_file, self.play_area.min_rank)
```

### StorageLayout Enum

```python
class StorageLayout(Enum):
    NONE = "none"
    TOP = "top"
    BOTTOM = "bottom"
    PERIMETER = "perimeter"
```

## Machine Integration

The storage layout system integrates with the machine controller:

1. **Piece Tracking**: `BoardState` tracks all pieces on all squares (playing + storage)
2. **Square Classification**: Board knows which squares are playing vs storage
3. **Movement Planning**: Machine can move pieces to/from storage areas
4. **Calibration**: Home position (0,0) is at a1 for all layouts

## Creating New Profiles

To create a new profile with a storage layout:

1. Edit `config/settings.yaml`
2. Add a new profile under `profiles.saved`:

```yaml
- name: My Custom Board
  board:
    files: 10              # Total grid size
    ranks: 10
    width_mm: 400.0
    height_mm: 400.0
    origin_x_mm: 0.0
    origin_y_mm: 0.0
    feedrate_mm_min: 2000
    storage_layout: perimeter   # Choose: none, top, bottom, perimeter
    play_area:
      min_file: 1          # Center 8x8 playing area
      max_file: 8
      min_rank: 1
      max_rank: 8
  pieces:
    # Copy piece configurations from existing profiles
```

3. Save and restart the application
4. Select your profile from the dropdown

## Testing

Test scripts are provided:
- `test_storage_layout.py` - Verify configuration loading
- `test_boardconfig_parsing.py` - Test BoardConfig parsing and square classification

Run tests:
```bash
python test_storage_layout.py
python test_boardconfig_parsing.py
```

## Future Enhancements

Potential improvements:
- Custom storage area shapes (not just top/perimeter)
- Per-profile home position configuration
- Storage square assignment strategies (e.g., white pieces on left, black on right)
- Visual indicators showing which pieces are in storage
- Storage square availability tracking
