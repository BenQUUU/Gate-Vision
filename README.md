# Gate-Vision: Edge-AI Automatic Gate Opener

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![Platform: Raspberry Pi 5](https://img.shields.io/badge/platform-Raspberry%20Pi%205-red.svg)
![AI: YOLOv8 / YOLOv11](https://img.shields.io/badge/AI-YOLOv8%20/%20YOLOv11-green.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)

**Gate-Vision** is a high-performance, asynchronous ANPR (Automatic Number Plate Recognition) system designed specifically for edge computing on the **Raspberry Pi 5**. It utilizes deep learning for vehicle plate detection and OCR for character recognition to automate gate access control for private properties and parking lots.

---

## 🚀 Key Features
* **Asynchronous Processing:** Powered by `asyncio` to ensure smooth video capture and concurrent AI inference without blocking the main thread.
* **Real-time ANPR:** Optimized YOLO inference engine for detecting license plates with ultra-low latency on ARM64 architecture.
* **Smart Access Logic:** Whitelist-based authorization with configurable confidence thresholds, regex validation, and cooldown management.
* **Hardware Integration:** Direct control over GPIO relays for industrial gate actuators and signal lights.
* **Industrial Logging:** Separated diagnostic system logs and secure event logs for entry auditing.

## 🛠 Tech Stack
* **Language:** Python 3.11+
* **Deep Learning:** Ultralytics YOLOv8/v11 (Object Detection)
* **Computer Vision:** OpenCV (Image Preprocessing, Morphological Filtering, and Overlays)
* **OCR Engine:** Tesseract OCR / PaddleOCR
* **Hardware:** Raspberry Pi 5 (4GB Recommended), RPi Camera Module 3 or USB HD Webcam

---

## 🏗 System Architecture
The application follows a modular "Producer-Consumer" pattern to maximize the efficiency of the Raspberry Pi 5:

1.  **Video Source:** Captures high-definition frames and manages a frame buffer.
2.  **Detection Layer:** YOLO model identifies the License Plate (LP) bounding box.
3.  **Refinement Layer:** Grayscale conversion, thresholding, and perspective correction of the plate region.
4.  **Recognition Layer:** OCR engine extracts alphanumeric characters from the refined image.
5.  **Logic Layer:** Validates the result against `whitelist.txt` and checks the cooldown state.
6.  **Actuation Layer:** Sends a signal to the GPIO controller to trigger the gate relay.

---

## 📊 Benchmarks (Raspberry Pi 5)
*Performance measurements based on YOLOv8n (ncnn/onnx quantized models) running on 4 CPU cores.*

| Component | Latency (ms) | Notes |
| :--- | :--- | :--- |
| **Plate Detection (YOLO)** | ~45ms | YOLOv8n-int8 |
| **OCR Processing** | ~180ms | Depending on image quality |
| **End-to-End Latency** | **~250ms** | Total time from capture to relay trigger |
| **Inference FPS** | **~20 FPS** | Optimized with skip-frame logic |

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone [https://github.com/BenQUUU/Gate-Vision.git](https://github.com/BenQUUU/Gate-Vision.git)
cd Gate-Vision
```
### 2. Prepare Environment
```bash
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```
### 3. Configuration
Edit `config.yaml` to match your hardware setup:
```yaml
cameras:
  in:
    source: 0
    fps: 30
ai:
  min_conf: 0.45        
gate:
  cooldown: 15.0         
performance:
  skip_frames: 5         
```

## ⚠️ Safety, Security & Disclaimer
This project is intended for educational purposes and private property access control.
* **Thermal Management**: Raspberry Pi 5 generates significant heat during AI inference. Use an active cooling solution to prevent thermal throttling.
* **Night Vision**: For 24/7 operation, an IR-sensitive camera and infrared illumination are required for reliable plate recognition.
* **Network Security**: It is strongly recommended to deploy this system on a secured IoT VLAN to prevent unauthorized access to the GPIO controller.

## 🛣 Roadmap
* [ ] Integration with Hailo-8L AI Accelerator for 60+ FPS inference.
* [ ] Web-based Dashboard for real-time monitoring and whitelist management.
* [ ] Support for multi-camera setups (Inbound/Outbound).





