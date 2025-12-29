import re, cv2, numpy as np

class OCREngine:
    def __init__(self, cfg):
        self.cfg = cfg
        self.engine = cfg["ocr"].get("engine", "tesseract")
        self.regex = re.compile(cfg["ocr"].get("whitelist_regex", r"^[A-Z0-9]{4,8}$"))
        self.psm = str(cfg["ocr"].get("tesseract_psm", 7))
        self.language = cfg["ocr"].get("paddle_language", "en")
        self._init_backends()

    def _init_backends(self):
        self.tess = None
        self.easy = None
        self.paddle = None
        if self.engine == "tesseract":
            try:
                import pytesseract
                self.tess = pytesseract
            except Exception as e:
                print("[OCR] pytesseract unavailable:", e)
        elif self.engine == "easyocr":
            try:
                import easyocr
                self.easy = easyocr.Reader(['en'], gpu=False)
            except Exception as e:
                print("[OCR] easyocr unavailable:", e)
        elif self.engine == "paddleocr":
            try:
                from paddleocr import PaddleOCR
                self.paddle = PaddleOCR(use_angle_cls=True, lang=self.language, show_log=False)
            except Exception as e:
                print("[OCR] paddleocr unavailable:", e)

    def preprocess(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if self.cfg["ocr"]["preprocess"].get("clahe", True):
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
        if self.cfg["ocr"]["preprocess"].get("denoise", True):
            gray = cv2.fastNlMeansDenoising(gray, h=10)
        # adaptive threshold
        thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, 31, 5)
        
        return thr

    def infer(self, plate_img):
        roi = self.preprocess(plate_img)
        text, conf = "", 0.0
        if self.tess is not None:
            cfg = f"--psm {self.psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            raw = self.tess.image_to_data(roi, config=cfg, output_type=self.tess.Output.DICT)
            # pick best word
            best_idx, best_conf = -1, -1
            for i, w in enumerate(raw["text"]):
                if w.strip():
                    c = int(raw["conf"][i]) if raw["conf"][i].isdigit() else -1
                    if c > best_conf:
                        best_conf = c
                        best_idx = i
            if best_idx >= 0:
                text = raw["text"][best_idx].strip().upper().replace(" ", "")
                conf = max(0.0, min(1.0, best_conf / 100.0))
        elif self.easy is not None:
            res = self.easy.readtext(roi)
            if res:
                # pick the longest
                res.sort(key=lambda x: len(x[1]), reverse=True)
                text = res[0][1].upper().replace(" ", "")
                conf = float(res[0][2])
        elif self.paddle is not None:
            # PaddleOCR inference
            res = self.paddle.ocr(roi, cls=True)
            if res and res[0]:  
                res = sorted(res[0], key=lambda x: len(x[1][0]), reverse=True)
                text = res[0][1][0].upper().replace(" ", "") 
                conf = float(res[0][1][1])
        valid = bool(self.regex.match(text)) if text else False
        return text, conf, valid, roi
