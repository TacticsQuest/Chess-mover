# Storage Future Enhancements

## Long-Term Goals for Smart Storage System

This document outlines future enhancements to the Smart Storage Management system based on different board configurations and advanced piece handling strategies.

---

## 1. Edge Push for Boards Without Storage Areas

### Problem
Larger boards (e.g., 8×8 with no dedicated storage area) need a way to remove captured pieces from the playing area.

### Solution: Edge Push Strategy

**Medium-Term Goal:**

For boards without dedicated storage squares:
1. **Find Empty Edge Square**: Scan perimeter for an empty edge square with adjacent square also empty
2. **Place on Edge**: Move captured piece to the empty edge square
3. **Position for Push**: Move gantry to the empty adjacent square
4. **Lower and Push**: Lower gripper and slowly push piece off the board edge

**Benefits:**
- Works on any board size without storage areas
- Simple mechanical action
- No need for extra physical space

**Implementation Steps:**
```python
def _find_edge_push_square(self) -> Optional[Tuple[str, str]]:
    """
    Find an empty edge square with empty adjacent square.

    Returns:
        (edge_square, push_square) or None if no suitable pair found
    """
    # Scan all edge squares (a-file, h-file, rank 1, rank 8)
    # Check if both edge square and adjacent square are empty
    # Return the pair if found
    pass

def _plan_edge_push(self, captured_piece, from_square) -> List[GantryAction]:
    """
    Plan action sequence to push piece off board edge.

    Sequence:
    1. Pick up captured piece from capture square
    2. Move to empty edge square
    3. Place piece on edge
    4. Move to adjacent square (off-board side)
    5. Lower gripper
    6. Slowly push piece off board
    7. Raise gripper
    """
    pass
```

**Technical Considerations:**
- **Safety**: Ensure slow push speed to avoid piece flying off
- **Edge Detection**: Map which edge squares can push which direction
- **Recovery**: Handle pieces that don't fall off cleanly
- **Storage Tracking**: Track which edge squares have pieces pushed off

---

## 2. Tool-Based Piece Pusher (Ultra Long-Term)

### Problem
Round chess pieces can roll or move sideways when pushed directly by the gripper, leading to inconsistent removal.

### Solution: Specialized Pusher Tool

**Ultra Long-Term Goal:**

Machine grabs a horizontal "pusher tool" with a curved end designed to scoop and push pieces straight off the board.

**Tool Specifications:**
- **Width**: ~2 inches (50mm) - wider than piece diameter
- **Shape**: Curved/scoop-shaped end to contain piece during push
- **Material**: Lightweight (3D-printable plastic or aluminum)
- **Mounting**: Tool holder mounted at designated board location

**Workflow:**
1. **Tool Pickup**: Move to tool holder, grip pusher tool
2. **Position at Piece**: Move to square with captured piece
3. **Scoop & Push**: Lower tool behind piece, push forward to scoop and push off edge
4. **Tool Return**: Return pusher tool to holder
5. **Continue**: Resume game moves

**Benefits:**
- **Consistent Removal**: Curved shape ensures piece travels straight
- **Distance**: Tool provides more reach than gripper alone
- **Piece Safety**: Scooping action prevents pieces from tipping or rolling sideways
- **Professional Appearance**: Clean, predictable piece removal

**Implementation Phases:**

**Phase 1: Tool Design**
- CAD design of pusher tool
- Test 3D printed prototypes
- Optimize curve angle and width

**Phase 2: Tool Holder**
- Design mount location (e.g., corner of board)
- Gripper pickup/release mechanism
- Position calibration

**Phase 3: Software Integration**
```python
class ToolType(Enum):
    PUSHER = "pusher"
    # Future tools: PIECE_SETTER, CALIBRATOR, etc.

def _plan_tool_based_push(self, captured_piece, from_square) -> List[GantryAction]:
    """
    Plan action sequence using pusher tool.

    Sequence:
    1. Move to tool holder
    2. Grip pusher tool
    3. Move to captured piece square
    4. Position tool behind piece
    5. Lower tool
    6. Push piece off edge (slow, controlled)
    7. Raise tool
    8. Return to tool holder
    9. Release tool
    """
    pass
```

**Phase 4: Testing & Refinement**
- Test with all piece types (pawns, rooks, queens, etc.)
- Adjust push speed and force
- Handle edge cases (pieces near corners, multiple pieces)

---

## 3. Hybrid Strategies

### Combination Approaches

Depending on board configuration, combine multiple strategies:

| Board Type | Primary Strategy | Fallback Strategy |
|-----------|------------------|-------------------|
| Perimeter Storage (10×10) | Smart Storage (BY_COLOR) | N/A (36 squares) |
| Top Storage (8×10) | Smart Storage (BY_TYPE) | Edge Push (if full) |
| Standard 8×8 (no storage) | Edge Push | Tool-Based Push |
| Custom Layouts | Configurable | User-defined |

**Configuration Example:**
```yaml
board:
  storage_layout: NONE
  capture_strategy:
    primary: edge_push
    fallback: tool_push
    tool_available: false  # Set true when tool implemented
```

---

## 4. Advanced Storage Features

### Dynamic Strategy Selection
AI-recommended storage strategy based on:
- Game type (blitz, casual, training)
- Piece capture frequency
- Promotion likelihood
- Storage utilization

### Multi-Zone Storage
Divide storage into zones:
- **Zone A**: Frequently accessed (for promotions)
- **Zone B**: Long-term storage (captured pieces)
- **Zone C**: Reserved/future use

### Storage Analytics
Track and display:
- Heat map of storage usage
- Average piece retrieval time
- Storage efficiency score
- Predictions for space exhaustion

---

## 5. Implementation Priority

### Immediate (Completed ✅)
- Smart Storage with 4 strategies
- Storage map widget
- TacticsQuest integration

### Short-Term (Next 3-6 months)
- Edge push for boards without storage
- Storage full alerts
- Automatic strategy switching

### Medium-Term (6-12 months)
- Tool holder design and prototyping
- Pusher tool CAD and 3D printing
- Tool-based push software integration

### Long-Term (12+ months)
- Multiple tool types (pusher, setter, calibrator)
- AI-driven strategy selection
- Storage analytics dashboard
- Multi-board coordination

---

## 6. Technical Considerations

### Edge Push Implementation
- **Coordinate Mapping**: Define off-board push coordinates for each edge
- **Force Control**: Implement slow, controlled push (low feedrate)
- **Safety Checks**: Verify adjacent square is truly empty
- **Recovery Mode**: Handle pieces that don't fall cleanly

### Tool-Based Push Implementation
- **Tool Calibration**: Precise grip location on tool
- **Tool Orientation**: Ensure correct angle during pickup
- **Push Dynamics**: Calculate optimal push speed and distance
- **Tool Wear**: Monitor tool condition, replacement alerts

---

## 7. User Configuration

Allow users to configure storage behavior:

```yaml
storage:
  strategy: BY_COLOR          # NEAREST, BY_COLOR, BY_TYPE, CHRONOLOGICAL
  fallback: edge_push         # What to do when storage full
  use_tool_push: false        # Enable tool-based push (when available)
  tool_holder_square: a0      # Where pusher tool is stored
  edge_push_speed: 500        # mm/min for pushing pieces off
  auto_clear_storage: true    # Clear storage between games
  storage_alerts: true        # Alert when 75% full
```

---

## 8. Future Vision

**Fully Automated Chess Experience:**
- Pieces automatically removed via smart strategies
- Tools automatically selected for optimal piece handling
- Storage managed intelligently with no user intervention
- Multiple board configurations supported seamlessly
- Professional, museum-quality piece movement

**Integration with TacticsQuest:**
- Puzzle mode uses smart storage for captured pieces
- Training mode tracks material advantage visually
- Tournament mode ensures consistent, fair piece removal
- Analytics track storage efficiency across games

---

## Summary

The Smart Storage system has a clear path forward:

1. ✅ **Current**: Smart storage with 4 strategies
2. 🔄 **Next**: Edge push for boards without storage
3. 🚀 **Future**: Tool-based push for professional quality
4. 🌟 **Vision**: Fully automated, AI-driven piece management

This roadmap ensures the Chess Mover Machine can handle any board configuration while continuously improving the user experience.
