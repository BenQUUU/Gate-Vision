import numpy as np, cv2, time

def point_in_poly(pt, poly):
    return cv2.pointPolygonTest(np.array(poly, dtype=np.int32), pt, False) >= 0

class ZonesAB:
    def __init__(self, polyA, polyB, max_delay=4.0):
        self.polyA = polyA
        self.polyB = polyB
        self.max_delay = max_delay
        self.tA = None

    def update(self, bbox_center):
        now = time.monotonic()
        inA = point_in_poly(bbox_center, self.polyA)
        inB = point_in_poly(bbox_center, self.polyB)
        trigger = False

        if inA:
            self.tA = now

        if inB and self.tA is not None and (now - self.tA) <= self.max_delay:
            trigger = True
            self.tA = None

        # timeout
        if self.tA is not None and (now - self.tA) > self.max_delay:
            self.tA = None

        return trigger, inA, inB
