"""
Edge Push System

Handles captured piece removal via edge pushing for boards without dedicated storage areas.
Finds empty edge squares and pushes pieces off the board in a controlled manner.
"""

from dataclasses import dataclass
from typing import Optional, Tuple, List
from enum import Enum

from logic.board_map import BoardConfig
from logic.board_state import Piece, BoardState


class EdgeDirection(Enum):
    """Direction to push piece off board."""
    NORTH = "north"  # Push up off top edge
    SOUTH = "south"  # Push down off bottom edge
    EAST = "east"    # Push right off right edge
    WEST = "west"    # Push left off left edge


@dataclass
class EdgePushLocation:
    """Represents a location for edge pushing."""
    edge_square: str           # Square on edge where piece is placed
    push_square: str           # Adjacent square (off-board) to push from
    direction: EdgeDirection   # Direction to push
    priority: int             # Priority (corners = 1, edges = 2)
    occupied: bool = False    # Whether this location is currently occupied


class EdgePushManager:
    """
    Manages edge push locations for boards without storage areas.

    Tracks available edge squares and coordinates piece removal via pushing.
    """

    def __init__(self, board_config: BoardConfig):
        """
        Initialize edge push manager.

        Args:
            board_config: Board configuration
        """
        self.board_config = board_config
        self.edge_locations: List[EdgePushLocation] = []
        self._build_edge_locations()

    def _build_edge_locations(self):
        """Build list of available edge push locations."""
        files = self.board_config.files
        ranks = self.board_config.ranks

        # Track all edge squares (a-file, h-file, rank 1, rank 8)
        # Priority: corners first (1), then edges (2)

        # Top edge (rank 8/highest)
        for file_idx in range(files):
            square = f"{chr(ord('a') + file_idx)}{ranks}"
            is_corner = (file_idx == 0 or file_idx == files - 1)
            priority = 1 if is_corner else 2

            # Push square is one rank higher (off-board)
            push_square = f"{chr(ord('a') + file_idx)}{ranks + 1}"

            self.edge_locations.append(EdgePushLocation(
                edge_square=square,
                push_square=push_square,
                direction=EdgeDirection.NORTH,
                priority=priority
            ))

        # Bottom edge (rank 1)
        for file_idx in range(files):
            square = f"{chr(ord('a') + file_idx)}1"
            is_corner = (file_idx == 0 or file_idx == files - 1)
            priority = 1 if is_corner else 2

            # Push square is one rank lower (off-board)
            push_square = f"{chr(ord('a') + file_idx)}0"

            self.edge_locations.append(EdgePushLocation(
                edge_square=square,
                push_square=push_square,
                direction=EdgeDirection.SOUTH,
                priority=priority
            ))

        # Right edge (h-file/rightmost, excluding corners already added)
        for rank_idx in range(2, ranks):  # Skip rank 1 and top rank (corners)
            square = f"{chr(ord('a') + files - 1)}{rank_idx}"

            # Push square is one file to the right (off-board)
            push_square = f"{chr(ord('a') + files)}{rank_idx}"

            self.edge_locations.append(EdgePushLocation(
                edge_square=square,
                push_square=push_square,
                direction=EdgeDirection.EAST,
                priority=2
            ))

        # Left edge (a-file, excluding corners already added)
        for rank_idx in range(2, ranks):  # Skip rank 1 and top rank (corners)
            square = f"a{rank_idx}"

            # Push square is one file to the left (off-board)
            # Use file '@' (one before 'a')
            push_square = f"@{rank_idx}"

            self.edge_locations.append(EdgePushLocation(
                edge_square=square,
                push_square=push_square,
                direction=EdgeDirection.WEST,
                priority=2
            ))

    def find_edge_push_location(self, board_state: BoardState, from_square: str) -> Optional[EdgePushLocation]:
        """
        Find best available edge push location.

        Args:
            board_state: Current board state to check occupancy
            from_square: Square where piece is being captured (for distance calculation)

        Returns:
            EdgePushLocation or None if no location available
        """
        # Get available locations (edge square is empty on board)
        available = [
            loc for loc in self.edge_locations
            if not loc.occupied and board_state.get_piece(loc.edge_square) is None
        ]

        if not available:
            return None

        # Sort by priority (corners first), then by distance to from_square
        from_file_idx = ord(from_square[0]) - ord('a')
        from_rank_idx = int(from_square[1:]) - 1

        def location_score(loc: EdgePushLocation) -> Tuple[int, float]:
            """Calculate location score (priority, distance)."""
            edge_file_idx = ord(loc.edge_square[0]) - ord('a')
            edge_rank_idx = int(loc.edge_square[1:]) - 1

            # Manhattan distance
            distance = abs(edge_file_idx - from_file_idx) + abs(edge_rank_idx - from_rank_idx)

            return (loc.priority, distance)

        # Select best location (lowest priority number, then shortest distance)
        best_location = min(available, key=location_score)
        return best_location

    def mark_occupied(self, edge_square: str):
        """
        Mark an edge location as occupied.

        Args:
            edge_square: Edge square name
        """
        for loc in self.edge_locations:
            if loc.edge_square == edge_square:
                loc.occupied = True
                break

    def mark_empty(self, edge_square: str):
        """
        Mark an edge location as empty.

        Args:
            edge_square: Edge square name
        """
        for loc in self.edge_locations:
            if loc.edge_square == edge_square:
                loc.occupied = False
                break

    def reset(self):
        """Reset all edge locations to empty."""
        for loc in self.edge_locations:
            loc.occupied = False

    def get_available_count(self) -> int:
        """Get count of available edge push locations."""
        return sum(1 for loc in self.edge_locations if not loc.occupied)

    def get_total_count(self) -> int:
        """Get total count of edge push locations."""
        return len(self.edge_locations)

    def get_utilization(self) -> float:
        """Get utilization percentage (0-100)."""
        if not self.edge_locations:
            return 0.0
        occupied = sum(1 for loc in self.edge_locations if loc.occupied)
        return (occupied / len(self.edge_locations)) * 100

    def get_push_coordinates(self, edge_square: str) -> Optional[Tuple[str, str, EdgeDirection]]:
        """
        Get push coordinates for an edge square.

        Args:
            edge_square: Edge square name

        Returns:
            (edge_square, push_square, direction) or None
        """
        for loc in self.edge_locations:
            if loc.edge_square == edge_square:
                return (loc.edge_square, loc.push_square, loc.direction)
        return None
