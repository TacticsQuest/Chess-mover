# Advanced Features Guide

## Overview

This guide covers advanced experimental features for the Chess Mover Machine, including edge push and tool-based piece removal strategies. These features are **disabled by default** and should only be enabled for specific use cases.

---

## Table of Contents

1. [When to Use Advanced Features](#when-to-use-advanced-features)
2. [Edge Push System](#edge-push-system)
3. [Tool-Based Pusher](#tool-based-pusher)
4. [Configuration](#configuration)
5. [Safety Considerations](#safety-considerations)
6. [Troubleshooting](#troubleshooting)

---

## When to Use Advanced Features

### Standard Boards (WITH Storage Areas)
**Recommendation**: Keep advanced features **DISABLED**

If your board has a storage layout (PERIMETER or TOP):
- Smart Storage handles all captures automatically
- No need for edge push or tool pusher
- Cleaner, more organized piece management

### Boards WITHOUT Storage Areas
**Recommendation**: Enable **Edge Push** as fallback

If your board is standard 8×8 with no storage:
- Enable edge push for when pieces need to be removed
- Tool pusher is optional (requires physical tool)

---

## Edge Push System

### What It Does

The edge push system removes captured pieces by pushing them off the board edge:

1. Finds empty edge square with adjacent square also empty
2. Moves captured piece to edge square
3. Positions gripper at adjacent (off-board) square
4. Slowly pushes piece off the board edge
5. Tracks which edge squares have been used

### How to Enable

Edit `config/advanced_settings.yaml`:

```yaml
capture_removal:
  edge_push:
    enabled: true  # Set to true to enable
    push_speed_mm_min: 300  # Slow controlled push
    push_distance_mm: 30  # How far to push piece
```

### Edge Square Selection

Edge squares are selected by priority:

1. **Corners** (priority 1): a1, h1, a8, h8
2. **Edge squares** (priority 2): All other perimeter squares

Within each priority, the **closest** square to the captured piece is selected.

### Example Workflow

```
1. Piece captured at e4
2. System finds nearest empty edge: h4
3. System checks adjacent square (i4) is also empty
4. Pick up captured piece from e4
5. Move to h4, place piece
6. Move to i4 (off-board position)
7. Lower gripper to push height
8. Push piece east 30mm off board
9. Raise gripper
```

### Edge Layouts

**Standard 8×8 Board:**
- Total edge squares: 28 (a1-h1, a8-h8, a2-a7, h2-h7)
- Corners: 4
- Edge: 24

**10×10 Board:**
- Total edge squares: 36
- Corners: 4
- Edge: 32

### Code Example

```python
from logic.edge_push import EdgePushManager
from logic.board_state import BoardState

# Create edge push manager
edge_push = EdgePushManager(board_config)

# Find location for captured piece
location = edge_push.find_edge_push_location(board_state, from_square="e4")

if location:
    print(f"Edge square: {location.edge_square}")
    print(f"Push square: {location.push_square}")
    print(f"Direction: {location.direction.value}")

    # Mark as occupied
    edge_push.mark_occupied(location.edge_square)
```

---

## Tool-Based Pusher

### What It Does

Uses a physical pusher tool to professionally remove pieces:

1. **Tool Pickup**: Moves to tool holder, grips pusher tool
2. **Position**: Moves to piece location
3. **Scoop & Push**: Tool scoops piece and pushes off edge cleanly
4. **Tool Return**: Returns tool to holder
5. **Continue**: Resumes game moves

### Tool Specifications

The pusher tool should have:

- **Width**: ~50mm (2 inches) - wider than piece diameter
- **Length**: ~100mm
- **Shape**: Curved/scoop end to contain piece during push
- **Material**: Lightweight (3D-printable plastic or aluminum)
- **Mounting**: Held in designated tool holder square

### Tool Holder Location

The tool must be stored at a designated square:

- **8×8 boards**: Usually `a9` (requires 9th rank off-board)
- **10×10 boards**: Usually `a0` (off-board square)
- **Custom**: Configurable in settings

### How to Enable

**Step 1**: Fabricate pusher tool (3D print or manufacture)

**Step 2**: Mount tool holder at designated square

**Step 3**: Calibrate gripper pickup position

**Step 4**: Edit `config/advanced_settings.yaml`:

```yaml
capture_removal:
  tool_pusher:
    enabled: true  # Set to true to enable
    tool_holder_square: "a9"  # Where tool is stored
    tool_width_mm: 50.0
    tool_length_mm: 100.0
    grip_offset_mm: 30.0  # Where to grip tool
    push_offset_mm: 15.0  # Positioning behind piece
    push_speed_mm_min: 300  # Slow controlled push
    pickup_speed_mm_min: 1000  # Speed for tool operations
```

### Example Workflow

```
1. Piece captured at e4
2. Move to tool holder at a9
3. Lower gripper, grip pusher tool
4. Raise tool
5. Move to e4 with tool
6. Lower tool behind piece
7. Push piece east with scooping motion
8. Raise tool
9. Return to a9
10. Lower tool into holder
11. Open gripper, release tool
12. Raise gripper
13. Continue game
```

### Code Example

```python
from logic.tool_pusher import ToolPusherManager, ToolConfig, ToolType

# Create tool configuration
tool_config = ToolConfig(
    tool_type=ToolType.PUSHER,
    holder_square="a9",
    width_mm=50.0,
    length_mm=100.0,
    grip_offset_mm=30.0,
    push_offset_mm=15.0,
    enabled=True
)

# Create tool pusher manager
tool_pusher = ToolPusherManager(board_config, tool_config)

# Check if tool is available
if tool_pusher.is_tool_available():
    print(f"Tool holder: {tool_pusher.get_tool_holder_square()}")

    # Calculate push position
    push_x, push_y = tool_pusher.calculate_push_position("e4", "east")
    print(f"Push position: ({push_x}, {push_y})")
```

---

## Configuration

### Full Configuration File

Location: `config/advanced_settings.yaml`

```yaml
# Capture Piece Removal Strategies
capture_removal:
  primary_strategy: "smart_storage"

  edge_push:
    enabled: false  # Enable for boards without storage
    push_speed_mm_min: 300
    push_distance_mm: 30

  tool_pusher:
    enabled: false  # Enable when physical tool available
    tool_holder_square: "a9"
    tool_width_mm: 50.0
    tool_length_mm: 100.0
    grip_offset_mm: 30.0
    push_offset_mm: 15.0
    push_speed_mm_min: 300
    pickup_speed_mm_min: 1000

# Storage Configuration
storage:
  default_strategy: "BY_COLOR"
  alert_at_percent: 75
  auto_clear: true

# AI Features (Future)
ai:
  auto_strategy_selection: false
  adaptive_learning: false

# Multi-Board (Future)
multi_board:
  enabled: false
  share_storage: false

# Experimental
experimental:
  detailed_logging: false
  simulation_mode: false
  profiling_enabled: false
```

### Loading Settings in Code

```python
from logic.advanced_settings import AdvancedSettings

# Load settings
advanced_settings = AdvancedSettings()

# Check what's enabled
if advanced_settings.is_edge_push_enabled():
    print("Edge push is enabled")

if advanced_settings.is_tool_pusher_enabled():
    print("Tool pusher is enabled")
    tool_config = advanced_settings.get_tool_config()

# Modify settings programmatically
advanced_settings.set_edge_push_enabled(True)
advanced_settings.save_config()
```

### Integration with Game Controller

```python
from logic.game_controller import GameController
from logic.advanced_settings import AdvancedSettings

# Load advanced settings
advanced_settings = AdvancedSettings()

# Create game controller with advanced features
game_controller = GameController(
    gantry=gantry,
    servos=servos,
    settings=settings,
    board_config=board_config,
    advanced_settings=advanced_settings  # Pass advanced settings
)

# Advanced features now active based on config
```

---

## Safety Considerations

### Edge Push Safety

1. **Push Speed**: Keep at 300mm/min or slower
   - Too fast: piece may fly off unpredictably
   - Too slow: piece may not fall cleanly

2. **Edge Clearance**: Ensure 50mm clearance around board
   - Pieces need space to fall
   - Avoid obstacles near edges

3. **Floor Protection**: Use soft surface or tray to catch pieces
   - Pieces will fall to floor
   - Prevent damage to pieces

4. **Recovery**: Plan for pieces that don't fall cleanly
   - May need manual intervention
   - Keep gripper open during push to avoid grabbing piece

### Tool Pusher Safety

1. **Tool Integrity**: Inspect tool before each session
   - Check for cracks or wear
   - Replace if damaged

2. **Grip Security**: Ensure reliable tool pickup
   - Calibrate grip position
   - Test pickup multiple times before game

3. **Push Force**: Monitor push force
   - Too much force can damage board or tool
   - Too little won't push piece off

4. **Tool Storage**: Secure tool holder
   - Tool should not fall or shift
   - Accessible to gripper

5. **Emergency Stop**: Have emergency stop readily available
   - Tool malfunction could damage board
   - Be ready to stop operation

---

## Troubleshooting

### Edge Push Issues

**Problem**: Piece doesn't fall off board

**Solutions**:
- Increase `push_distance_mm` (try 40-50mm)
- Decrease `push_speed_mm_min` (try 200mm/min)
- Check that edge is truly at board boundary
- Ensure gripper is fully lowered during push

---

**Problem**: No edge squares available

**Solutions**:
- Reset edge push manager: `edge_push.reset()`
- Manually clear some edge squares
- Increase board size or use storage areas

---

**Problem**: Pieces pushed in wrong direction

**Solutions**:
- Verify board orientation in config
- Check edge direction calculations
- Calibrate off-board push square coordinates

---

### Tool Pusher Issues

**Problem**: Tool pickup fails

**Solutions**:
- Recalibrate grip offset (`grip_offset_mm`)
- Check tool holder position
- Verify tool is present at holder square
- Adjust gripper width for tool

---

**Problem**: Tool pushes piece sideways

**Solutions**:
- Adjust `push_offset_mm` to position tool closer behind piece
- Slow down push speed
- Check tool curve angle
- Ensure tool is lowered to correct height

---

**Problem**: Tool damaged during operation

**Solutions**:
- Use stronger material (metal vs plastic)
- Reduce push force/speed
- Redesign tool with reinforced structure
- Add wear indicators to detect damage early

---

## Future Enhancements

### Planned Features

1. **AI Strategy Selection**: Automatically choose best removal strategy based on:
   - Board configuration
   - Game type (blitz, classical, training)
   - Current storage utilization

2. **Multiple Tools**: Support for different tool types:
   - Pusher tool (current)
   - Piece setter tool (for setup)
   - Calibration tool (for alignment)

3. **Learning System**: Adaptive learning from user preferences:
   - Track which strategies work best
   - Optimize push parameters
   - Predict storage needs

4. **Multi-Board Coordination**: Share resources between multiple boards:
   - Shared storage areas
   - Tool sharing
   - Synchronized gameplay

---

## Summary

**Default Configuration**: All advanced features **DISABLED**
- Smart Storage handles everything
- Simple, reliable, tested

**When to Enable**:
- **Edge Push**: Boards without storage areas
- **Tool Pusher**: Professional setups, when tool is fabricated

**Safety First**:
- Start with slow speeds
- Test extensively before real games
- Have recovery plan for failures

**Next Steps**:
1. Review your board configuration
2. Decide if you need advanced features
3. If yes, start with edge push (simpler)
4. Consider tool pusher for ultra-professional setup

For most users, keeping these features **disabled** and using Smart Storage is the best approach.
