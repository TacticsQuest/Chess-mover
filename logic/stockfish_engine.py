"""
Stockfish Chess Engine Integration

Provides chess analysis and best move suggestions using Stockfish.
Enables offline operation on Raspberry Pi.
"""

import os
import subprocess
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class EngineAnalysis:
    """Analysis result from Stockfish."""
    best_move: str  # UCI format (e.g., "e2e4")
    evaluation: float  # Centipawn score (positive = white advantage)
    mate_in: Optional[int] = None  # Moves to mate (None if not mate)
    pv_line: List[str] = None  # Principal variation (best line)
    depth: int = 20  # Search depth used


class StockfishEngine:
    """
    Interface to Stockfish chess engine.

    Features:
    - Best move suggestions
    - Position evaluation
    - Mate detection
    - Principal variation analysis
    - Configurable skill level and depth
    """

    def __init__(self, stockfish_path: Optional[str] = None, skill_level: int = 20):
        """
        Initialize Stockfish engine.

        Args:
            stockfish_path: Path to stockfish executable
                           (auto-detects if None)
            skill_level: Stockfish skill level (0-20, where 20 is strongest)
        """
        self.process: Optional[subprocess.Popen] = None
        self.is_ready = False
        self.skill_level = skill_level

        # Default engine parameters
        self.default_depth = 20
        self.default_time_ms = 2000  # 2 seconds per move

        # Find Stockfish (may raise FileNotFoundError)
        self.stockfish_path = stockfish_path or self._find_stockfish()

    def _find_stockfish(self) -> str:
        """
        Auto-detect Stockfish installation.

        Returns:
            Path to stockfish executable

        Raises:
            FileNotFoundError: If Stockfish not found
        """
        # Common locations for Stockfish
        possible_paths = [
            # Windows
            r"C:\Program Files\Stockfish\stockfish.exe",
            r"C:\Stockfish\stockfish.exe",
            "stockfish.exe",
            # Linux / Raspberry Pi
            "/usr/bin/stockfish",
            "/usr/local/bin/stockfish",
            "/usr/games/stockfish",
            "stockfish",
            # macOS
            "/opt/homebrew/bin/stockfish",
            "/usr/local/Cellar/stockfish/*/bin/stockfish"
        ]

        for path in possible_paths:
            # Handle wildcard paths
            if '*' in path:
                import glob
                matches = glob.glob(path)
                if matches:
                    return matches[0]
            # Direct path check
            elif os.path.exists(path):
                return path
            # Check if in PATH
            elif self._is_in_path(path):
                return path

        raise FileNotFoundError(
            "Stockfish not found. Please install Stockfish or provide path."
        )

    def _is_in_path(self, command: str) -> bool:
        """Check if command is available in system PATH."""
        try:
            result = subprocess.run(
                [command, "--version"] if os.name == 'nt' else ["which", command],
                capture_output=True,
                timeout=1
            )
            return result.returncode == 0
        except:
            return False

    def start(self) -> bool:
        """
        Start Stockfish engine process.

        Returns:
            True if started successfully
        """
        try:
            self.process = subprocess.Popen(
                [self.stockfish_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )

            # Send UCI initialization
            self._send_command("uci")

            # Wait for uciok
            while True:
                line = self._read_line()
                if line == "uciok":
                    break

            # Set skill level
            self._send_command(f"setoption name Skill Level value {self.skill_level}")

            # Send isready
            self._send_command("isready")
            while True:
                line = self._read_line()
                if line == "readyok":
                    break

            self.is_ready = True
            return True

        except Exception as e:
            print(f"[STOCKFISH] Failed to start: {e}")
            return False

    def stop(self):
        """Stop Stockfish engine process."""
        if self.process:
            try:
                self._send_command("quit")
                self.process.wait(timeout=2)
            except:
                self.process.kill()
            self.process = None
            self.is_ready = False

    def analyze_position(self, fen: str, depth: Optional[int] = None) -> Optional[EngineAnalysis]:
        """
        Analyze a chess position.

        Args:
            fen: Position in FEN notation
            depth: Search depth (uses default if None)

        Returns:
            EngineAnalysis with best move and evaluation
        """
        if not self.is_ready:
            if not self.start():
                return None

        depth = depth or self.default_depth

        try:
            # Set position
            self._send_command(f"position fen {fen}")

            # Start analysis
            self._send_command(f"go depth {depth}")

            # Parse output
            best_move = None
            evaluation = 0.0
            mate_in = None
            pv_line = []

            while True:
                line = self._read_line()

                if line.startswith("bestmove"):
                    parts = line.split()
                    best_move = parts[1] if len(parts) > 1 else None
                    break

                elif line.startswith("info"):
                    # Parse info line
                    parts = line.split()

                    # Get evaluation
                    if "score" in parts:
                        score_idx = parts.index("score")
                        score_type = parts[score_idx + 1]
                        score_value = int(parts[score_idx + 2])

                        if score_type == "cp":
                            evaluation = score_value / 100.0
                        elif score_type == "mate":
                            mate_in = score_value

                    # Get principal variation
                    if "pv" in parts:
                        pv_idx = parts.index("pv")
                        pv_line = parts[pv_idx + 1:]

            if best_move:
                return EngineAnalysis(
                    best_move=best_move,
                    evaluation=evaluation,
                    mate_in=mate_in,
                    pv_line=pv_line,
                    depth=depth
                )

            return None

        except Exception as e:
            print(f"[STOCKFISH] Analysis error: {e}")
            return None

    def get_best_move(self, fen: str, time_ms: Optional[int] = None) -> Optional[str]:
        """
        Get best move for a position (quick analysis).

        Args:
            fen: Position in FEN notation
            time_ms: Time limit in milliseconds

        Returns:
            Best move in UCI format (e.g., "e2e4")
        """
        if not self.is_ready:
            if not self.start():
                return None

        time_ms = time_ms or self.default_time_ms

        try:
            # Set position
            self._send_command(f"position fen {fen}")

            # Start search
            self._send_command(f"go movetime {time_ms}")

            # Get best move
            while True:
                line = self._read_line()
                if line.startswith("bestmove"):
                    parts = line.split()
                    return parts[1] if len(parts) > 1 else None

        except Exception as e:
            print(f"[STOCKFISH] Best move error: {e}")
            return None

    def evaluate_move(self, fen: str, move: str, depth: Optional[int] = None) -> Optional[float]:
        """
        Evaluate a specific move in a position.

        Args:
            fen: Position in FEN notation
            move: Move to evaluate (UCI format)
            depth: Search depth

        Returns:
            Evaluation in pawns (positive = good for white)
        """
        if not self.is_ready:
            if not self.start():
                return None

        depth = depth or self.default_depth

        try:
            # Set position with move
            self._send_command(f"position fen {fen} moves {move}")

            # Analyze
            self._send_command(f"go depth {depth}")

            evaluation = 0.0

            while True:
                line = self._read_line()

                if line.startswith("bestmove"):
                    break

                elif line.startswith("info") and "score cp" in line:
                    parts = line.split()
                    if "cp" in parts:
                        cp_idx = parts.index("cp")
                        evaluation = -int(parts[cp_idx + 1]) / 100.0  # Negate because we made the move

            return evaluation

        except Exception as e:
            print(f"[STOCKFISH] Move evaluation error: {e}")
            return None

    def get_top_moves(self, fen: str, count: int = 3, depth: Optional[int] = None) -> List[Tuple[str, float]]:
        """
        Get top N best moves for a position.

        Args:
            fen: Position in FEN notation
            count: Number of top moves to return
            depth: Search depth

        Returns:
            List of (move, evaluation) tuples
        """
        if not self.is_ready:
            if not self.start():
                return []

        depth = depth or self.default_depth

        try:
            # Set position
            self._send_command(f"position fen {fen}")

            # Request multiple PV lines
            self._send_command(f"setoption name MultiPV value {count}")

            # Analyze
            self._send_command(f"go depth {depth}")

            moves = []

            while True:
                line = self._read_line()

                if line.startswith("bestmove"):
                    break

                elif line.startswith("info") and "multipv" in line:
                    parts = line.split()

                    # Get PV move
                    if "pv" in parts:
                        pv_idx = parts.index("pv")
                        move = parts[pv_idx + 1] if pv_idx + 1 < len(parts) else None

                    # Get evaluation
                    evaluation = 0.0
                    if "score cp" in line:
                        cp_idx = parts.index("cp")
                        evaluation = int(parts[cp_idx + 1]) / 100.0
                    elif "score mate" in line:
                        mate_idx = parts.index("mate")
                        mate_in = int(parts[mate_idx + 1])
                        evaluation = 999.0 if mate_in > 0 else -999.0

                    if move and (move, evaluation) not in moves:
                        moves.append((move, evaluation))

            # Reset MultiPV
            self._send_command("setoption name MultiPV value 1")

            return moves[:count]

        except Exception as e:
            print(f"[STOCKFISH] Top moves error: {e}")
            return []

    def set_skill_level(self, level: int):
        """
        Set Stockfish skill level.

        Args:
            level: Skill level (0-20, where 20 is strongest)
        """
        self.skill_level = max(0, min(20, level))
        if self.is_ready:
            self._send_command(f"setoption name Skill Level value {self.skill_level}")

    def _send_command(self, command: str):
        """Send command to Stockfish."""
        if self.process and self.process.stdin:
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()

    def _read_line(self) -> str:
        """Read line from Stockfish output."""
        if self.process and self.process.stdout:
            return self.process.stdout.readline().strip()
        return ""

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

    def __del__(self):
        """Cleanup on deletion."""
        self.stop()
