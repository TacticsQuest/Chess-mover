"""
Chess Game Controller

High-level controller for managing chess games and executing moves
on the physical board.
"""

from typing import List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from logic.chess_engine import ChessEngine, MoveAnalysis
from logic.move_executor import MoveExecutor, GantryAction, ActionType
from logic.board_map import BoardConfig
from logic.profiles import Settings
from logic.smart_storage import SmartStorage, StorageStrategy
from logic.advanced_settings import AdvancedSettings
from controllers.gantry_controller import GantryController
from controllers.servo_controller import ServoController


class GameMode(Enum):
    """Game modes."""
    MANUAL = "manual"          # Manual piece movement
    PGN_REPLAY = "pgn_replay"  # Replay a PGN game
    LIVE_GAME = "live_game"    # Play a live game


@dataclass
class GameState:
    """Current game state."""
    mode: GameMode
    fen: str
    move_count: int
    current_turn: str  # "white" or "black"
    is_check: bool
    is_checkmate: bool
    is_stalemate: bool
    last_move: Optional[str] = None


class GameController:
    """
    Main controller for chess game logic and physical execution.

    Coordinates between:
    - Chess engine (logic)
    - Move executor (planning)
    - Gantry controller (movement)
    - Servo controller (piece manipulation)
    """

    def __init__(
        self,
        gantry: GantryController,
        servos: ServoController,
        settings: Settings,
        board_config: BoardConfig,
        log_fn: Callable[[str], None] = print,
        storage_strategy: StorageStrategy = StorageStrategy.BY_COLOR,
        advanced_settings: Optional[AdvancedSettings] = None
    ):
        self.gantry = gantry
        self.servos = servos
        self.settings = settings
        self.board_config = board_config
        self.log = log_fn

        # Load advanced settings
        self.advanced_settings = advanced_settings or AdvancedSettings()

        # Chess components
        self.chess_engine = ChessEngine()
        self.smart_storage = SmartStorage(board_config, storage_strategy)

        # Initialize move executor with advanced features
        self.move_executor = MoveExecutor(
            self.chess_engine,
            board_config,
            settings,
            self.smart_storage,
            board_state=None,  # Will be set externally if needed
            edge_push_enabled=self.advanced_settings.is_edge_push_enabled(),
            tool_pusher_config=self.advanced_settings.get_tool_config()
        )

        # Game state
        self.mode = GameMode.MANUAL
        self.is_executing = False
        self.current_action_sequence: List[GantryAction] = []

        # PGN replay state
        self.pgn_moves: List[str] = []
        self.pgn_current_index = 0

    def new_game(self):
        """Start a new game from the starting position."""
        self.chess_engine.reset()
        self.move_executor.reset_storage()
        self.mode = GameMode.LIVE_GAME
        self.current_action_sequence = []
        self.is_executing = False
        self.log("[GAME] New game started")

    def load_pgn(self, pgn_string: str) -> bool:
        """
        Load a game from PGN notation.

        Args:
            pgn_string: PGN string

        Returns:
            True if loaded successfully
        """
        # Reset engine first
        self.chess_engine.reset()
        self.move_executor.reset_storage()

        # Parse PGN
        if not self.chess_engine.load_pgn(pgn_string):
            self.log("[GAME] Failed to load PGN")
            return False

        # Get move list
        self.pgn_moves = self.chess_engine.get_move_list_san()
        self.pgn_current_index = len(self.pgn_moves)  # Start at end

        # Reset to starting position for replay
        self.chess_engine.reset()
        self.mode = GameMode.PGN_REPLAY
        self.pgn_current_index = 0

        self.log(f"[GAME] Loaded PGN with {len(self.pgn_moves)} moves")
        return True

    def load_fen(self, fen: str) -> bool:
        """
        Load a position from FEN notation.

        Args:
            fen: FEN string

        Returns:
            True if loaded successfully
        """
        if self.chess_engine.set_fen(fen):
            self.log(f"[GAME] Loaded FEN: {fen}")
            self.mode = GameMode.MANUAL
            return True
        else:
            self.log("[GAME] Failed to load FEN")
            return False

    def make_move(self, move_str: str, execute_physically: bool = False) -> bool:
        """
        Make a move in the game.

        Args:
            move_str: Move in UCI or SAN format
            execute_physically: If True, execute on physical board

        Returns:
            True if move was legal and made
        """
        if self.is_executing:
            self.log("[GAME] Cannot make move while executing")
            return False

        # Plan the move
        action_sequence = self.move_executor.plan_move(move_str)

        if action_sequence is None:
            self.log(f"[GAME] Illegal move: {move_str}")
            return False

        self.log(f"[GAME] Move: {move_str}")
        self.current_action_sequence = action_sequence

        # Execute physically if requested
        if execute_physically:
            self.execute_current_move()

        return True

    def execute_current_move(self):
        """Execute the current action sequence on the physical board."""
        if not self.current_action_sequence:
            self.log("[GAME] No move to execute")
            return

        if self.is_executing:
            self.log("[GAME] Already executing")
            return

        self.is_executing = True
        self.log(f"[GAME] Executing {len(self.current_action_sequence)} actions...")

        try:
            for i, action in enumerate(self.current_action_sequence):
                self.log(f"  [{i+1}/{len(self.current_action_sequence)}] {action}")
                self._execute_action(action)

            self.log("[GAME] ✓ Move executed successfully")

        except Exception as e:
            self.log(f"[GAME] ✗ Execution failed: {e}")

        finally:
            self.is_executing = False
            self.current_action_sequence = []

    def _execute_action(self, action: GantryAction):
        """
        Execute a single gantry action.

        Args:
            action: GantryAction to execute
        """
        if action.action_type == ActionType.MOVE_TO:
            # Move gantry to square
            if action.square:
                # All squares (including storage) are now handled by board_config
                x, y = self.board_config.square_center_xy(action.square)
                feedrate = self.settings.get_board().get('feedrate_mm_min', 2000)
                self.gantry.rapid_to(x, y, feedrate)

        elif action.action_type == ActionType.LIFT_UP:
            self.servos.lift_up()

        elif action.action_type == ActionType.LIFT_DOWN:
            self.servos.lift_down()

        elif action.action_type == ActionType.GRIP_OPEN:
            self.servos.grip_open()

        elif action.action_type == ActionType.GRIP_CLOSE:
            self.servos.grip_close()

        elif action.action_type == ActionType.WAIT:
            import time
            time.sleep(action.duration_ms / 1000.0)

    def get_state(self) -> GameState:
        """
        Get current game state.

        Returns:
            GameState object
        """
        board = self.chess_engine.board
        return GameState(
            mode=self.mode,
            fen=self.chess_engine.get_fen(),
            move_count=len(self.chess_engine.move_history),
            current_turn="white" if board.turn else "black",
            is_check=board.is_check(),
            is_checkmate=self.chess_engine.is_checkmate(),
            is_stalemate=self.chess_engine.is_stalemate(),
            last_move=self.chess_engine.get_move_list_san()[-1] if self.chess_engine.move_history else None
        )

    def get_move_history(self) -> List[str]:
        """Get move history in SAN format."""
        return self.chess_engine.get_move_list_san()

    def get_legal_moves(self) -> List[str]:
        """Get list of all legal moves in current position."""
        return self.chess_engine.get_legal_moves()

    def undo_last_move(self) -> bool:
        """
        Undo the last move.

        Note: This only undoes the move in the engine, not on the physical board.

        Returns:
            True if a move was undone
        """
        if self.chess_engine.undo_move():
            self.log("[GAME] Move undone")
            return True
        else:
            self.log("[GAME] No move to undo")
            return False

    # PGN Replay Methods

    def pgn_next_move(self, execute_physically: bool = True) -> bool:
        """
        Play next move in PGN replay.

        Args:
            execute_physically: If True, execute on physical board

        Returns:
            True if move was made
        """
        if self.mode != GameMode.PGN_REPLAY:
            self.log("[GAME] Not in PGN replay mode")
            return False

        if self.pgn_current_index >= len(self.pgn_moves):
            self.log("[GAME] End of game")
            return False

        move_str = self.pgn_moves[self.pgn_current_index]
        if self.make_move(move_str, execute_physically):
            self.pgn_current_index += 1
            return True

        return False

    def pgn_previous_move(self) -> bool:
        """
        Go back one move in PGN replay.

        Note: Only undoes in engine, not on physical board.

        Returns:
            True if moved back
        """
        if self.mode != GameMode.PGN_REPLAY:
            return False

        if self.pgn_current_index <= 0:
            return False

        if self.undo_last_move():
            self.pgn_current_index -= 1
            return True

        return False

    def pgn_goto_move(self, move_index: int) -> bool:
        """
        Jump to a specific move in PGN replay.

        Args:
            move_index: Move number (0-indexed)

        Returns:
            True if successful
        """
        if self.mode != GameMode.PGN_REPLAY:
            return False

        if move_index < 0 or move_index > len(self.pgn_moves):
            return False

        # Reset to start
        self.chess_engine.reset()
        self.move_executor.reset_storage()

        # Play through to desired position
        for i in range(move_index):
            self.make_move(self.pgn_moves[i], execute_physically=False)

        self.pgn_current_index = move_index
        return True

    def get_pgn_progress(self) -> tuple:
        """
        Get PGN replay progress.

        Returns:
            (current_move_index, total_moves)
        """
        if self.mode != GameMode.PGN_REPLAY:
            return (0, 0)
        return (self.pgn_current_index, len(self.pgn_moves))
