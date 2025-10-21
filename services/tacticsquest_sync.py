"""
TacticsQuest Game Synchronization Service

Connects to TacticsQuest Supabase database and synchronizes correspondence
games to the physical Chess Mover Machine.

Restricted to user: davidljones88@yahoo.com
"""

import os
import time
import threading
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from supabase import create_client, Client

from logic.game_controller import GameController


@dataclass
class PendingMove:
    """Represents a move that needs to be executed on the physical board."""
    game_id: str
    move_uci: str
    move_san: str
    move_index: int
    white_username: str
    black_username: str
    time_control: str


@dataclass
class Puzzle:
    """Represents a chess puzzle from TacticsQuest."""
    puzzle_id: str
    fen: str
    moves: List[str]  # Solution moves in UCI format
    rating: int
    themes: List[str]
    popularity: int
    difficulty: str  # 'easy', 'medium', 'hard'


class TacticsQuestSync:
    """
    Synchronizes TacticsQuest correspondence games to physical chess board.

    Features:
    - Polls Supabase for new moves
    - Executes moves on physical board
    - Updates sync status back to database
    - Supports multiple concurrent games
    """

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        user_id: str,
        game_controller: GameController,
        log_fn: Callable[[str], None] = print
    ):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.user_id = user_id
        self.game_controller = game_controller
        self.log = log_fn

        # Sync state
        self.is_running = False
        self.poll_interval = 10  # seconds
        self.sync_thread: Optional[threading.Thread] = None

        # Tracked games (game_id -> move_index)
        self.tracked_games: Dict[str, int] = {}

        # Current active game on physical board
        self.active_game_id: Optional[str] = None

    def start(self):
        """Start the synchronization service."""
        if self.is_running:
            self.log("[SYNC] Already running")
            return

        self.is_running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        self.log("[SYNC] ✓ TacticsQuest sync started")

    def stop(self):
        """Stop the synchronization service."""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        self.log("[SYNC] ✗ TacticsQuest sync stopped")

    def _sync_loop(self):
        """Main sync loop (runs in background thread)."""
        while self.is_running:
            try:
                self._check_for_new_moves()
            except Exception as e:
                self.log(f"[SYNC] Error in sync loop: {e}")

            # Wait before next poll
            time.sleep(self.poll_interval)

    def _check_for_new_moves(self):
        """Check Supabase for new moves in tracked games."""
        try:
            # Call the database function to get pending games
            response = self.supabase.rpc(
                'get_chess_mover_pending_games',
                {'p_user_id': self.user_id}
            ).execute()

            if not response.data:
                return  # No pending moves

            # Process each game with new moves
            for game in response.data:
                self._process_game_moves(game)

        except Exception as e:
            self.log(f"[SYNC] Error checking for moves: {e}")

    def _process_game_moves(self, game: Dict):
        """
        Process new moves for a game.

        Args:
            game: Game data from database
        """
        game_id = game['game_id']
        moves = game['moves']  # JSONB array
        last_synced = game['last_synced_move_index']
        total_moves = game['total_moves']

        if total_moves <= last_synced:
            return  # No new moves

        # Get new moves
        new_moves = moves[last_synced:]

        self.log(f"[SYNC] Game {game_id[:8]}... has {len(new_moves)} new move(s)")
        self.log(f"  White: {game['white_username']}")
        self.log(f"  Black: {game['black_username']}")
        self.log(f"  Time: {game['time_control']}")

        # Check if this is the active game
        if self.active_game_id and self.active_game_id != game_id:
            self.log(f"[SYNC] ⚠️ Different game active on board. Skipping...")
            return

        # If no active game, load this one
        if not self.active_game_id:
            self._load_game_to_board(game)

        # Execute each new move
        for i, move_data in enumerate(new_moves):
            move_index = last_synced + i

            # Extract move (format depends on how TacticsQuest stores moves)
            # Assuming UCI format like "e2e4"
            move_uci = move_data if isinstance(move_data, str) else move_data.get('uci', '')

            if not move_uci:
                self.log(f"[SYNC] ⚠️ Invalid move format at index {move_index}")
                continue

            self.log(f"[SYNC] Executing move {move_index + 1}: {move_uci}")

            # Execute on physical board
            success = self.game_controller.make_move(move_uci, execute_physically=True)

            if success:
                # Mark as synced in database
                self._mark_synced(game_id, move_index + 1)
                self.tracked_games[game_id] = move_index + 1
            else:
                self.log(f"[SYNC] ✗ Failed to execute move: {move_uci}")
                break  # Stop processing this game

    def _load_game_to_board(self, game: Dict):
        """
        Load a game onto the physical board.

        Args:
            game: Game data from database
        """
        game_id = game['game_id']
        fen = game['fen']

        self.log(f"[SYNC] Loading game {game_id[:8]}... to physical board")

        # Load position from FEN
        if self.game_controller.load_fen(fen):
            self.active_game_id = game_id
            self.log(f"[SYNC] ✓ Game loaded successfully")
        else:
            self.log(f"[SYNC] ✗ Failed to load FEN: {fen}")

    def _mark_synced(self, game_id: str, move_index: int):
        """
        Mark moves as synced in the database.

        Args:
            game_id: Game ID
            move_index: Last synced move index
        """
        try:
            self.supabase.rpc(
                'mark_chess_mover_synced',
                {
                    'p_game_id': game_id,
                    'p_user_id': self.user_id,
                    'p_move_index': move_index
                }
            ).execute()

        except Exception as e:
            self.log(f"[SYNC] Error marking synced: {e}")

    def enable_game_sync(self, game_id: str) -> bool:
        """
        Enable sync for a specific game.

        Args:
            game_id: Game ID to enable

        Returns:
            True if enabled successfully
        """
        try:
            self.supabase.rpc(
                'enable_chess_mover_sync',
                {
                    'p_game_id': game_id,
                    'p_user_id': self.user_id
                }
            ).execute()

            self.log(f"[SYNC] ✓ Enabled sync for game {game_id[:8]}...")
            return True

        except Exception as e:
            self.log(f"[SYNC] ✗ Failed to enable sync: {e}")
            return False

    def disable_game_sync(self, game_id: str) -> bool:
        """
        Disable sync for a specific game.

        Args:
            game_id: Game ID to disable

        Returns:
            True if disabled successfully
        """
        try:
            self.supabase.rpc(
                'disable_chess_mover_sync',
                {
                    'p_game_id': game_id,
                    'p_user_id': self.user_id
                }
            ).execute()

            self.log(f"[SYNC] ✓ Disabled sync for game {game_id[:8]}...")

            # Clear from tracked games
            if game_id in self.tracked_games:
                del self.tracked_games[game_id]

            # Clear active game if it was this one
            if self.active_game_id == game_id:
                self.active_game_id = None

            return True

        except Exception as e:
            self.log(f"[SYNC] ✗ Failed to disable sync: {e}")
            return False

    def get_synced_games(self) -> List[Dict]:
        """
        Get list of all games currently synced to chess mover.

        Returns:
            List of game dictionaries
        """
        try:
            response = self.supabase.table('games').select('*').eq(
                'sync_to_chess_mover', True
            ).eq(
                'chess_mover_user_id', self.user_id
            ).execute()

            return response.data

        except Exception as e:
            self.log(f"[SYNC] Error getting synced games: {e}")
            return []

    def set_poll_interval(self, seconds: int):
        """
        Set the polling interval.

        Args:
            seconds: Seconds between polls (minimum 5)
        """
        self.poll_interval = max(5, seconds)
        self.log(f"[SYNC] Poll interval set to {self.poll_interval}s")

    # ========================================================================
    # PUZZLE FEATURES
    # ========================================================================

    def get_daily_puzzle(self) -> Optional[Puzzle]:
        """
        Fetch the daily puzzle from TacticsQuest.

        Returns:
            Puzzle object or None if error
        """
        try:
            response = self.supabase.rpc(
                'get_daily_puzzle',
                {}
            ).execute()

            if response.data:
                puzzle_data = response.data[0] if isinstance(response.data, list) else response.data
                return self._parse_puzzle(puzzle_data)

            return None

        except Exception as e:
            self.log(f"[PUZZLE] Error fetching daily puzzle: {e}")
            return None

    def get_random_puzzle(self, difficulty: Optional[str] = None, themes: Optional[List[str]] = None) -> Optional[Puzzle]:
        """
        Fetch a random puzzle matching criteria.

        Args:
            difficulty: 'easy', 'medium', or 'hard'
            themes: List of theme tags (e.g., ['fork', 'pin'])

        Returns:
            Puzzle object or None if error
        """
        try:
            params = {
                'p_user_id': self.user_id
            }

            if difficulty:
                params['p_difficulty'] = difficulty

            if themes:
                params['p_themes'] = themes

            response = self.supabase.rpc(
                'get_random_puzzle',
                params
            ).execute()

            if response.data:
                puzzle_data = response.data[0] if isinstance(response.data, list) else response.data
                return self._parse_puzzle(puzzle_data)

            return None

        except Exception as e:
            self.log(f"[PUZZLE] Error fetching random puzzle: {e}")
            return None

    def get_puzzle_by_id(self, puzzle_id: str) -> Optional[Puzzle]:
        """
        Fetch a specific puzzle by ID.

        Args:
            puzzle_id: Puzzle ID

        Returns:
            Puzzle object or None if error
        """
        try:
            response = self.supabase.table('puzzles').select('*').eq(
                'id', puzzle_id
            ).execute()

            if response.data:
                return self._parse_puzzle(response.data[0])

            return None

        except Exception as e:
            self.log(f"[PUZZLE] Error fetching puzzle {puzzle_id}: {e}")
            return None

    def get_user_puzzles(self, limit: int = 10, difficulty: Optional[str] = None) -> List[Puzzle]:
        """
        Get puzzles tailored to user's rating/performance.

        Args:
            limit: Max number of puzzles to return
            difficulty: Optional difficulty filter

        Returns:
            List of Puzzle objects
        """
        try:
            params = {
                'p_user_id': self.user_id,
                'p_limit': limit
            }

            if difficulty:
                params['p_difficulty'] = difficulty

            response = self.supabase.rpc(
                'get_user_recommended_puzzles',
                params
            ).execute()

            if response.data:
                return [self._parse_puzzle(p) for p in response.data]

            return []

        except Exception as e:
            self.log(f"[PUZZLE] Error fetching user puzzles: {e}")
            return []

    def submit_puzzle_attempt(self, puzzle_id: str, success: bool, time_seconds: int, attempts: int = 1) -> bool:
        """
        Submit a puzzle attempt to TacticsQuest.

        Args:
            puzzle_id: Puzzle ID
            success: Whether solved correctly
            time_seconds: Time taken in seconds
            attempts: Number of attempts made

        Returns:
            True if submitted successfully
        """
        try:
            self.supabase.rpc(
                'submit_puzzle_attempt',
                {
                    'p_user_id': self.user_id,
                    'p_puzzle_id': puzzle_id,
                    'p_success': success,
                    'p_time_seconds': time_seconds,
                    'p_attempts': attempts
                }
            ).execute()

            self.log(f"[PUZZLE] ✓ Submitted attempt for puzzle {puzzle_id[:8]}...")
            return True

        except Exception as e:
            self.log(f"[PUZZLE] ✗ Error submitting attempt: {e}")
            return False

    def _parse_puzzle(self, data: Dict) -> Puzzle:
        """
        Parse puzzle data from database into Puzzle object.

        Args:
            data: Raw puzzle data from Supabase

        Returns:
            Puzzle object
        """
        return Puzzle(
            puzzle_id=data.get('id', ''),
            fen=data.get('fen', ''),
            moves=data.get('moves', []) if isinstance(data.get('moves'), list) else [],
            rating=data.get('rating', 1500),
            themes=data.get('themes', []) if isinstance(data.get('themes'), list) else [],
            popularity=data.get('popularity', 0),
            difficulty=data.get('difficulty', 'medium')
        )
