
import numpy as np
import cv2
try:
    import onnxruntime as ort
except Exception:
    ort = None
from enum import IntEnum

class Label(IntEnum):
    EMPTY = 0
    WHITE = 1
    BLACK = 2

class SquareClassifier:
    def __init__(self, onnx_path: str | None = None, conf_thresh: float = 0.55):
        self.onnx_path = onnx_path
        self.conf_thresh = conf_thresh
        self.sess = None
        if onnx_path and ort:
            try:
                self.sess = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
            except Exception:
                self.sess = None

    def _heuristic(self, tile_bgr):
        lab = cv2.cvtColor(tile_bgr, cv2.COLOR_BGR2LAB)
        L,A,B = cv2.split(lab)
        edges = cv2.Canny(L, 40, 120)
        occupied_score = (edges.mean()/255.0)*0.6 + (np.var(L)/(255.0*255.0))*0.4
        if occupied_score < 0.02:
            return Label.EMPTY, 0.95
        center = tile_bgr[tile_bgr.shape[0]//4: 3*tile_bgr.shape[0]//4,
                          tile_bgr.shape[1]//4: 3*tile_bgr.shape[1]//4]
        v = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)[...,2].mean()
        if v > 115:
            return Label.WHITE, min(0.95, 0.5 + (v-115)/140)
        else:
            return Label.BLACK, min(0.95, 0.5 + (115-v)/115)

    def predict_batch(self, tiles_bgr):
        labels=[[Label.EMPTY]*8 for _ in range(8)]
        confs =[[1.0]*8 for _ in range(8)]
        for r in range(8):
            for c in range(8):
                lab, conf = self._heuristic(tiles_bgr[r][c])
                labels[r][c]=lab
                confs[r][c]=float(conf)
        return labels, confs
