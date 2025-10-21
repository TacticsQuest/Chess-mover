from typing import Tuple
from .board_map import BoardConfig

class MovePlanner:
    def __init__(self, board_cfg: BoardConfig):
        self.board_cfg = board_cfg

    def plan_move(self, from_sq: str, to_sq: str) -> Tuple[tuple[float,float], tuple[float,float]]:
        start_xy = self.board_cfg.square_center_xy(from_sq)
        end_xy = self.board_cfg.square_center_xy(to_sq)
        return start_xy, end_xy
