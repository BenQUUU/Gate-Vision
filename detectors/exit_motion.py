import cv2, numpy as np, time
from collections import deque
from utils.zones import ZonesAB

class ExitMotion:
    def __init__(self, cfg, logger):
        self.cfg = cfg
        self.log = logger
        z = cfg["zones_out"]
        self.zones = ZonesAB(z["A"], z["B"], max_delay=float(z.get("max_seconds_A_to_B", 4)))
        self.bg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=64, detectShadows=True)
        self.min_area = int(z.get("min_bbox_area", 12000))
        self.min_speed = float(z.get("min_speed_px_per_s", 0))

        self.track = deque(maxlen=10)

    def process(self, frame):
        fg = self.bg.apply(frame)
        fg = cv2.medianBlur(fg, 5)
        _, thr = cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)
        thr = cv2.dilate(thr, np.ones((5,5), np.uint8), iterations=2)

        contours, _ = cv2.findContours(thr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        best = None
        best_area = 0
        for c in contours:
            x,y,w,h = cv2.boundingRect(c)
            area = w*h
            if area > best_area and area >= self.min_area:
                best = (x,y,w,h); best_area = area

        if best is None:
            self.track.clear()
            return False, None, thr

        x,y,w,h = best
        cx, cy = x + w//2, y + h//2
        self.track.append((time.monotonic(), cx, cy))

        speed_ok = True
        if self.min_speed > 0 and len(self.track) >= 2:
            t0,x0,y0 = self.track[0]
            t1,x1,y1 = self.track[-1]
            dt = max(1e-3, (t1 - t0))
            v = ((x1-x0)**2 + (y1-y0)**2) ** 0.5 / dt
            speed_ok = v >= self.min_speed

        trigger, inA, inB = self.zones.update((cx, cy))
        should_open = bool(trigger and speed_ok)
        return should_open, (x,y,w,h), thr
