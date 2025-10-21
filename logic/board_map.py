from dataclasses import dataclass
from typing import Optional
from enum import Enum

class StorageLayout(Enum):
    """Defines where captured pieces are stored relative to the playing area."""
    NONE = "none"  # No storage area, entire board is playing area (standard 8x8)
    TOP = "top"  # Storage above the playing area (ranks 9-10, A1 at bottom-left)
    BOTTOM = "bottom"  # Storage below the playing area (ranks 1-2, A1 at storage bottom-left, playing area at top)
    PERIMETER = "perimeter"  # Storage around all sides (1 square border)

@dataclass
class PlayArea:
    """Defines the actual playing area within a larger board grid."""
    min_file: int  # 0-indexed
    max_file: int  # 0-indexed, inclusive
    min_rank: int  # 0-indexed
    max_rank: int  # 0-indexed, inclusive

@dataclass
class BoardConfig:
    files: int
    ranks: int
    width_mm: float
    height_mm: float
    origin_x_mm: float
    origin_y_mm: float
    play_area: Optional[PlayArea] = None  # None means entire board is playing area
    storage_layout: StorageLayout = StorageLayout.NONE  # Storage configuration

    def square_size_x(self) -> float:
        return self.width_mm / max(1, (self.files))

    def square_size_y(self) -> float:
        return self.height_mm / max(1, (self.ranks))

    def file_index(self, file_char: str) -> int:
        f = file_char.lower()
        if not ('a' <= f <= 'z'):
            raise ValueError("Invalid file character")
        idx = ord(f) - ord('a')
        if idx < 0 or idx >= self.files:
            raise ValueError("File out of range")
        return idx

    def rank_index(self, rank_num: int) -> int:
        idx = rank_num - 1
        if idx < 0 or idx >= self.ranks:
            raise ValueError("Rank out of range")
        return idx

    def square_center_xy(self, square: str) -> tuple[float, float]:
        # Accept formats like "e4" (files a.., ranks 1..)
        if len(square) < 2:
            raise ValueError("Square must be like 'e4'")
        file_char = square[0]
        try:
            rank_num = int(square[1:])
        except Exception as e:
            raise ValueError("Square rank must be numeric") from e
        fx = self.file_index(file_char)
        ry = self.rank_index(rank_num)
        cx = self.origin_x_mm + (fx + 0.5) * self.square_size_x()
        cy = self.origin_y_mm + (ry + 0.5) * self.square_size_y()
        return cx, cy

    def is_playing_square(self, file_idx: int, rank_idx: int) -> bool:
        """Check if a square (0-indexed) is in the playing area."""
        if self.play_area is None:
            return True  # Entire board is playing area
        return (self.play_area.min_file <= file_idx <= self.play_area.max_file and
                self.play_area.min_rank <= rank_idx <= self.play_area.max_rank)

    def is_captured_piece_square(self, file_idx: int, rank_idx: int) -> bool:
        """Check if a square (0-indexed) is in the captured piece storage area."""
        return not self.is_playing_square(file_idx, rank_idx)

    def get_home_square(self) -> str:
        """
        Get the home position (machine origin) square notation.
        Returns the square where the machine's (0,0) position is located.
        """
        if self.storage_layout == StorageLayout.BOTTOM:
            # Bottom storage: Home is at the bottom-left of storage area
            return "a1"
        elif self.storage_layout == StorageLayout.TOP:
            # Top storage: Home is at bottom-left of playing area (rank 1)
            return "a1"
        elif self.storage_layout == StorageLayout.PERIMETER:
            # Perimeter: Home is at bottom-left of perimeter (file a, rank 1)
            return "a1"
        else:
            # Standard board: Home is at A1 (bottom-left of playing area)
            return "a1"

    def get_playing_area_offset(self) -> tuple[int, int]:
        """
        Get the offset (in squares) from the board's (0,0) to the playing area's bottom-left.
        Returns (file_offset, rank_offset) in squares.
        """
        if self.play_area is None:
            return (0, 0)
        return (self.play_area.min_file, self.play_area.min_rank)
