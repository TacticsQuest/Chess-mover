"""
Tool-Based Pusher System

Manages pusher tool for professional-quality piece removal from board edges.
Uses a curved pusher tool to scoop and push pieces off the board cleanly.
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum

from logic.board_map import BoardConfig


class ToolType(Enum):
    """Types of tools available."""
    PUSHER = "pusher"           # Curved pusher for edge removal
    PIECE_SETTER = "setter"     # Future: for piece placement
    CALIBRATOR = "calibrator"   # Future: for board calibration


@dataclass
class ToolConfig:
    """Configuration for a tool."""
    tool_type: ToolType
    holder_square: str          # Where tool is stored on board
    width_mm: float            # Tool width
    length_mm: float           # Tool length
    grip_offset_mm: float      # Offset from tool end to grip point
    push_offset_mm: float      # Offset behind piece for pushing
    enabled: bool = False      # Whether tool is available for use


class ToolPusherManager:
    """
    Manages tool-based piece pushing.

    Coordinates tool pickup, piece pushing, and tool return.
    """

    def __init__(self, board_config: BoardConfig, tool_config: Optional[ToolConfig] = None):
        """
        Initialize tool pusher manager.

        Args:
            board_config: Board configuration
            tool_config: Tool configuration (None = tool not available)
        """
        self.board_config = board_config
        self.tool_config = tool_config
        self.tool_in_hand = False

    def is_tool_available(self) -> bool:
        """Check if pusher tool is available and enabled."""
        return self.tool_config is not None and self.tool_config.enabled

    def get_tool_holder_square(self) -> Optional[str]:
        """Get square where tool is stored."""
        if self.tool_config:
            return self.tool_config.holder_square
        return None

    def calculate_push_position(self, piece_square: str, push_direction: str) -> Tuple[float, float]:
        """
        Calculate position for tool to push piece.

        Args:
            piece_square: Square where piece is located
            push_direction: Direction to push ('north', 'south', 'east', 'west')

        Returns:
            (x, y) coordinates for tool positioning
        """
        if not self.tool_config:
            raise ValueError("Tool not configured")

        # Get piece square center
        piece_x, piece_y = self.board_config.square_center_xy(piece_square)

        # Calculate offset based on direction
        offset = self.tool_config.push_offset_mm

        if push_direction == 'north':
            # Position tool below piece (push upward)
            return (piece_x, piece_y - offset)
        elif push_direction == 'south':
            # Position tool above piece (push downward)
            return (piece_x, piece_y + offset)
        elif push_direction == 'east':
            # Position tool left of piece (push rightward)
            return (piece_x - offset, piece_y)
        elif push_direction == 'west':
            # Position tool right of piece (push leftward)
            return (piece_x + offset, piece_y)
        else:
            raise ValueError(f"Invalid push direction: {push_direction}")

    def get_push_distance(self, push_direction: str) -> float:
        """
        Get distance to push piece based on direction.

        Args:
            push_direction: Direction to push

        Returns:
            Distance in mm to push piece off board
        """
        # Push distance is typically one square width plus buffer
        square_size = self.board_config.width_mm / self.board_config.files
        return square_size + 20.0  # 20mm buffer to ensure piece falls off

    def mark_tool_picked_up(self):
        """Mark that tool is currently in gripper."""
        self.tool_in_hand = True

    def mark_tool_returned(self):
        """Mark that tool has been returned to holder."""
        self.tool_in_hand = False

    def is_tool_in_hand(self) -> bool:
        """Check if tool is currently in gripper."""
        return self.tool_in_hand


class ToolPusherSettings:
    """
    Default settings for tool pusher system.

    These can be customized per board configuration.
    """

    # Default pusher tool specifications
    DEFAULT_PUSHER_WIDTH = 50.0      # 50mm (~2 inches)
    DEFAULT_PUSHER_LENGTH = 100.0    # 100mm
    DEFAULT_GRIP_OFFSET = 30.0       # Grip 30mm from end
    DEFAULT_PUSH_OFFSET = 15.0       # Position 15mm behind piece

    # Default tool holder locations (corner squares)
    DEFAULT_HOLDER_8X8 = "a9"        # For 8x8 board (requires 9th rank)
    DEFAULT_HOLDER_10X10 = "a0"      # For 10x10 board (off-board square)

    # Push speeds
    TOOL_PICKUP_FEEDRATE = 1000      # mm/min for tool pickup
    PUSH_FEEDRATE = 300              # mm/min for pushing (slow and controlled)
    TOOL_RETURN_FEEDRATE = 1500      # mm/min for returning tool

    @classmethod
    def create_default_config(cls, board_config: BoardConfig, enabled: bool = False) -> ToolConfig:
        """
        Create default tool configuration for a board.

        Args:
            board_config: Board configuration
            enabled: Whether to enable tool by default

        Returns:
            ToolConfig with default settings
        """
        # Determine tool holder square based on board size
        if board_config.files == 8 and board_config.ranks == 8:
            holder = cls.DEFAULT_HOLDER_8X8
        elif board_config.files == 10 and board_config.ranks == 10:
            holder = cls.DEFAULT_HOLDER_10X10
        else:
            # Use off-board square in bottom-left
            holder = f"@0"

        return ToolConfig(
            tool_type=ToolType.PUSHER,
            holder_square=holder,
            width_mm=cls.DEFAULT_PUSHER_WIDTH,
            length_mm=cls.DEFAULT_PUSHER_LENGTH,
            grip_offset_mm=cls.DEFAULT_GRIP_OFFSET,
            push_offset_mm=cls.DEFAULT_PUSH_OFFSET,
            enabled=enabled
        )


def create_tool_pusher_manager(
    board_config: BoardConfig,
    enabled: bool = False
) -> ToolPusherManager:
    """
    Factory function to create tool pusher manager with default config.

    Args:
        board_config: Board configuration
        enabled: Whether to enable tool pusher

    Returns:
        ToolPusherManager instance
    """
    if enabled:
        tool_config = ToolPusherSettings.create_default_config(board_config, enabled=True)
        return ToolPusherManager(board_config, tool_config)
    else:
        return ToolPusherManager(board_config, tool_config=None)
