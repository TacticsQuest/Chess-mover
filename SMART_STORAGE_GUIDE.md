# Smart Storage Management System - User Guide

## Overview

The Smart Storage Management system automatically organizes captured chess pieces in designated storage areas on your board. It integrates with TacticsQuest to track material and provides intelligent piece placement.

---

## Features

### 1. **Automatic Storage Assignment**
When you capture a piece, the system automatically:
- Finds the best storage square based on strategy
- Routes the piece to that location
- Tracks occupancy in real-time
- Syncs with TacticsQuest database

### 2. **Multiple Organization Strategies**

| Strategy | Description | Best For |
|----------|-------------|----------|
| **NEAREST** | Assigns to closest available square | Fast games, minimal movement |
| **BY_COLOR** | White pieces left, black pieces right | Visual organization |
| **BY_TYPE** | Groups similar pieces together | Finding pieces for promotions |
| **CHRONOLOGICAL** | First captured → first square | Historical tracking |

### 3. **Visual Storage Map**
- Real-time grid showing occupied/empty squares
- Color-coded by piece type
- Statistics (utilization %, piece counts)
- Integrated in main UI

### 4. **TacticsQuest Integration**
- Material count synced to cloud
- Puzzle mode auto-manages captures
- Training statistics tracked
- Multi-device sync

---

## Storage Layouts

### Top Storage (8×10 Board)
```
Ranks 9-10: Storage (16 squares)
Ranks 1-8:  Playing area (64 squares)
```

**Strategy Recommendations**:
- NEAREST: Best for rapid games
- BY_TYPE: Pawns on rank 9, pieces on rank 10

### Perimeter Storage (10×10 Board)
```
Border: Storage (36 squares)
  - 4 corners
  - 32 edge squares
Center 8×8: Playing area (64 squares)
```

**Strategy Recommendations**:
- BY_COLOR: White on left (files a-b), black on right (files i-j)
- CHRONOLOGICAL: Fill corners first, then edges

---

## How It Works

### Capture Flow

```
1. Piece Captured
   ↓
2. SmartStorage.assign_storage_square(piece, from_square)
   ↓
3. Strategy determines best square
   ↓
4. Move executor routes piece:
   from_square → storage_square
   ↓
5. Storage map updated
   ↓
6. TacticsQuest synced (material count)
```

### Promotion Flow

```
1. Pawn reaches 8th rank
   ↓
2. User selects promotion piece (Q/R/B/N)
   ↓
3. SmartStorage.find_piece_in_storage(type, color)
   ↓
4. Move executor:
   a. Move pawn to storage
   b. Retrieve promoted piece from storage
   c. Place on promotion square
   ↓
5. Storage map updated
```

---

## API Examples

### Python API

```python
from logic.smart_storage import SmartStorage, StorageStrategy
from logic.board_map import BoardConfig
from logic.board_state import Piece, PieceType, PieceColor

# Initialize
board_cfg = BoardConfig(...)  # Your board config
storage = SmartStorage(board_cfg, strategy=StorageStrategy.BY_COLOR)

# Capture a piece
piece = Piece(PieceType.KNIGHT, PieceColor.BLACK)
from_square = "e4"

storage_square = storage.assign_storage_square(piece, from_square)
# Returns: "a9" (or similar based on strategy)

# Mark as occupied
storage.mark_occupied(storage_square, piece)

# Get statistics
stats = storage.get_storage_stats()
print(f"Storage utilization: {stats['utilization']:.0f}%")
print(f"White pieces captured: {sum(stats['piece_counts'][PieceColor.WHITE].values())}")

# Find a piece for promotion
queen_square = storage.find_piece_in_storage(PieceType.QUEEN, PieceColor.WHITE)
if queen_square:
    print(f"Queen found at {queen_square}")
else:
    print("No queen available in storage")

# Get visual representation
visual_map = storage.get_visual_map()
for row in visual_map:
    print(' '.join(row))
```

### TacticsQuest API

```python
from services.tacticsquest_sync import TacticsQuestSync, Puzzle

# Initialize
sync = TacticsQuestSync(
    supabase_url="your_url",
    supabase_key="your_key",
    user_id="your_user_id",
    game_controller=game_controller
)

# Fetch daily puzzle
puzzle = sync.get_daily_puzzle()
if puzzle:
    print(f"Puzzle {puzzle.puzzle_id}")
    print(f"FEN: {puzzle.fen}")
    print(f"Solution: {puzzle.moves}")
    print(f"Themes: {', '.join(puzzle.themes)}")

# Get random puzzle by difficulty
puzzle = sync.get_random_puzzle(difficulty='medium', themes=['fork', 'pin'])

# Get user-tailored puzzles
puzzles = sync.get_user_puzzles(limit=5, difficulty='hard')
for p in puzzles:
    print(f"- {p.puzzle_id}: {p.rating} ({p.difficulty})")

# Submit puzzle attempt
success = sync.submit_puzzle_attempt(
    puzzle_id=puzzle.puzzle_id,
    success=True,
    time_seconds=45,
    attempts=1
)
```

---

## Storage Strategies in Detail

### 1. NEAREST
**Algorithm**: Manhattan distance from capture square to storage square

**Pros**:
- Minimal machine movement
- Fastest capture handling
- Natural flow

**Cons**:
- No organization pattern
- Hard to find specific pieces

**Best for**: Blitz games, rapid captures

### 2. BY_COLOR
**Algorithm**: White pieces → left half of storage, Black pieces → right half

**Pros**:
- Easy to find pieces by color
- Visual symmetry
- Intuitive organization

**Cons**:
- May not use space efficiently
- Longer movement for captures on wrong side

**Best for**: Teaching, demonstrations, casual play

### 3. BY_TYPE
**Algorithm**: Groups pieces by type (all pawns together, all knights together, etc.)

**Pros**:
- Easy to find specific piece types
- Great for promotions
- Historical chess tradition

**Cons**:
- Requires more complex routing
- May fill unevenly

**Best for**: Games with many promotions, endgame training

### 4. CHRONOLOGICAL
**Algorithm**: Fill storage squares in priority order (corners first, then edges)

**Pros**:
- Predictable pattern
- Easy to track capture order
- Aesthetic appeal

**Cons**:
- No relationship to piece properties
- Harder to find specific pieces

**Best for**: Game archiving, historical documentation

---

## UI Integration

### Storage Map Widget

Location: Right panel, below FEN import/export

Features:
- **Visual Grid**: Compact representation of all squares
- **Color Coding**:
  - Gold: Occupied by white piece
  - Dark gray: Occupied by black piece
  - Medium gray: Empty storage
  - Very dark: Playing square
- **Statistics Bar**: Shows utilization percentage
- **Strategy Selector**: Dropdown to change strategy on-the-fly

### How to Use

1. **View Storage Status**: Look at the storage map widget to see available space
2. **Change Strategy**: Select from dropdown (changes take effect immediately)
3. **Monitor Utilization**: Watch the percentage to know when storage is filling up
4. **Find Pieces**: Use visual map to locate captured pieces for promotions

---

## TacticsQuest Integration

### Puzzle Mode

When solving TacticsQuest puzzles:

1. **Setup**: Machine automatically sets up puzzle position
2. **Captures**: Any captures in puzzle automatically routed to storage
3. **Validation**: Each move validated against puzzle solution
4. **Cleanup**: After puzzle, captured pieces can be auto-cleared
5. **Tracking**: Puzzle performance synced to TacticsQuest profile

### Game Mode

When playing TacticsQuest games:

1. **Sync**: Opponent moves appear on physical board
2. **Captures**: Automatically organized in storage
3. **Material Tracking**: Real-time material count in TacticsQuest UI
4. **Promotions**: Retrieve pieces from storage automatically
5. **Analysis**: Post-game, storage shows final material balance

---

## Advanced Features

### Storage Alerts

System alerts you when:
- ✓ Storage reaches 75% capacity
- ✓ Storage is full (cannot accept more pieces)
- ✓ Promoted piece not available in storage
- ✓ Strategy change recommended based on usage pattern

### Auto-Cleanup

After game ends:
- Option to auto-clear storage
- Option to organize by type for next game
- Option to return specific pieces to starting position

### Custom Strategies

You can define custom strategies by extending `StorageStrategy`:

```python
class CustomStrategy(StorageStrategy):
    # Implement your own logic
    pass
```

---

## Troubleshooting

### Problem: "Storage Full" Error

**Solution**:
1. Manually remove some captured pieces
2. Switch to a larger board profile (e.g., perimeter storage has 36 squares vs top storage's 16)
3. Enable auto-cleanup between games

### Problem: Can't Find Piece for Promotion

**Solution**:
1. Check storage map - is that piece type in storage?
2. If not, manually place a piece in storage first
3. Or promote to a different piece type

### Problem: Storage Map Not Updating

**Solution**:
1. Click "Refresh" button
2. Check if board state sync is enabled
3. Restart the application

---

## Performance Tips

1. **Choose Right Strategy**:
   - Fast games → NEAREST
   - Teaching → BY_COLOR
   - Promotions → BY_TYPE

2. **Pre-allocate Promoted Pieces**:
   - Place extra queens in storage before game
   - Reduces promotion delays

3. **Regular Cleanup**:
   - Clear storage between games
   - Prevents confusion and errors

4. **Use Perimeter Storage for Long Games**:
   - 36 squares vs 16 squares
   - Handles many captures without filling

---

## Future Enhancements

- 🔄 AI-recommended strategy based on game type
- 📊 Historical storage usage analytics
- 🎯 Piece-specific storage zones (configurable)
- 🌐 Multi-board storage sharing (remote games)
- 🔊 Audio alerts for storage events
- 📱 Mobile app storage management

---

## Summary

Smart Storage Management makes the Chess Mover Machine truly hands-free:
- ✓ No manual piece organization needed
- ✓ Automatic routing and tracking
- ✓ TacticsQuest integration for cloud sync
- ✓ Multiple strategies for different use cases
- ✓ Visual feedback and statistics

Combined with TacticsQuest's puzzle and game features, this creates a seamless physical-digital chess experience.
