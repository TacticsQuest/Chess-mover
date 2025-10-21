"""
Chess Game State Management

Tracks the current state of a chess game including piece positions,
move history, and game status. Provides move validation and execution.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Tuple, Dict
import re


class PieceType(Enum):
    """Chess piece types."""
    KING = 'k'
    QUEEN = 'q'
    ROOK = 'r'
    BISHOP = 'b'
    KNIGHT = 'n'
    PAWN = 'p'


class PieceColor(Enum):
    """Chess piece colors."""
    WHITE = 'w'
    BLACK = 'b'


@dataclass
class Piece:
    """Represents a chess piece."""
    type: PieceType
    color: PieceColor

    def __str__(self) -> str:
        """String representation (e.g., 'wK', 'bP')."""
        symbol = self.type.value.upper() if self.color == PieceColor.WHITE else self.type.value
        return symbol

    @staticmethod
    def from_symbol(symbol: str) -> Optional['Piece']:
        """Create piece from FEN symbol (e.g., 'K', 'p', 'N')."""
        if not symbol or symbol == ' ':
            return None

        color = PieceColor.WHITE if symbol.isupper() else PieceColor.BLACK
        piece_map = {
            'k': PieceType.KING,
            'q': PieceType.QUEEN,
            'r': PieceType.ROOK,
            'b': PieceType.BISHOP,
            'n': PieceType.KNIGHT,
            'p': PieceType.PAWN,
        }

        piece_type = piece_map.get(symbol.lower())
        if piece_type:
            return Piece(piece_type, color)
        return None


@dataclass
class Move:
    """Represents a chess move."""
    from_square: str  # e.g., "e2"
    to_square: str    # e.g., "e4"
    piece: Piece
    captured_piece: Optional[Piece] = None
    is_castling: bool = False
    is_en_passant: bool = False
    promotion_piece: Optional[PieceType] = None

    # For castling, stores the rook's move
    rook_from: Optional[str] = None
    rook_to: Optional[str] = None

    def __str__(self) -> str:
        """String representation."""
        if self.is_castling:
            return "O-O" if self.to_square in ['g1', 'g8'] else "O-O-O"

        move_str = f"{self.from_square}-{self.to_square}"
        if self.captured_piece:
            move_str += f"x{self.captured_piece}"
        if self.promotion_piece:
            move_str += f"={self.promotion_piece.value.upper()}"
        return move_str


class ChessBoard:
    """
    Represents a chess board state.

    Board coordinates:
    - Files: a-h (0-7)
    - Ranks: 1-8 (0-7)
    - a1 is (0,0), h8 is (7,7)
    """

    def __init__(self):
        # 8x8 board: board[rank][file] = Piece or None
        self.board: List[List[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        self.move_history: List[Move] = []
        self.current_turn = PieceColor.WHITE

        # Castling rights
        self.white_can_castle_kingside = True
        self.white_can_castle_queenside = True
        self.black_can_castle_kingside = True
        self.black_can_castle_queenside = True

        # En passant target square (if pawn just moved two squares)
        self.en_passant_target: Optional[str] = None

        # Halfmove clock (for 50-move rule)
        self.halfmove_clock = 0

        # Fullmove number
        self.fullmove_number = 1

    def setup_starting_position(self):
        """Set up the standard chess starting position."""
        # Clear board
        self.board = [[None for _ in range(8)] for _ in range(8)]

        # White pieces (rank 0 and 1)
        self.board[0][0] = Piece(PieceType.ROOK, PieceColor.WHITE)
        self.board[0][1] = Piece(PieceType.KNIGHT, PieceColor.WHITE)
        self.board[0][2] = Piece(PieceType.BISHOP, PieceColor.WHITE)
        self.board[0][3] = Piece(PieceType.QUEEN, PieceColor.WHITE)
        self.board[0][4] = Piece(PieceType.KING, PieceColor.WHITE)
        self.board[0][5] = Piece(PieceType.BISHOP, PieceColor.WHITE)
        self.board[0][6] = Piece(PieceType.KNIGHT, PieceColor.WHITE)
        self.board[0][7] = Piece(PieceType.ROOK, PieceColor.WHITE)
        for file in range(8):
            self.board[1][file] = Piece(PieceType.PAWN, PieceColor.WHITE)

        # Black pieces (rank 6 and 7)
        for file in range(8):
            self.board[6][file] = Piece(PieceType.PAWN, PieceColor.BLACK)
        self.board[7][0] = Piece(PieceType.ROOK, PieceColor.BLACK)
        self.board[7][1] = Piece(PieceType.KNIGHT, PieceColor.BLACK)
        self.board[7][2] = Piece(PieceType.BISHOP, PieceColor.BLACK)
        self.board[7][3] = Piece(PieceType.QUEEN, PieceColor.BLACK)
        self.board[7][4] = Piece(PieceType.KING, PieceColor.BLACK)
        self.board[7][5] = Piece(PieceType.BISHOP, PieceColor.BLACK)
        self.board[7][6] = Piece(PieceType.KNIGHT, PieceColor.BLACK)
        self.board[7][7] = Piece(PieceType.ROOK, PieceColor.BLACK)

        # Reset game state
        self.current_turn = PieceColor.WHITE
        self.move_history = []
        self.white_can_castle_kingside = True
        self.white_can_castle_queenside = True
        self.black_can_castle_kingside = True
        self.black_can_castle_queenside = True
        self.en_passant_target = None
        self.halfmove_clock = 0
        self.fullmove_number = 1

    @staticmethod
    def square_to_coords(square: str) -> Tuple[int, int]:
        """
        Convert square notation to (rank, file) coordinates.

        Args:
            square: Square in algebraic notation (e.g., "e4")

        Returns:
            (rank, file) tuple where rank and file are 0-7
        """
        file = ord(square[0].lower()) - ord('a')
        rank = int(square[1]) - 1
        return rank, file

    @staticmethod
    def coords_to_square(rank: int, file: int) -> str:
        """
        Convert (rank, file) coordinates to square notation.

        Args:
            rank: Rank (0-7)
            file: File (0-7)

        Returns:
            Square in algebraic notation (e.g., "e4")
        """
        return f"{chr(ord('a') + file)}{rank + 1}"

    def get_piece(self, square: str) -> Optional[Piece]:
        """Get piece at a square."""
        rank, file = self.square_to_coords(square)
        return self.board[rank][file]

    def set_piece(self, square: str, piece: Optional[Piece]):
        """Place piece at a square."""
        rank, file = self.square_to_coords(square)
        self.board[rank][file] = piece

    def remove_piece(self, square: str) -> Optional[Piece]:
        """Remove and return piece at a square."""
        piece = self.get_piece(square)
        self.set_piece(square, None)
        return piece

    def make_move(self, move: Move) -> bool:
        """
        Execute a move on the board.

        Args:
            move: Move to execute

        Returns:
            True if move was executed successfully
        """
        # Remove piece from source square
        piece = self.remove_piece(move.from_square)
        if not piece:
            return False

        # Handle capture
        if move.captured_piece:
            self.remove_piece(move.to_square)

        # Handle en passant
        if move.is_en_passant:
            # Remove captured pawn
            from_rank, from_file = self.square_to_coords(move.from_square)
            to_rank, to_file = self.square_to_coords(move.to_square)
            captured_pawn_square = self.coords_to_square(from_rank, to_file)
            self.remove_piece(captured_pawn_square)

        # Place piece at destination
        if move.promotion_piece:
            # Promote pawn
            promoted_piece = Piece(move.promotion_piece, piece.color)
            self.set_piece(move.to_square, promoted_piece)
        else:
            self.set_piece(move.to_square, piece)

        # Handle castling
        if move.is_castling and move.rook_from and move.rook_to:
            rook = self.remove_piece(move.rook_from)
            if rook:
                self.set_piece(move.rook_to, rook)

        # Update castling rights
        if piece.type == PieceType.KING:
            if piece.color == PieceColor.WHITE:
                self.white_can_castle_kingside = False
                self.white_can_castle_queenside = False
            else:
                self.black_can_castle_kingside = False
                self.black_can_castle_queenside = False

        if piece.type == PieceType.ROOK:
            if move.from_square == 'a1':
                self.white_can_castle_queenside = False
            elif move.from_square == 'h1':
                self.white_can_castle_kingside = False
            elif move.from_square == 'a8':
                self.black_can_castle_queenside = False
            elif move.from_square == 'h8':
                self.black_can_castle_kingside = False

        # Update en passant target
        self.en_passant_target = None
        if piece.type == PieceType.PAWN:
            from_rank, _ = self.square_to_coords(move.from_square)
            to_rank, to_file = self.square_to_coords(move.to_square)
            if abs(to_rank - from_rank) == 2:
                # Pawn moved two squares, set en passant target
                ep_rank = (from_rank + to_rank) // 2
                self.en_passant_target = self.coords_to_square(ep_rank, to_file)

        # Update move counters
        if piece.type == PieceType.PAWN or move.captured_piece:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        if self.current_turn == PieceColor.BLACK:
            self.fullmove_number += 1

        # Switch turn
        self.current_turn = PieceColor.BLACK if self.current_turn == PieceColor.WHITE else PieceColor.WHITE

        # Record move
        self.move_history.append(move)

        return True

    def to_fen(self) -> str:
        """
        Export board state to FEN (Forsyth-Edwards Notation).

        Returns:
            FEN string representing current position
        """
        # Piece placement
        fen_parts = []
        for rank in range(7, -1, -1):  # Start from rank 8
            empty_count = 0
            rank_str = ""
            for file in range(8):
                piece = self.board[rank][file]
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

        fen = "/".join(fen_parts)

        # Active color
        fen += " " + ("w" if self.current_turn == PieceColor.WHITE else "b")

        # Castling rights
        castling = ""
        if self.white_can_castle_kingside:
            castling += "K"
        if self.white_can_castle_queenside:
            castling += "Q"
        if self.black_can_castle_kingside:
            castling += "k"
        if self.black_can_castle_queenside:
            castling += "q"
        fen += " " + (castling if castling else "-")

        # En passant target
        fen += " " + (self.en_passant_target if self.en_passant_target else "-")

        # Halfmove clock and fullmove number
        fen += f" {self.halfmove_clock} {self.fullmove_number}"

        return fen

    def from_fen(self, fen: str) -> bool:
        """
        Load board state from FEN notation.

        Args:
            fen: FEN string

        Returns:
            True if FEN was parsed successfully
        """
        try:
            parts = fen.split()
            if len(parts) < 4:
                return False

            # Clear board
            self.board = [[None for _ in range(8)] for _ in range(8)]

            # Parse piece placement
            ranks = parts[0].split('/')
            for rank_idx, rank_str in enumerate(ranks):
                rank = 7 - rank_idx  # FEN starts from rank 8
                file = 0
                for char in rank_str:
                    if char.isdigit():
                        file += int(char)
                    else:
                        piece = Piece.from_symbol(char)
                        if piece:
                            self.board[rank][file] = piece
                        file += 1

            # Parse active color
            self.current_turn = PieceColor.WHITE if parts[1] == 'w' else PieceColor.BLACK

            # Parse castling rights
            castling = parts[2]
            self.white_can_castle_kingside = 'K' in castling
            self.white_can_castle_queenside = 'Q' in castling
            self.black_can_castle_kingside = 'k' in castling
            self.black_can_castle_queenside = 'q' in castling

            # Parse en passant target
            self.en_passant_target = parts[3] if parts[3] != '-' else None

            # Parse halfmove clock and fullmove number
            if len(parts) >= 5:
                self.halfmove_clock = int(parts[4])
            if len(parts) >= 6:
                self.fullmove_number = int(parts[5])

            return True

        except Exception:
            return False

    def __str__(self) -> str:
        """String representation of the board (ASCII art)."""
        result = []
        result.append("  +---+---+---+---+---+---+---+---+")
        for rank in range(7, -1, -1):
            row = f"{rank + 1} |"
            for file in range(8):
                piece = self.board[rank][file]
                symbol = f" {piece} " if piece else "   "
                row += symbol + "|"
            result.append(row)
            result.append("  +---+---+---+---+---+---+---+---+")
        result.append("    a   b   c   d   e   f   g   h")
        return "\n".join(result)
