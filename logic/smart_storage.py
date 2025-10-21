"""
Smart Storage Management System

Automatically assigns storage squares for captured pieces using intelligent algorithms.
Integrates with TacticsQuest to track material and organization.
"""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

from logic.board_state import Piece, PieceType, PieceColor
from logic.board_map import BoardConfig, StorageLayout


class StorageStrategy(Enum):
    """Strategy for organizing captured pieces in storage."""
    NEAREST = "nearest"  # Assign to nearest available storage square
    BY_COLOR = "by_color"  # White left, black right
    BY_TYPE = "by_type"  # Group pawns together, pieces together
    CHRONOLOGICAL = "chronological"  # First captured goes to first square


@dataclass
class StorageSquare:
    """Represents a storage square with metadata."""
    square: str  # e.g., "a9"
    file_idx: int
    rank_idx: int
    occupied: bool = False
    piece: Optional[Piece] = None
    priority: int = 0  # Lower = higher priority for assignment
    reserved_for_color: Optional[PieceColor] = None
    reserved_for_type: Optional[PieceType] = None


@dataclass
class StorageMap:
    """Map of all storage squares and their current state."""
    squares: Dict[str, StorageSquare] = field(default_factory=dict)
    strategy: StorageStrategy = StorageStrategy.NEAREST

    def get_occupied_count(self) -> int:
        """Count occupied storage squares."""
        return sum(1 for sq in self.squares.values() if sq.occupied)

    def get_available_count(self) -> int:
        """Count available storage squares."""
        return sum(1 for sq in self.squares.values() if not sq.occupied)

    def get_occupied_squares(self) -> List[str]:
        """Get list of occupied storage square names."""
        return [sq.square for sq in self.squares.values() if sq.occupied]

    def get_available_squares(self) -> List[str]:
        """Get list of available storage square names."""
        return [sq.square for sq in self.squares.values() if not sq.occupied]


class SmartStorage:
    """
    Smart storage management system.

    Features:
    - Automatic storage square assignment
    - Multiple organization strategies
    - Visual storage map tracking
    - TacticsQuest integration for material tracking
    """

    def __init__(self, board_config: BoardConfig, strategy: StorageStrategy = StorageStrategy.BY_COLOR):
        self.board_config = board_config
        self.strategy = strategy
        self.storage_map = self._build_storage_map()

    def _build_storage_map(self) -> StorageMap:
        """Build initial storage map from board configuration."""
        storage_map = StorageMap(strategy=self.strategy)

        # Find all storage squares
        for file_idx in range(self.board_config.files):
            for rank_idx in range(self.board_config.ranks):
                if not self.board_config.is_playing_square(file_idx, rank_idx):
                    square = f"{chr(ord('a') + file_idx)}{rank_idx + 1}"

                    storage_square = StorageSquare(
                        square=square,
                        file_idx=file_idx,
                        rank_idx=rank_idx,
                        priority=self._calculate_priority(file_idx, rank_idx)
                    )

                    # Apply strategy-specific reservations
                    self._apply_strategy_reservations(storage_square)

                    storage_map.squares[square] = storage_square

        return storage_map

    def _calculate_priority(self, file_idx: int, rank_idx: int) -> int:
        """
        Calculate priority for storage square assignment.
        Lower number = higher priority.

        For TOP/BOTTOM: Prefer edges
        For PERIMETER: Prefer corners, then edges
        """
        if self.board_config.storage_layout == StorageLayout.TOP:
            # Prefer lower storage rank first (rank 9 over rank 10)
            # Within same rank, prefer center files
            rank_priority = rank_idx * 100
            file_distance_from_center = abs(file_idx - self.board_config.files / 2)
            return rank_priority + int(file_distance_from_center * 10)

        elif self.board_config.storage_layout == StorageLayout.BOTTOM:
            # Prefer higher storage rank first
            rank_priority = (self.board_config.ranks - rank_idx) * 100
            file_distance_from_center = abs(file_idx - self.board_config.files / 2)
            return rank_priority + int(file_distance_from_center * 10)

        elif self.board_config.storage_layout == StorageLayout.PERIMETER:
            # Prefer corners first, then edges
            # Check if corner
            is_corner = (
                (file_idx == 0 or file_idx == self.board_config.files - 1) and
                (rank_idx == 0 or rank_idx == self.board_config.ranks - 1)
            )
            if is_corner:
                return 0  # Highest priority

            # Edge squares
            return 50

        else:
            return 100

    def _apply_strategy_reservations(self, storage_square: StorageSquare):
        """Apply strategy-specific reservations to storage square."""
        if self.strategy == StorageStrategy.BY_COLOR:
            # Reserve left half for white, right half for black
            mid_file = self.board_config.files / 2
            if storage_square.file_idx < mid_file:
                storage_square.reserved_for_color = PieceColor.WHITE
            else:
                storage_square.reserved_for_color = PieceColor.BLACK

        elif self.strategy == StorageStrategy.BY_TYPE:
            # Reserve by rank (pawns bottom, pieces top)
            if self.board_config.storage_layout == StorageLayout.TOP:
                if storage_square.rank_idx == self.board_config.ranks - 2:  # Second-to-last rank
                    storage_square.reserved_for_type = PieceType.PAWN
            elif self.board_config.storage_layout == StorageLayout.PERIMETER:
                # Bottom edge for pawns, top edge for pieces
                if storage_square.rank_idx == 0:
                    storage_square.reserved_for_type = PieceType.PAWN

    def assign_storage_square(self, piece: Piece, from_square: str) -> Optional[str]:
        """
        Assign a storage square for a captured piece.

        Args:
            piece: The captured piece
            from_square: Where the piece was captured from

        Returns:
            Storage square name (e.g., "a9") or None if storage full
        """
        # Get available squares
        available = [
            sq for sq in self.storage_map.squares.values()
            if not sq.occupied
        ]

        if not available:
            return None  # Storage full!

        # Apply strategy
        if self.strategy == StorageStrategy.NEAREST:
            return self._assign_nearest(piece, from_square, available)

        elif self.strategy == StorageStrategy.BY_COLOR:
            return self._assign_by_color(piece, available)

        elif self.strategy == StorageStrategy.BY_TYPE:
            return self._assign_by_type(piece, available)

        elif self.strategy == StorageStrategy.CHRONOLOGICAL:
            return self._assign_chronological(available)

        # Default: Use priority
        available.sort(key=lambda sq: sq.priority)
        return available[0].square

    def _assign_nearest(self, piece: Piece, from_square: str, available: List[StorageSquare]) -> str:
        """Assign to nearest available storage square."""
        from_file = ord(from_square[0]) - ord('a')
        from_rank = int(from_square[1:]) - 1

        def distance(sq: StorageSquare) -> float:
            """Calculate Manhattan distance."""
            return abs(sq.file_idx - from_file) + abs(sq.rank_idx - from_rank)

        available.sort(key=distance)
        return available[0].square

    def _assign_by_color(self, piece: Piece, available: List[StorageSquare]) -> str:
        """Assign based on piece color (white left, black right)."""
        # Filter by color reservation if possible
        reserved = [sq for sq in available if sq.reserved_for_color == piece.color]

        if reserved:
            reserved.sort(key=lambda sq: sq.priority)
            return reserved[0].square

        # Fallback to any available
        available.sort(key=lambda sq: sq.priority)
        return available[0].square

    def _assign_by_type(self, piece: Piece, available: List[StorageSquare]) -> str:
        """Assign based on piece type."""
        # Filter by type reservation if possible
        reserved = [sq for sq in available if sq.reserved_for_type == piece.type]

        if reserved:
            reserved.sort(key=lambda sq: sq.priority)
            return reserved[0].square

        # Fallback to any available
        available.sort(key=lambda sq: sq.priority)
        return available[0].square

    def _assign_chronological(self, available: List[StorageSquare]) -> str:
        """Assign to first available square in priority order."""
        available.sort(key=lambda sq: sq.priority)
        return available[0].square

    def mark_occupied(self, square: str, piece: Piece):
        """Mark a storage square as occupied."""
        if square in self.storage_map.squares:
            sq = self.storage_map.squares[square]
            sq.occupied = True
            sq.piece = piece

    def mark_empty(self, square: str):
        """Mark a storage square as empty."""
        if square in self.storage_map.squares:
            sq = self.storage_map.squares[square]
            sq.occupied = False
            sq.piece = None

    def get_piece_at(self, square: str) -> Optional[Piece]:
        """Get piece at storage square."""
        if square in self.storage_map.squares:
            return self.storage_map.squares[square].piece
        return None

    def is_storage_square(self, square: str) -> bool:
        """Check if a square is a storage square."""
        return square in self.storage_map.squares

    def get_storage_stats(self) -> Dict:
        """Get storage statistics."""
        total = len(self.storage_map.squares)
        occupied = self.storage_map.get_occupied_count()
        available = self.storage_map.get_available_count()

        # Count by piece type
        piece_counts = {
            PieceColor.WHITE: {pt: 0 for pt in PieceType},
            PieceColor.BLACK: {pt: 0 for pt in PieceType}
        }

        for sq in self.storage_map.squares.values():
            if sq.occupied and sq.piece:
                piece_counts[sq.piece.color][sq.piece.type] += 1

        return {
            'total_squares': total,
            'occupied': occupied,
            'available': available,
            'utilization': (occupied / total * 100) if total > 0 else 0,
            'piece_counts': piece_counts,
            'strategy': self.strategy.value
        }

    def get_visual_map(self) -> List[List[str]]:
        """
        Get visual representation of storage map.
        Returns 2D grid showing piece symbols or empty spaces.
        """
        grid = []
        for rank_idx in range(self.board_config.ranks - 1, -1, -1):
            row = []
            for file_idx in range(self.board_config.files):
                square = f"{chr(ord('a') + file_idx)}{rank_idx + 1}"

                if square in self.storage_map.squares:
                    sq = self.storage_map.squares[square]
                    if sq.occupied and sq.piece:
                        row.append(str(sq.piece))  # FEN character
                    else:
                        row.append('·')  # Empty storage
                else:
                    row.append(' ')  # Playing square

            grid.append(row)

        return grid

    def sync_with_board_state(self, board_state):
        """
        Synchronize storage map with actual board state.
        Updates occupancy based on pieces currently in storage squares.

        Args:
            board_state: BoardState instance
        """
        for square_name, storage_sq in self.storage_map.squares.items():
            piece = board_state.get_piece_virtual(square_name)

            if piece:
                storage_sq.occupied = True
                storage_sq.piece = piece
            else:
                storage_sq.occupied = False
                storage_sq.piece = None

    def find_piece_in_storage(self, piece_type: PieceType, piece_color: PieceColor) -> Optional[str]:
        """
        Find a specific piece type in storage.
        Useful for promotions - need to retrieve a piece from storage.

        Args:
            piece_type: Type of piece to find
            piece_color: Color of piece to find

        Returns:
            Square name if found, None otherwise
        """
        for square_name, storage_sq in self.storage_map.squares.items():
            if (storage_sq.occupied and
                storage_sq.piece and
                storage_sq.piece.type == piece_type and
                storage_sq.piece.color == piece_color):
                return square_name

        return None

    def set_strategy(self, strategy: StorageStrategy):
        """Change storage assignment strategy."""
        self.strategy = strategy
        self.storage_map.strategy = strategy
        # Rebuild reservations
        for sq in self.storage_map.squares.values():
            sq.reserved_for_color = None
            sq.reserved_for_type = None
            self._apply_strategy_reservations(sq)
