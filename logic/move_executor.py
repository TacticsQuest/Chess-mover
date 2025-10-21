"""
Move Execution Planner

Converts chess moves into gantry action sequences.
Handles piece pickup, movement, captures, and special moves.
Integrates with Smart Storage for automatic captured piece organization.
"""

from dataclasses import dataclass
from typing import List, Optional, Callable
from enum import Enum
import chess

from logic.chess_engine import ChessEngine, MoveAnalysis
from logic.board_map import BoardConfig
from logic.profiles import Settings
from logic.smart_storage import SmartStorage, StorageStrategy
from logic.board_state import Piece, PieceType, PieceColor, BoardState
from logic.edge_push import EdgePushManager, EdgePushLocation
from logic.tool_pusher import ToolPusherManager, ToolConfig


class ActionType(Enum):
    """Types of gantry actions."""
    MOVE_TO = "move_to"          # Move gantry to square
    LIFT_UP = "lift_up"          # Raise lift mechanism
    LIFT_DOWN = "lift_down"      # Lower lift mechanism
    GRIP_OPEN = "grip_open"      # Open gripper
    GRIP_CLOSE = "grip_close"    # Close gripper
    WAIT = "wait"                # Wait/pause
    PUSH = "push"                # Push piece (for edge push)


@dataclass
class GantryAction:
    """Represents a single gantry action."""
    action_type: ActionType
    square: Optional[str] = None  # Target square for MOVE_TO
    duration_ms: int = 0          # Duration for WAIT actions
    description: str = ""         # Human-readable description
    push_direction: Optional[str] = None  # Direction for PUSH actions
    push_distance_mm: float = 0.0  # Distance for PUSH actions
    feedrate: Optional[int] = None  # Custom feedrate for this action

    def __str__(self) -> str:
        if self.action_type == ActionType.MOVE_TO:
            return f"Move to {self.square}"
        elif self.action_type == ActionType.WAIT:
            return f"Wait {self.duration_ms}ms"
        elif self.action_type == ActionType.PUSH:
            return f"Push {self.push_direction} {self.push_distance_mm}mm"
        else:
            return self.action_type.value.replace('_', ' ').title()


class MoveExecutor:
    """
    Plans and executes chess moves as gantry action sequences.

    Converts high-level chess moves into low-level gantry commands:
    - Regular moves: pickup → travel → putdown
    - Captures: remove captured piece → pickup → travel → putdown
    - Castling: king move + rook move
    - En passant: remove pawn → pickup → travel → putdown
    """

    def __init__(
        self,
        chess_engine: ChessEngine,
        board_config: BoardConfig,
        settings: Settings,
        smart_storage: SmartStorage,
        board_state: Optional[BoardState] = None,
        edge_push_enabled: bool = False,
        tool_pusher_config: Optional[ToolConfig] = None
    ):
        self.chess_engine = chess_engine
        self.board_config = board_config
        self.settings = settings
        self.smart_storage = smart_storage
        self.board_state = board_state

        # Advanced capture strategies (disabled by default)
        self.edge_push_manager = EdgePushManager(board_config) if edge_push_enabled else None
        self.tool_pusher_manager = ToolPusherManager(board_config, tool_pusher_config) if tool_pusher_config else None


    def plan_move(self, move_str: str) -> Optional[List[GantryAction]]:
        """
        Plan gantry action sequence for a chess move.

        Args:
            move_str: Move in UCI or SAN format (e.g., "e2e4" or "e4")

        Returns:
            List of GantryAction objects, or None if move is illegal
        """
        # Make the move in the chess engine
        analysis = self.chess_engine.make_move(move_str)

        if analysis is None:
            return None  # Illegal move

        # Plan action sequence based on move type
        if analysis.is_castling:
            return self._plan_castling(analysis)
        elif analysis.is_en_passant:
            return self._plan_en_passant(analysis)
        elif analysis.is_capture:
            return self._plan_capture(analysis)
        else:
            return self._plan_normal_move(analysis)

    def _plan_normal_move(self, analysis: MoveAnalysis) -> List[GantryAction]:
        """
        Plan action sequence for a normal (non-capture) move.

        Sequence:
        1. Move to source square
        2. Lower lift
        3. Close gripper
        4. Raise lift
        5. Move to destination square
        6. Lower lift
        7. Open gripper
        8. Raise lift
        """
        actions = [
            GantryAction(ActionType.MOVE_TO, square=analysis.from_square,
                        description=f"Move to {analysis.from_square} ({analysis.piece_type})"),
            GantryAction(ActionType.LIFT_DOWN,
                        description="Lower to grab piece"),
            GantryAction(ActionType.GRIP_CLOSE,
                        description=f"Grip {analysis.piece_type}"),
            GantryAction(ActionType.WAIT, duration_ms=200,
                        description="Stabilize grip"),
            GantryAction(ActionType.LIFT_UP,
                        description="Lift piece"),
            GantryAction(ActionType.MOVE_TO, square=analysis.to_square,
                        description=f"Travel to {analysis.to_square}"),
            GantryAction(ActionType.LIFT_DOWN,
                        description="Lower piece"),
            GantryAction(ActionType.GRIP_OPEN,
                        description="Release piece"),
            GantryAction(ActionType.LIFT_UP,
                        description="Raise gripper"),
        ]

        return actions

    def _plan_capture(self, analysis: MoveAnalysis) -> List[GantryAction]:
        """
        Plan action sequence for a capture move.

        Sequence:
        1. Remove captured piece to storage
        2. Execute normal move for capturing piece
        """
        actions = []

        # Step 1: Remove captured piece
        if analysis.captured_square:
            # Determine captured piece color (opposite of current turn)
            captured_color = PieceColor.BLACK if self.chess_engine.board.turn == chess.WHITE else PieceColor.WHITE

            # Get piece type from the board before the move
            captured_piece_type = self._get_piece_type_from_analysis(analysis)

            # Create Piece object
            captured_piece = Piece(captured_piece_type, captured_color)

            # Assign storage square using Smart Storage
            storage_square = self.smart_storage.assign_storage_square(
                captured_piece,
                analysis.captured_square
            )

            if storage_square is None:
                # Storage full - log warning but continue
                # TODO: Handle storage full scenario (alert user, auto-cleanup, etc.)
                storage_square = "storage_full_fallback"

            actions.extend([
                GantryAction(ActionType.MOVE_TO, square=analysis.captured_square,
                            description=f"Move to captured {captured_piece_type.value} at {analysis.captured_square}"),
                GantryAction(ActionType.LIFT_DOWN,
                            description="Lower to grab captured piece"),
                GantryAction(ActionType.GRIP_CLOSE,
                            description=f"Grip captured {captured_piece_type.value}"),
                GantryAction(ActionType.WAIT, duration_ms=200,
                            description="Stabilize grip"),
                GantryAction(ActionType.LIFT_UP,
                            description="Lift captured piece"),
                GantryAction(ActionType.MOVE_TO, square=storage_square,
                            description=f"Move to storage {storage_square}"),
                GantryAction(ActionType.LIFT_DOWN,
                            description="Lower captured piece"),
                GantryAction(ActionType.GRIP_OPEN,
                            description="Release captured piece"),
                GantryAction(ActionType.LIFT_UP,
                            description="Raise gripper"),
            ])

            # Mark storage square as occupied
            if storage_square != "storage_full_fallback":
                self.smart_storage.mark_occupied(storage_square, captured_piece)

        # Step 2: Move capturing piece
        actions.extend(self._plan_normal_move(analysis))

        return actions

    def _plan_en_passant(self, analysis: MoveAnalysis) -> List[GantryAction]:
        """
        Plan action sequence for en passant capture.

        Sequence:
        1. Remove captured pawn (different square than destination!)
        2. Move attacking pawn
        """
        actions = []

        # Step 1: Remove captured pawn
        if analysis.en_passant_capture_square:
            # Determine captured pawn color (opposite of current turn)
            captured_color = PieceColor.BLACK if self.chess_engine.board.turn == chess.WHITE else PieceColor.WHITE

            # Create Piece object (en passant always captures a pawn)
            captured_piece = Piece(PieceType.PAWN, captured_color)

            # Assign storage square using Smart Storage
            storage_square = self.smart_storage.assign_storage_square(
                captured_piece,
                analysis.en_passant_capture_square
            )

            if storage_square is None:
                # Storage full - log warning but continue
                storage_square = "storage_full_fallback"

            actions.extend([
                GantryAction(ActionType.MOVE_TO, square=analysis.en_passant_capture_square,
                            description=f"Move to captured pawn at {analysis.en_passant_capture_square}"),
                GantryAction(ActionType.LIFT_DOWN,
                            description="Lower to grab captured pawn"),
                GantryAction(ActionType.GRIP_CLOSE,
                            description="Grip captured pawn"),
                GantryAction(ActionType.WAIT, duration_ms=200,
                            description="Stabilize grip"),
                GantryAction(ActionType.LIFT_UP,
                            description="Lift captured pawn"),
                GantryAction(ActionType.MOVE_TO, square=storage_square,
                            description=f"Move to storage {storage_square}"),
                GantryAction(ActionType.LIFT_DOWN,
                            description="Lower captured pawn"),
                GantryAction(ActionType.GRIP_OPEN,
                            description="Release captured pawn"),
                GantryAction(ActionType.LIFT_UP,
                            description="Raise gripper"),
            ])

            # Mark storage square as occupied
            if storage_square != "storage_full_fallback":
                self.smart_storage.mark_occupied(storage_square, captured_piece)

        # Step 2: Move attacking pawn
        actions.extend(self._plan_normal_move(analysis))

        return actions

    def _plan_castling(self, analysis: MoveAnalysis) -> List[GantryAction]:
        """
        Plan action sequence for castling.

        Castling requires moving two pieces: king and rook.

        Sequence:
        1. Move king
        2. Move rook
        """
        actions = []

        # Step 1: Move king (use from_square and to_square from analysis)
        king_move = MoveAnalysis(
            move=analysis.move,
            from_square=analysis.from_square,
            to_square=analysis.to_square,
            piece_type="king",
            is_capture=False,
            is_castling=False  # Treat as normal move for action planning
        )
        actions.extend(self._plan_normal_move(king_move))

        # Step 2: Move rook
        if analysis.castling_rook_move:
            rook_from, rook_to = analysis.castling_rook_move
            rook_move = MoveAnalysis(
                move=analysis.move,  # Same move object
                from_square=rook_from,
                to_square=rook_to,
                piece_type="rook",
                is_capture=False,
                is_castling=False  # Treat as normal move for action planning
            )
            actions.extend(self._plan_normal_move(rook_move))

        return actions

    def _get_piece_type_from_analysis(self, analysis: MoveAnalysis) -> PieceType:
        """
        Extract piece type from move analysis for captured piece.

        Args:
            analysis: MoveAnalysis object

        Returns:
            PieceType of the captured piece
        """
        # Get the piece at the captured square from the board
        if analysis.captured_square:
            square_obj = chess.parse_square(analysis.captured_square)
            piece = self.chess_engine.board.piece_at(square_obj)

            if piece:
                # Map python-chess piece types to our PieceType enum
                piece_type_map = {
                    chess.PAWN: PieceType.PAWN,
                    chess.KNIGHT: PieceType.KNIGHT,
                    chess.BISHOP: PieceType.BISHOP,
                    chess.ROOK: PieceType.ROOK,
                    chess.QUEEN: PieceType.QUEEN,
                    chess.KING: PieceType.KING,
                }
                return piece_type_map.get(piece.piece_type, PieceType.PAWN)

        # Fallback to pawn if unable to determine
        return PieceType.PAWN

    def reset_storage(self):
        """Reset storage counters (start of new game)."""
        # Clear all storage squares
        for square in self.smart_storage.storage_map.squares.values():
            self.smart_storage.mark_empty(square.square)

    def plan_promotion(self, from_square: str, to_square: str, promoted_piece_type: PieceType, piece_color: PieceColor) -> Optional[List[GantryAction]]:
        """
        Plan action sequence for pawn promotion.

        Sequence:
        1. Move pawn to storage (temporary holding)
        2. Retrieve promoted piece from storage
        3. Place promoted piece on promotion square

        Args:
            from_square: Source square of pawn
            to_square: Promotion square
            promoted_piece_type: Type of piece to promote to (Q/R/B/N)
            piece_color: Color of the promoting pawn

        Returns:
            List of GantryAction objects, or None if promoted piece not available
        """
        actions = []

        # Step 1: Find promoted piece in storage
        promoted_piece_square = self.smart_storage.find_piece_in_storage(
            promoted_piece_type,
            piece_color
        )

        if promoted_piece_square is None:
            # Promoted piece not available in storage
            return None

        # Create temporary storage square for the pawn
        pawn_piece = Piece(PieceType.PAWN, piece_color)
        pawn_storage_square = self.smart_storage.assign_storage_square(
            pawn_piece,
            to_square
        )

        if pawn_storage_square is None:
            # Storage full - cannot complete promotion
            return None

        # Step 2: Move pawn to temporary storage
        actions.extend([
            GantryAction(ActionType.MOVE_TO, square=from_square,
                        description=f"Move to pawn at {from_square}"),
            GantryAction(ActionType.LIFT_DOWN,
                        description="Lower to grab pawn"),
            GantryAction(ActionType.GRIP_CLOSE,
                        description="Grip pawn"),
            GantryAction(ActionType.WAIT, duration_ms=200,
                        description="Stabilize grip"),
            GantryAction(ActionType.LIFT_UP,
                        description="Lift pawn"),
            GantryAction(ActionType.MOVE_TO, square=pawn_storage_square,
                        description=f"Move pawn to storage {pawn_storage_square}"),
            GantryAction(ActionType.LIFT_DOWN,
                        description="Lower pawn"),
            GantryAction(ActionType.GRIP_OPEN,
                        description="Release pawn"),
            GantryAction(ActionType.LIFT_UP,
                        description="Raise gripper"),
        ])

        # Mark pawn as stored
        self.smart_storage.mark_occupied(pawn_storage_square, pawn_piece)

        # Step 3: Retrieve promoted piece from storage
        actions.extend([
            GantryAction(ActionType.MOVE_TO, square=promoted_piece_square,
                        description=f"Move to {promoted_piece_type.value} at {promoted_piece_square}"),
            GantryAction(ActionType.LIFT_DOWN,
                        description=f"Lower to grab {promoted_piece_type.value}"),
            GantryAction(ActionType.GRIP_CLOSE,
                        description=f"Grip {promoted_piece_type.value}"),
            GantryAction(ActionType.WAIT, duration_ms=200,
                        description="Stabilize grip"),
            GantryAction(ActionType.LIFT_UP,
                        description=f"Lift {promoted_piece_type.value}"),
            GantryAction(ActionType.MOVE_TO, square=to_square,
                        description=f"Move to promotion square {to_square}"),
            GantryAction(ActionType.LIFT_DOWN,
                        description=f"Lower {promoted_piece_type.value}"),
            GantryAction(ActionType.GRIP_OPEN,
                        description=f"Release {promoted_piece_type.value}"),
            GantryAction(ActionType.LIFT_UP,
                        description="Raise gripper"),
        ])

        # Mark promoted piece square as empty (it's now on the board)
        self.smart_storage.mark_empty(promoted_piece_square)

        return actions

    def _plan_edge_push_removal(self, captured_piece: Piece, from_square: str) -> Optional[List[GantryAction]]:
        """
        Plan action sequence to remove piece via edge push.

        Sequence:
        1. Pick up captured piece
        2. Move to edge square
        3. Place piece on edge
        4. Move to push square (adjacent off-board)
        5. Lower gripper
        6. Push piece off board
        7. Raise gripper

        Args:
            captured_piece: Piece being removed
            from_square: Square where piece was captured

        Returns:
            List of GantryAction objects, or None if no edge location available
        """
        if not self.edge_push_manager or not self.board_state:
            return None

        # Find edge push location
        location = self.edge_push_manager.find_edge_push_location(self.board_state, from_square)

        if location is None:
            return None  # No edge location available

        actions = [
            # Pick up captured piece
            GantryAction(ActionType.MOVE_TO, square=from_square,
                        description=f"Move to captured {captured_piece.type.value} at {from_square}"),
            GantryAction(ActionType.LIFT_DOWN,
                        description="Lower to grab captured piece"),
            GantryAction(ActionType.GRIP_CLOSE,
                        description=f"Grip captured {captured_piece.type.value}"),
            GantryAction(ActionType.WAIT, duration_ms=200,
                        description="Stabilize grip"),
            GantryAction(ActionType.LIFT_UP,
                        description="Lift captured piece"),

            # Move to edge square
            GantryAction(ActionType.MOVE_TO, square=location.edge_square,
                        description=f"Move to edge square {location.edge_square}"),
            GantryAction(ActionType.LIFT_DOWN,
                        description="Lower piece to edge"),
            GantryAction(ActionType.GRIP_OPEN,
                        description="Release piece"),
            GantryAction(ActionType.LIFT_UP,
                        description="Raise gripper"),

            # Move to push square and push
            GantryAction(ActionType.MOVE_TO, square=location.push_square,
                        description=f"Move to push position {location.push_square}"),
            GantryAction(ActionType.LIFT_DOWN,
                        description="Lower gripper for push"),
            GantryAction(ActionType.PUSH,
                        push_direction=location.direction.value,
                        push_distance_mm=30.0,  # Push 30mm
                        feedrate=300,  # Slow push
                        description=f"Push piece {location.direction.value} off board"),
            GantryAction(ActionType.LIFT_UP,
                        description="Raise gripper"),
        ]

        # Mark edge location as occupied
        self.edge_push_manager.mark_occupied(location.edge_square)

        return actions

    def _plan_tool_push_removal(self, captured_piece: Piece, from_square: str, edge_location: EdgePushLocation) -> Optional[List[GantryAction]]:
        """
        Plan action sequence to remove piece using pusher tool.

        Sequence:
        1. Move to tool holder
        2. Pick up pusher tool
        3. Move to piece location
        4. Position tool behind piece
        5. Lower tool
        6. Push piece off edge
        7. Raise tool
        8. Return to tool holder
        9. Release tool

        Args:
            captured_piece: Piece being removed
            from_square: Square where piece was captured
            edge_location: Edge location for pushing

        Returns:
            List of GantryAction objects, or None if tool not available
        """
        if not self.tool_pusher_manager or not self.tool_pusher_manager.is_tool_available():
            return None

        tool_holder = self.tool_pusher_manager.get_tool_holder_square()
        if not tool_holder:
            return None

        actions = [
            # Pick up tool
            GantryAction(ActionType.MOVE_TO, square=tool_holder,
                        description=f"Move to tool holder at {tool_holder}"),
            GantryAction(ActionType.LIFT_DOWN,
                        description="Lower to grab pusher tool"),
            GantryAction(ActionType.GRIP_CLOSE,
                        description="Grip pusher tool"),
            GantryAction(ActionType.WAIT, duration_ms=200,
                        description="Stabilize tool grip"),
            GantryAction(ActionType.LIFT_UP,
                        description="Lift pusher tool"),

            # Move to piece
            GantryAction(ActionType.MOVE_TO, square=from_square,
                        description=f"Move tool to piece at {from_square}"),

            # Push piece off board
            GantryAction(ActionType.LIFT_DOWN,
                        description="Lower tool to push height"),
            GantryAction(ActionType.PUSH,
                        push_direction=edge_location.direction.value,
                        push_distance_mm=self.tool_pusher_manager.get_push_distance(edge_location.direction.value),
                        feedrate=300,  # Slow controlled push
                        description=f"Push piece {edge_location.direction.value} with tool"),
            GantryAction(ActionType.LIFT_UP,
                        description="Raise tool"),

            # Return tool
            GantryAction(ActionType.MOVE_TO, square=tool_holder,
                        description=f"Return to tool holder at {tool_holder}"),
            GantryAction(ActionType.LIFT_DOWN,
                        description="Lower tool to holder"),
            GantryAction(ActionType.GRIP_OPEN,
                        description="Release pusher tool"),
            GantryAction(ActionType.LIFT_UP,
                        description="Raise gripper"),
        ]

        # Mark tool status
        self.tool_pusher_manager.mark_tool_picked_up()
        # ... tool operations ...
        self.tool_pusher_manager.mark_tool_returned()

        return actions

    def _get_capture_removal_strategy(self, captured_piece: Piece, from_square: str) -> Optional[List[GantryAction]]:
        """
        Determine best strategy for captured piece removal.

        Priority:
        1. Smart Storage (if available)
        2. Tool-based push (if enabled and tool available)
        3. Edge push (if enabled)
        4. Fallback error

        Args:
            captured_piece: Piece being captured
            from_square: Square where piece was captured

        Returns:
            List of GantryAction objects
        """
        # Try smart storage first
        storage_square = self.smart_storage.assign_storage_square(captured_piece, from_square)

        if storage_square is not None:
            # Smart storage available - use it
            return None  # Handled by existing _plan_capture logic

        # Storage full - try advanced strategies

        # Try tool-based push if enabled
        if self.tool_pusher_manager and self.tool_pusher_manager.is_tool_available():
            if self.edge_push_manager and self.board_state:
                edge_location = self.edge_push_manager.find_edge_push_location(self.board_state, from_square)
                if edge_location:
                    return self._plan_tool_push_removal(captured_piece, from_square, edge_location)

        # Try edge push if enabled
        if self.edge_push_manager:
            return self._plan_edge_push_removal(captured_piece, from_square)

        # No strategy available
        return None
