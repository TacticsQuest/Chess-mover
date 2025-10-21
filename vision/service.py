
from fastapi import FastAPI
from pydantic import BaseModel
import cv2
from .board_finder import BoardFinder, BoardGeometry
from .square_classifier import SquareClassifier
from .move_verifier import MoveVerifier

app=FastAPI(title="Chess Vision Service")
finder=BoardFinder(800)
geom: BoardGeometry | None = None
clf=SquareClassifier()
mv=MoveVerifier()

class CalibReq(BaseModel):
    cam:int=0
    save_path:str="board.yml"
    manual_points:list[list[float]]|None=None

@app.post("/vision/calibrate")
def calibrate(req:CalibReq):
    global geom
    cap=cv2.VideoCapture(req.cam)
    ok,frame=cap.read()
    cap.release()
    if not ok:
        return {"ok":False,"error":"camera read failed"}
    if req.manual_points:
        import numpy as np
        src=np.float32(req.manual_points)
        dst=np.float32([[0,0],[finder.warp_w,0],[finder.warp_w,finder.warp_h],[0,finder.warp_h]])
        import cv2
        H=cv2.getPerspectiveTransform(src,dst)
        geom=BoardGeometry(H=H,size=(finder.warp_w,finder.warp_h))
    else:
        g=finder.detect_homography_aruco(frame)
        if not g:
            return {"ok":False,"error":"aruco not found"}
        geom=g
    finder.save_geom(req.save_path, geom)
    return {"ok":True,"geom_path":req.save_path}

class ScanReq(BaseModel):
    cam:int=0
    geom_path:str="board.yml"

@app.post("/vision/scan")
def scan(req:ScanReq):
    global geom
    if geom is None:
        try:
            geom=finder.load_geom(req.geom_path)
        except Exception as e:
            return {"ok":False,"error":f"load geom failed: {e}"}
    cap=cv2.VideoCapture(req.cam)
    ok,frame=cap.read()
    cap.release()
    if not ok:
        return {"ok":False,"error":"camera read failed"}
    warped=finder.warp(frame, geom)
    tiles=finder.split_into_64(warped)
    labels,confs=clf.predict_batch(tiles)
    return {"ok":True,"labels":[[int(x) for x in row] for row in labels],"confs":confs}

class MoveReq(BaseModel):
    cam:int=0
    geom_path:str="board.yml"
    prev_labels:list[list[int]]

@app.post("/vision/move")
def move(req:MoveReq):
    sc=scan(ScanReq(cam=req.cam, geom_path=req.geom_path))
    if not sc.get("ok"): return sc
    prev=req.prev_labels
    curr=sc["labels"]
    mv_idx=mv.derive_move(prev,curr)
    return {"ok":True,"prev":prev,"curr":curr,"move_rc":mv_idx}
