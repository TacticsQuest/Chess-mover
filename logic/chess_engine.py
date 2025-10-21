"""
Chess Engine Integration

Uses python-chess library for move validation, game state tracking,
and PGN parsing. Provides high-level interface for chess game management.
"""

import chess
import chess.pgn
from typing import List, Optional, Tuple
from dataclasses import dataclass
from io import StringIO


@dataclass
class MoveAnalysis:
    """Analysis of a chess move for physical execution."""
    move: chess.Move
    from_square: str  # e.g., "e2"
    to_square: str    # e.g., "e4"
    piece_type: str   # "pawn", "knight", "bishop", "rook", "queen", "king"
    is_capture: bool
    captured_square: Optional[str] = None  # Where captured piece is located
    is_castling: bool = False
    castling_rook_move: Optional[Tuple[str, str]] = None  # (from, to) for rook
    is_en_passant: bool = False
    en_passant_capture_square: Optional[str] = None
    is_promotion: bool = False
    promotion_piece: Optional[str] = None  # "queen", "rook", "bishop", "knight"


class ChessEngine:
    """
    Chess game engine using python-chess library.

    Handles all chess logic: move validation, game state, PGN parsing, etc.
    """

    def __init__(self):
        self.board = chess.Board()
        self.move_history: List[MoveAnalysis] = []

    def reset(self):
        """Reset to starting position."""
        self.board.reset()
        self.move_history = []

    def get_fen(self) -> str:
        """Get current position in FEN notation."""
        return self.board.fen()

    def set_fen(self, fen: str) -> bool:
        """
        Set position from FEN notation.

        Args:
            fen: FEN string

        Returns:
            True if FEN was valid and loaded
        """
        try:
            self.board.set_fen(fen)
            self.move_history = []
            return True
        except ValueError:
            return False

    def is_legal_move(self, move_str: str) -> bool:
        """
        Check if a move is legal in current position.

        Args:
            move_str: Move in UCI format (e.g., "e2e4") or SAN (e.g., "e4")

        Returns:
            True if move is legal
        """
        try:
            move = self._parse_move(move_str)
            return move in self.board.legal_moves
        except:
            return False

    def make_move(self, move_str: str) -> Optional[MoveAnalysis]:
        """
        Make a move on the board.

        Args:
            move_str: Move in UCI format (e.g., "e2e4") or SAN (e.g., "e4", "Nf3")

        Returns:
            MoveAnalysis if move was legal and executed, None otherwise
        """
        try:
            move = self._parse_move(move_str)

            if move not in self.board.legal_moves:
                return None

            # Analyze move before making it
            analysis = self._analyze_move(move)

            # Make the move
            self.board.push(move)

            # Record in history
            self.move_history.append(analysis)

            return analysis

        except Exception as e:
            print(f"[CHESS] Error making move {move_str}: {e}")
            return None

    def undo_move(self) -> bool:
        """
        Undo the last move.

        Returns:
            True if a move was undone
        """
        if len(self.board.move_stack) > 0:
            self.board.pop()
            if self.move_history:
                self.move_history.pop()
            return True
        return False

    def get_legal_moves(self) -> List[str]:
        """
        Get list of all legal moves in current position.

        Returns:
            List of moves in UCI format
        """
        return [move.uci() for move in self.board.legal_moves]

    def is_checkmate(self) -> bool:
        """Check if current position is checkmate."""
        return self.board.is_checkmate()

    def is_stalemate(self) -> bool:
        """Check if current position is stalemate."""
        return self.board.is_stalemate()

    def is_game_over(self) -> bool:
        """Check if game is over (checkmate, stalemate, or insufficient material)."""
        return self.board.is_game_over()

    def get_result(self) -> str:
        """
        Get game result.

        Returns:
            "1-0" (White wins), "0-1" (Black wins), "1/2-1/2" (Draw), or "*" (Ongoing)
        """
        if self.is_checkmate():
            return "1-0" if self.board.turn == chess.BLACK else "0-1"
        elif self.is_stalemate() or self.board.is_insufficient_material():
            return "1/2-1/2"
        else:
            return "*"

    def load_pgn(self, pgn_string: str) -> bool:
        """
        Load a game from PGN notation.

        Args:
            pgn_string: PGN string (can include headers and moves)

        Returns:
            True if PGN was loaded successfully
        """
        try:
            # Strip leading whitespace from each line to handle indented PGN strings
            # (e.g., when PGN is indented in source code)
            lines = pgn_string.split('\n')
            cleaned_lines = [line.lstrip() for line in lines]
            cleaned_pgn = '\n'.join(cleaned_lines)

            pgn = StringIO(cleaned_pgn)
            game = chess.pgn.read_game(pgn)

            if game is None:
                return False

            # Reset board
            self.reset()

            # Play through all moves
            for move in game.mainline_moves():
                analysis = self._analyze_move(move)
                self.board.push(move)
                self.move_history.append(analysis)

            return True

        except Exception as e:
            print(f"[CHESS] Error loading PGN: {e}")
            return False

    def get_pgn(self) -> str:
        """
        Export current game as PGN.

        Returns:
            PGN string
        """
        game = chess.pgn.Game()

        # Add headers
        game.headers["Event"] = "Chess Mover Machine Game"
        game.headers["Result"] = self.get_result()

        # Add moves
        node = game
        self.board.reset()  # Temporarily reset to replay moves
        for analysis in self.move_history:
            node = node.add_variation(analysis.move)
            self.board.push(analysis.move)

        # Restore board state
        self.board.reset()
        for analysis in self.move_history:
            self.board.push(analysis.move)

        return str(game)

    def get_move_list_san(self) -> List[str]:
        """
        Get move history in Standard Algebraic Notation.

        Returns:
            List of moves in SAN format (e.g., ["e4", "e5", "Nf3"])
        """
        sans = []
        temp_board = chess.Board()
        for analysis in self.move_history:
            sans.append(temp_board.san(analysis.move))
            temp_board.push(analysis.move)
        return sans

    def _parse_move(self, move_str: str) -> chess.Move:
        """
        Parse move string to chess.Move object.

        Args:
            move_str: Move in UCI (e.g., "e2e4") or SAN (e.g., "e4") format

        Returns:
            chess.Move object

        Raises:
            ValueError: If move string is invalid
        """
        # Try UCI format first
        try:
            return chess.Move.from_uci(move_str)
        except:
            pass

        # Try SAN format
        try:
            return self.board.parse_san(move_str)
        except:
            raise ValueError(f"Invalid move: {move_str}")

    def _analyze_move(self, move: chess.Move) -> MoveAnalysis:
        """
        Analyze a move for physical execution planning.

        Args:
            move: chess.Move object

        Returns:
            MoveAnalysis with details needed for gantry execution
        """
        from_square = chess.square_name(move.from_square)
        to_square = chess.square_name(move.to_square)

        piece = self.board.piece_at(move.from_square)
        piece_type = chess.piece_name(piece.piece_type) if piece else "unknown"

        # Check for capture
        is_capture = self.board.is_capture(move)
        captured_square = to_square if is_capture else None

        # Check for castling
        is_castling = self.board.is_castling(move)
        castling_rook_move = None
        if is_castling:
            # Determine rook movement
            if move.to_square > move.from_square:  # Kingside
                rook_from = chess.square_name(move.from_square + 3)
                rook_to = chess.square_name(move.from_square + 1)
            else:  # Queenside
                rook_from = chess.square_name(move.from_square - 4)
                rook_to = chess.square_name(move.from_square - 1)
            castling_rook_move = (rook_from, rook_to)

        # Check for en passant
        is_en_passant = self.board.is_en_passant(move)
        en_passant_capture_square = None
        if is_en_passant:
            # Captured pawn is on the same file as destination, same rank as source
            captured_pawn_square = chess.square(
                chess.square_file(move.to_square),
                chess.square_rank(move.from_square)
            )
            en_passant_capture_square = chess.square_name(captured_pawn_square)

        # Check for promotion
        is_promotion = move.promotion is not None
        promotion_piece = None
        if is_promotion:
            promotion_piece = chess.piece_name(move.promotion)

        return MoveAnalysis(
            move=move,
            from_square=from_square,
            to_square=to_square,
            piece_type=piece_type,
            is_capture=is_capture and not is_en_passant,  # Regular capture
            captured_square=captured_square if (is_capture and not is_en_passant) else None,
            is_castling=is_castling,
            castling_rook_move=castling_rook_move,
            is_en_passant=is_en_passant,
            en_passant_capture_square=en_passant_capture_square,
            is_promotion=is_promotion,
            promotion_piece=promotion_piece
        )

    def get_board_state(self) -> dict:
        """
        Get current board state as a dictionary.

        Returns:
            Dict with piece positions for all 64 squares
        """
        state = {}
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            square_name = chess.square_name(square)
            if piece:
                color = "white" if piece.color == chess.WHITE else "black"
                piece_type = chess.piece_name(piece.piece_type)
                state[square_name] = f"{color}_{piece_type}"
            else:
                state[square_name] = None
        return state

    def __str__(self) -> str:
        """ASCII representation of current board."""
        return str(self.board)
