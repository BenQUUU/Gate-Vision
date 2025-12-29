import cv2
import threading
import time

class VideoSource:
    def __init__(self, src, width=None, height=None, fps=None):
        self.src = src
        self.width = width
        self.height = height
        self.fps = fps
        
        self.cap = None
        self.frame = None 
        self.lock = threading.Lock()
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        self.cap = cv2.VideoCapture(self.src)
        
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        reconnect_delay = 1.0

        while self.running:
            if self.cap is None or not self.cap.isOpened():
                time.sleep(reconnect_delay)
                self.cap = cv2.VideoCapture(self.src)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                if not self.cap.isOpened():
                    reconnect_delay = min(10.0, reconnect_delay * 1.5)
                    continue
                reconnect_delay = 1.0

            ret, frame = self.cap.read()

            if ret:
                timestamp = time.time()
                with self.lock:
                    self.frame = (frame, timestamp)
            else:
                self.cap.release()
                self.cap = None

    def get_frame(self):
        with self.lock:
            if self.frame is None:
                return None
            
            frame, timestamp = self.frame
            return (frame.copy(), timestamp)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()
