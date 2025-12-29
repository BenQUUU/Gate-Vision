import os, time, json, threading

class EventLogger:
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def log(self, kind, **kwargs):
        rec = {"t": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": kind}
        rec.update(kwargs or {})
        line = json.dumps(rec, ensure_ascii=False)
        with self.lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        print(line)
