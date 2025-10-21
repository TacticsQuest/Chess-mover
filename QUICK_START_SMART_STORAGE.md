# Quick Start: Smart Storage + TacticsQuest

## 5-Minute Setup Guide

### 1. Import Smart Storage

```python
from logic.smart_storage import SmartStorage, StorageStrategy
from logic.board_map import BoardConfig
from logic.profiles import Settings

# Load your board configuration
settings = Settings()
profile = settings.get_profile_by_name("Board with Perimeter Storage")
board_cfg = # ... parse to BoardConfig

# Initialize smart storage
smart_storage = SmartStorage(
    board_config=board_cfg,
    strategy=StorageStrategy.BY_COLOR  # or NEAREST, BY_TYPE, CHRONOLOGICAL
)
```

### 2. Assign Storage Squares

```python
from logic.board_state import Piece, PieceType, PieceColor

# When a piece is captured
captured_piece = Piece(PieceType.KNIGHT, PieceColor.BLACK)
capture_square = "e4"  # Where it was captured

# Get storage square assignment
storage_square = smart_storage.assign_storage_square(captured_piece, capture_square)
print(f"Route {captured_piece} to {storage_square}")

# Mark as occupied
smart_storage.mark_occupied(storage_square, captured_piece)
```

### 3. Use TacticsQuest API

```python
from services.tacticsquest_sync import TacticsQuestSync

# Initialize (get credentials from environment or config)
sync = TacticsQuestSync(
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_key=os.getenv("SUPABASE_KEY"),
    user_id="your-user-id",
    game_controller=game_controller
)

# Fetch a puzzle
puzzle = sync.get_daily_puzzle()
if puzzle:
    print(f"Puzzle: {puzzle.fen}")
    print(f"Rating: {puzzle.rating}")
    print(f"Solution: {' '.join(puzzle.moves)}")

# Submit attempt
sync.submit_puzzle_attempt(
    puzzle_id=puzzle.puzzle_id,
    success=True,
    time_seconds=32,
    attempts=1
)
```

### 4. Display Storage Map (UI)

```python
from ui.storage_map_widget import StorageMapWidget

# In your UI code
theme = {
    'panel_bg': '#252525',
    'canvas_bg': '#2d2d2d',
    'input_bg': '#3a3a3a',
    'fg': '#e0e0e0',
    'text_secondary': '#95a5a6'
}

storage_widget = StorageMapWidget(
    parent=right_panel,
    smart_storage=smart_storage,
    theme=theme
)
storage_widget.pack(fill=tk.BOTH, expand=True)

# Refresh when board changes
storage_widget.refresh(board_state)
```

---

## Common Use Cases

### Use Case 1: Auto-Route Captured Pieces

```python
def handle_capture(capturing_move, captured_piece, from_square):
    """Automatically route captured piece to storage."""

    # Assign storage square
    storage_square = smart_storage.assign_storage_square(
        captured_piece,
        from_square
    )

    # Execute move sequence:
    # 1. Move capturing piece to destination
    # 2. Pick up captured piece
    # 3. Move to storage square
    # 4. Drop captured piece

    move_executor.execute_capture_with_storage(
        capturing_move,
        captured_piece,
        storage_square
    )

    # Update storage map
    smart_storage.mark_occupied(storage_square, captured_piece)

    # Refresh UI
    storage_widget.refresh()
```

### Use Case 2: Retrieve Piece for Promotion

```python
def handle_promotion(promotion_square, promoted_piece_type, color):
    """Retrieve promoted piece from storage."""

    # Find piece in storage
    piece_square = smart_storage.find_piece_in_storage(
        promoted_piece_type,
        color
    )

    if piece_square:
        # Execute promotion sequence:
        # 1. Pick up pawn from promotion square
        # 2. Move to storage
        # 3. Pick up promoted piece from storage
        # 4. Move to promotion square
        # 5. Place promoted piece

        move_executor.execute_promotion(
            promotion_square,
            piece_square,
            promoted_piece_type
        )

        # Update storage
        smart_storage.mark_empty(piece_square)
        storage_widget.refresh()
    else:
        print(f"Error: No {promoted_piece_type} available in storage!")
```

### Use Case 3: Solve TacticsQuest Puzzle

```python
def solve_puzzle_mode():
    """Interactive puzzle solving mode."""

    # Fetch puzzle
    puzzle = sync.get_random_puzzle(difficulty='medium')

    # Set up position
    board_state.load_fen(puzzle.fen, 'virtual')
    move_executor.sync_board_to_virtual()

    # Track solving
    start_time = time.time()
    attempts = 0
    solution_index = 0

    while solution_index < len(puzzle.moves):
        # Wait for user's physical move
        user_move = wait_for_physical_move()
        attempts += 1

        # Check if correct
        if user_move == puzzle.moves[solution_index]:
            solution_index += 1

            # If there's a response move, execute it
            if solution_index < len(puzzle.moves):
                response_move = puzzle.moves[solution_index]
                move_executor.execute_move(response_move, physically=True)
                solution_index += 1
        else:
            # Wrong move - undo and try again
            move_executor.undo_last_move()
            print("Incorrect! Try again.")

    # Puzzle solved!
    elapsed_time = int(time.time() - start_time)

    sync.submit_puzzle_attempt(
        puzzle_id=puzzle.puzzle_id,
        success=True,
        time_seconds=elapsed_time,
        attempts=attempts
    )

    print(f"Puzzle solved in {elapsed_time}s with {attempts} attempts!")
```

---

## Configuration

### Change Storage Strategy

```python
# Change strategy on-the-fly
smart_storage.set_strategy(StorageStrategy.BY_TYPE)

# Visual widget will automatically update
storage_widget.refresh()
```

### Get Storage Statistics

```python
stats = smart_storage.get_storage_stats()

print(f"Total squares: {stats['total_squares']}")
print(f"Occupied: {stats['occupied']}")
print(f"Available: {stats['available']}")
print(f"Utilization: {stats['utilization']:.1f}%")
print(f"Strategy: {stats['strategy']}")

# Piece counts
white_counts = stats['piece_counts'][PieceColor.WHITE]
black_counts = stats['piece_counts'][PieceColor.BLACK]

print(f"\nWhite captured:")
for piece_type, count in white_counts.items():
    if count > 0:
        print(f"  {piece_type.value}: {count}")

print(f"\nBlack captured:")
for piece_type, count in black_counts.items():
    if count > 0:
        print(f"  {piece_type.value}: {count}")
```

### Sync with Board State

```python
# Ensure storage map matches actual board
smart_storage.sync_with_board_state(board_state)

# This checks all storage squares and updates occupancy
```

---

## Troubleshooting

### Problem: "No storage square available"

```python
storage_square = smart_storage.assign_storage_square(piece, from_square)

if storage_square is None:
    print("Storage is full!")

    # Options:
    # 1. Clear some storage manually
    # 2. Use larger board profile
    # 3. Auto-cleanup old pieces
    available = smart_storage.storage_map.get_available_count()
    print(f"Available squares: {available}")
```

### Problem: Visual map not updating

```python
# Force refresh
storage_widget.refresh(board_state)

# Or rebuild storage map
smart_storage.sync_with_board_state(board_state)
storage_widget.refresh()
```

---

## Best Practices

1. **Always sync after captures**
   ```python
   smart_storage.mark_occupied(square, piece)
   storage_widget.refresh(board_state)
   ```

2. **Check availability before assignment**
   ```python
   available = smart_storage.storage_map.get_available_count()
   if available < 3:
       print("Warning: Storage filling up!")
   ```

3. **Use BY_TYPE for games with promotions**
   ```python
   if game_has_many_pawns_remaining:
       smart_storage.set_strategy(StorageStrategy.BY_TYPE)
   ```

4. **Clear storage between games**
   ```python
   # After game ends
   for square in smart_storage.storage_map.squares:
       smart_storage.mark_empty(square)
   storage_widget.refresh()
   ```

---

## Complete Example

```python
from logic.smart_storage import SmartStorage, StorageStrategy
from services.tacticsquest_sync import TacticsQuestSync
from ui.storage_map_widget import StorageMapWidget

# 1. Initialize smart storage
smart_storage = SmartStorage(board_cfg, StorageStrategy.BY_COLOR)

# 2. Initialize TacticsQuest sync
tq_sync = TacticsQuestSync(url, key, user_id, game_controller)

# 3. Create storage UI widget
storage_widget = StorageMapWidget(parent, smart_storage, theme)

# 4. Fetch and solve puzzle
puzzle = tq_sync.get_daily_puzzle()
board_state.load_fen(puzzle.fen, 'virtual')

# 5. Handle captures during puzzle
def on_capture(captured_piece, from_square):
    storage_square = smart_storage.assign_storage_square(
        captured_piece, from_square
    )
    move_executor.route_to_storage(captured_piece, storage_square)
    smart_storage.mark_occupied(storage_square, captured_piece)
    storage_widget.refresh(board_state)

# 6. Submit result
tq_sync.submit_puzzle_attempt(puzzle.puzzle_id, True, 45, 1)

# 7. Check statistics
stats = smart_storage.get_storage_stats()
print(f"Storage utilization: {stats['utilization']:.0f}%")
```

---

That's it! You now have:
- ✅ Automatic storage management
- ✅ TacticsQuest integration
- ✅ Visual feedback
- ✅ Multiple strategies

For more details, see:
- `SMART_STORAGE_GUIDE.md` - Complete user guide
- `IMPLEMENTATION_SUMMARY.md` - Technical details
- `logic/smart_storage.py` - Source code
- `services/tacticsquest_sync.py` - API client
