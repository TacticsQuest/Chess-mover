
from typing import List, Tuple
from .square_classifier import Label

def diff_boards(prev_lab: List[List[Label]], curr_lab: List[List[Label]]):
    ch=[]
    for r in range(8):
        for c in range(8):
            if prev_lab[r][c] != curr_lab[r][c]:
                ch.append((r,c))
    return ch

def to_fen_from_labels(labels: List[List[Label]], side_to_move: str = 'w') -> str:
    rows=[]
    for r in range(8):
        empty=0; row=""
        for c in range(8):
            l=labels[r][c]
            if l==Label.EMPTY:
                empty+=1
            else:
                if empty>0: row+=str(empty); empty=0
                row+= 'P' if l==Label.WHITE else 'p'
        if empty>0: row+=str(empty)
        rows.append(row)
    return "/".join(rows) + f" {side_to_move} - - 0 1"

class MoveVerifier:
    def derive_move(self, prev_lab, curr_lab):
        changed = diff_boards(prev_lab, curr_lab)
        if len(changed) < 2:
            return None
        from_sq=None; to_sq=None
        for (r,c) in changed:
            if prev_lab[r][c]!=Label.EMPTY and curr_lab[r][c]==Label.EMPTY:
                from_sq=(r,c)
            if prev_lab[r][c]==Label.EMPTY and curr_lab[r][c]!=Label.EMPTY:
                to_sq=(r,c)
        if from_sq is None or to_sq is None:
            return None
        def rc_to_sq(r,c):
            file=c; rank=7-r
            return rank*8+file
        return rc_to_sq(*from_sq), rc_to_sq(*to_sq)
