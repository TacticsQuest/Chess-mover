"""
Board State Manager - Tracks physical and virtual piece positions.

This module manages the state of pieces on the physical chess machine,
distinguishing between:
- Virtual position: What pieces SHOULD be on the board (software state)
- Physical position: What pieces ARE actually on the board (hardware state)
"""

from typing import Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


class PieceType(Enum):
    """Chess piece types."""
    PAWN = 'p'
    KNIGHT = 'n'
    BISHOP = 'b'
    ROOK = 'r'
    QUEEN = 'q'
    KING = 'k'


class PieceColor(Enum):
    """Piece colors."""
    WHITE = 'w'
    BLACK = 'b'


@dataclass
class Piece:
    """Represents a chess piece."""
    type: PieceType
    color: PieceColor

    def __str__(self) -> str:
        """Return piece as FEN character."""
        char = self.type.value
        return char.upper() if self.color == PieceColor.WHITE else char

    @staticmethod
    def from_fen(fen_char: str) -> 'Piece':
        """Create piece from FEN character."""
        color = PieceColor.WHITE if fen_char.isupper() else PieceColor.BLACK
        piece_type = PieceType(fen_char.lower())
        return Piece(type=piece_type, color=color)


@dataclass
class BoardState:
    """
    Manages board state with separate tracking for virtual and physical positions.

    Attributes:
        virtual_position: Dict mapping square (e.g. 'e4') to Piece (software state)
        physical_position: Dict mapping square to Piece (actual hardware state)
        synced: Whether virtual and physical states match
        board_cfg: Optional board configuration for play area offset
    """
    virtual_position: Dict[str, Piece] = field(default_factory=dict)
    physical_position: Dict[str, Piece] = field(default_factory=dict)
    board_cfg: Optional['BoardConfig'] = None

    def is_synced(self) -> bool:
        """Check if virtual and physical positions match."""
        return self.virtual_position == self.physical_position

    def get_differences(self) -> Tuple[Set[str], Set[str], Set[str]]:
        """
        Get differences between virtual and physical positions.

        Returns:
            (to_add, to_remove, to_move):
                - to_add: Squares where pieces need to be added
                - to_remove: Squares where pieces need to be removed
                - to_move: Squares where pieces need to be moved
        """
        virtual_squares = set(self.virtual_position.keys())
        physical_squares = set(self.physical_position.keys())

        # Pieces to add (in virtual but not physical)
        to_add = virtual_squares - physical_squares

        # Pieces to remove (in physical but not virtual)
        to_remove = physical_squares - virtual_squares

        # Pieces that need to be moved (wrong piece on square)
        to_move = set()
        for square in virtual_squares & physical_squares:
            if self.virtual_position[square] != self.physical_position[square]:
                to_move.add(square)

        return to_add, to_remove, to_move

    def set_piece_virtual(self, square: str, piece: Optional[Piece]) -> None:
        """
        Set or remove a piece in virtual position.

        Args:
            square: Square notation (e.g. 'e4')
            piece: Piece to place, or None to remove
        """
        if piece is None:
            self.virtual_position.pop(square, None)
        else:
            self.virtual_position[square] = piece

    def set_piece_physical(self, square: str, piece: Optional[Piece]) -> None:
        """
        Set or remove a piece in physical position.

        Args:
            square: Square notation (e.g. 'e4')
            piece: Piece to place, or None to remove
        """
        if piece is None:
            self.physical_position.pop(square, None)
        else:
            self.physical_position[square] = piece

    def sync_physical_to_virtual(self) -> None:
        """Update physical position to match virtual position."""
        self.physical_position = self.virtual_position.copy()

    def sync_virtual_to_physical(self) -> None:
        """Update virtual position to match physical position."""
        self.virtual_position = self.physical_position.copy()

    def load_fen(self, fen: str, target: str = 'virtual') -> None:
        """
        Load position from FEN string.

        FEN notation always refers to the playing area (a1-h8).
        If board_cfg is set with a play_area, pieces are placed in the playing area,
        otherwise they're placed starting from a1.

        Args:
            fen: FEN string (only position part, before first space)
            target: 'virtual' or 'physical' - which position to update
        """
        position = {}

        # Get playing area offset (0, 0) if no board_cfg or no play_area
        file_offset = 0
        rank_offset = 0
        if self.board_cfg and self.board_cfg.play_area:
            file_offset = self.board_cfg.play_area.min_file
            rank_offset = self.board_cfg.play_area.min_rank

        # Parse FEN (e.g., "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
        ranks = fen.split(' ')[0].split('/')

        for rank_idx, rank in enumerate(ranks):
            file_idx = 0
            for char in rank:
                if char.isdigit():
                    # Empty squares
                    file_idx += int(char)
                else:
                    # Piece - FEN rank 8 is at rank_idx=0, FEN rank 1 is at rank_idx=7
                    # FEN file a is at file_idx=0, FEN file h is at file_idx=7
                    # Apply offset to place in playing area
                    physical_file = file_idx + file_offset
                    physical_rank = (7 - rank_idx) + rank_offset
                    square = f"{chr(ord('a') + physical_file)}{physical_rank + 1}"
                    piece = Piece.from_fen(char)
                    position[square] = piece
                    file_idx += 1

        if target == 'virtual':
            self.virtual_position = position
        elif target == 'physical':
            self.physical_position = position
        else:
            raise ValueError(f"Invalid target: {target}. Must be 'virtual' or 'physical'")

    def to_fen(self, source: str = 'virtual') -> str:
        """
        Export position to FEN string (position part only).

        Args:
            source: 'virtual' or 'physical' - which position to export

        Returns:
            FEN string (position part only, e.g., "rnbqkbnr/pppppppp/...")
        """
        position = self.virtual_position if source == 'virtual' else self.physical_position

        fen_parts = []
        for rank in range(8, 0, -1):  # Ranks 8 to 1
            empty_count = 0
            rank_str = ""

            for file_char in 'abcdefgh':
                square = f"{file_char}{rank}"
                piece = position.get(square)

                if piece is None:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        rank_str += str(empty_count)
                        empty_count = 0
                    rank_str += str(piece)

            if empty_count > 0:
                rank_str += str(empty_count)

            fen_parts.append(rank_str)

        return '/'.join(fen_parts)

    def get_piece_virtual(self, square: str) -> Optional[Piece]:
        """Get piece at square in virtual position."""
        return self.virtual_position.get(square)

    def get_piece_physical(self, square: str) -> Optional[Piece]:
        """Get piece at square in physical position."""
        return self.physical_position.get(square)

    def clear_virtual(self) -> None:
        """Clear all pieces from virtual position."""
        self.virtual_position.clear()

    def clear_physical(self) -> None:
        """Clear all pieces from physical position."""
        self.physical_position.clear()

    def reset_starting_position(self, target: str = 'virtual') -> None:
        """
        Reset to standard starting position.

        Args:
            target: 'virtual' or 'physical' - which position to reset
        """
        starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.load_fen(starting_fen, target)
