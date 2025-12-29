import asyncio, time, os, re, yaml, cv2
import numpy as np
from utils.video import VideoSource
from utils.log import EventLogger
from detectors.ocr_backend import OCREngine
from detectors.anpr import ANPRDetector
from detectors.exit_motion import ExitMotion
from gate.controller import GateController

def load_cfg(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def draw_overlay(frame, text, pos=(10,30)):
    cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2, cv2.LINE_AA)

async def loop_in_camera(cfg, logger, gate):
    cam_cfg = cfg["cameras"]["in"]
    vs = VideoSource(cam_cfg["source"], cam_cfg["width"], cam_cfg["height"], cam_cfg["fps"])
    vs.start()
    ocr = OCREngine(cfg)
    anpr = ANPRDetector(cfg, ocr, logger)

    whitelist_path = cfg["paths"]["whitelist_file"]
    os.makedirs(os.path.dirname(whitelist_path), exist_ok=True)

    try:
        with open(whitelist_path, "r", encoding="utf-8") as f:
            wl = {ln.strip().upper() for ln in f if ln.strip()}
    except FileNotFoundError:
            wl = set()
    
    last_open_plate = None
    last_seen_time = 0
    cooldown = 10.0
    
    skip_frames = 5  
    frame_counter = 0

    current_text = None
    current_conf = 0.0
    current_valid = False
    current_plate_img = None
    current_whitelisted = False

    while True:
        frame_and_ts = vs.get_frame()
        if frame_and_ts is None:
            await asyncio.sleep(0.03)
            continue
        try:
            frame, capture_time = frame_and_ts
        except ValueError:
            continue

        frame_counter += 1

        if frame_counter % skip_frames == 0:
            text, conf, valid, plate_img = anpr.recognize(frame)
            
            current_text = text
            current_conf = conf
            current_valid = valid
            current_plate_img = plate_img
            
            if current_text and current_valid:
                current_whitelisted = current_text in wl
            else:
                current_whitelisted = False

        should_open = False
        
        if current_text and current_valid and current_whitelisted and current_conf >= 0.3:
            if last_open_plate == current_text:
                if capture_time - last_seen_time > cooldown:
                    should_open = True
            else:
                should_open = True

        if should_open:
            ok = await gate.request_open("in", reason=f"ANPR {current_text} conf={current_conf:.2f}")
            if ok:
                logger.log("open_by_in", plate=current_text, conf=current_conf)
                last_open_plate = current_text
                last_seen_time = capture_time # Resetujemy timer

        if current_text and current_valid and last_open_plate == current_text:
            last_seen_time = capture_time

        if cfg["debug"]["draw_overlays"]:
            if current_text:
                status = 'WL' if current_whitelisted else 'NO-WL'
                draw_overlay(frame, f"PLATE: {current_text} ({current_conf:.2f}) {status}", (10,30))
            
            color = (0, 255, 0) if should_open else (0, 0, 255)
            cv2.rectangle(frame, (10,50), (220,80), color, 2)
            draw_overlay(frame, f"STATE: {gate.state}", (10,110))

        if cfg["debug"]["show_windows"]:
            cv2.imshow("IN", frame)
            if cv2.waitKey(1) == 27: break

        await asyncio.sleep(0.01)

async def main():
    cfg = load_cfg("config.yaml")
    logger = EventLogger(cfg["paths"]["log_file"])
    gate = GateController(cfg, logger)

    tasks = [
        asyncio.create_task(loop_in_camera(cfg, logger, gate)),
        #asyncio.create_task(loop_out_camera(cfg, logger, gate)),
    ]

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    asyncio.run(main())
