
import cv2, argparse
from .board_finder import BoardFinder

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cam", type=int, default=0)
    args=ap.parse_args()
    cap=cv2.VideoCapture(args.cam)
    finder=BoardFinder(800)
    print("Press q to quit")
    while True:
        ok,frame=cap.read()
        if not ok: break
        g=finder.detect_homography_aruco(frame)
        vis=frame.copy()
        if g:
            warp=finder.warp(frame,g)
            cv2.imshow("Warp", warp)
        cv2.imshow("Camera", vis)
        if cv2.waitKey(1)&0xFF==ord('q'): break
    cap.release(); cv2.destroyAllWindows()

if __name__=="__main__":
    main()
