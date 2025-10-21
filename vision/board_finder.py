
import cv2
import numpy as np
from dataclasses import dataclass
import yaml

@dataclass
class BoardGeometry:
    H: np.ndarray
    size: tuple[int,int]

class BoardFinder:
    def __init__(self, warp_size: int = 800):
        self.warp_w = warp_size
        self.warp_h = warp_size
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, cv2.aruco.DetectorParameters())

    def detect_homography_aruco(self, frame_bgr):
        corners, ids, _ = self.detector.detectMarkers(frame_bgr)
        if ids is None:
            return None
        ids = ids.flatten()
        centers = {}
        for c, i in zip(corners, ids):
            centers[int(i)] = c[0].mean(axis=0)
        needed = [0,1,2,3]
        if not all(k in centers for k in needed):
            return None
        src = np.float32([centers[0], centers[1], centers[2], centers[3]])
        dst = np.float32([[0,0],[self.warp_w,0],[self.warp_w,self.warp_h],[0,self.warp_h]])
        H = cv2.getPerspectiveTransform(src, dst)
        return BoardGeometry(H=H, size=(self.warp_w, self.warp_h))

    def warp(self, frame_bgr, geom: BoardGeometry):
        return cv2.warpPerspective(frame_bgr, geom.H, geom.size)

    def split_into_64(self, img):
        h,w = img.shape[:2]
        th, tw = h//8, w//8
        return [[img[r*th:(r+1)*th, c*tw:(c+1)*tw] for c in range(8)] for r in range(8)]

    def save_geom(self, path: str, geom: BoardGeometry):
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump({"H": geom.H.tolist(), "size": list(geom.size)}, f)

    def load_geom(self, path: str) -> BoardGeometry:
        with open(path, "r", encoding="utf-8") as f:
            d = yaml.safe_load(f)
        import numpy as np
        return BoardGeometry(H=np.array(d["H"], dtype=np.float32), size=tuple(d["size"]))
