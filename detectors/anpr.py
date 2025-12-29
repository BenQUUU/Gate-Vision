import cv2, numpy as np, time

class ANPRDetector:
    def __init__(self, cfg, ocr_engine, logger):
        self.cfg = cfg
        self.ocr = ocr_engine
        self.log = logger
        self.model = None
        self._init_model()

        self.det_thr = cfg["detection"].get("conf_thr", 0.5)

        self.vote_text = []
        self.vote_window = 5

    def _init_model(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.cfg["detection"]["plate_model"], task='detect')
            print("[ANPR] YOLO model loaded.")
        except Exception as e:
            print("[ANPR] Could not load YOLO model:", e)
            self.model = None

    def detect_plate(self, frame):
        if self.model is None:
            return []

        res = self.model.predict(source=frame, conf=self.cfg["detection"].get("conf_thr",0.5),
                                 iou=self.cfg["detection"].get("iou_thr",0.45), verbose=False, device='cpu')[0]
        boxes = []
        for b in res.boxes:
            x1,y1,x2,y2 = map(int, b.xyxy[0].tolist())
            conf = float(b.conf[0].item())
            boxes.append((x1,y1,x2,y2,conf))
        # sort by conf desc
        boxes.sort(key=lambda x: x[4], reverse=True)
        return boxes

    @staticmethod
    def crop_with_margin(img, box, margin=0.05):
        h, w = img.shape[:2]
        x1,y1,x2,y2,_ = box
        dx = int((x2-x1)*margin); dy = int((y2-y1)*margin)
        x1 = max(0, x1-dx); y1 = max(0, y1-dy)
        x2 = min(w-1, x2+dx); y2 = min(h-1, y2+dy)
        return img[y1:y2, x1:x2]

    def recognize(self, frame):
        boxes = self.detect_plate(frame)
        if not boxes:
            self.vote_text = []
            return None, None, None, None

        plate_img = self.crop_with_margin(frame, boxes[0], margin=0.08)
        text, conf, valid, roi = self.ocr.infer(plate_img)
        if text:
            self.vote_text.append(text)
            if len(self.vote_text) > self.vote_window:
                self.vote_text.pop(0)
        else:
            self.vote_text = []

        return text, conf, valid, plate_img
