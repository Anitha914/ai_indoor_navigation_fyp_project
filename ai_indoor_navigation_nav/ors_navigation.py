import cv2
import torch
import time
import numpy as np
import threading
from outdoor.tts import SpeechService


# CONFIG
CAM_INDEX = 0
CONF_THRESHOLD = 0.25
FOCAL_LENGTH = 1280.0  # replace with your calibrated focal length (pixels)
KNOWN_WIDTHS = {
    "person": 0.5,
    "bicycle": 0.5,
    "car": 1.6,
    "motorbike": 0.8,
    "bus": 2.5,
    "truck": 2.5,
    "dog": 0.4,
    "cat": 0.3,
    "chair": 0.5,
    "bench": 1.2,
    "bottle": 0.07,
    "backpack": 0.4,
    "suitcase": 0.5,
    "table": 1.2,
    "potted plant": 0.5,
    "stop sign": 0.6,
    "traffic light": 0.3
}

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
model.conf = CONF_THRESHOLD

tts = SpeechService()
cooldown = 2.0  # seconds between repeats per object
last_spoken = {}  # track last spoken time for each class

def estimate_distance(real_width_m, focal_length_px, pixel_width):
    if pixel_width == 0:
        return None
    return (real_width_m * focal_length_px) / pixel_width

def safe_speak(text):
    """Speak using a separate thread to avoid run loop conflicts."""
    threading.Thread(target=tts.speak, args=(text,)).start()

def run_detector(focal_length=FOCAL_LENGTH, cam_idx=CAM_INDEX):
    cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
    time.sleep(1)

    if not cap.isOpened():
        print("❌ Camera not opened. Check CAM_INDEX.")
        return

    print("🎥 Detector started. Press 'q' to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to read frame.")
            break

        results = model(frame)
        df = results.pandas().xyxy[0]

        for _, row in df.iterrows():
            cls = row['name']
            conf = float(row['confidence'])
            x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
            pixel_w = x2 - x1

            # Estimate distance if known
            dist_m = None
            if cls in KNOWN_WIDTHS:
                dist_m = estimate_distance(KNOWN_WIDTHS[cls], focal_length, pixel_w)

            # Draw bounding box
            label = f"{cls} {conf:.2f}"
            if dist_m:
                label += f" {dist_m:.2f}m"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Speak with cooldown
            now = time.time()
            last_time = last_spoken.get(cls, 0)
            if now - last_time > cooldown:
                if dist_m:
                    safe_speak(f"{cls} ahead {dist_m:.1f} meters")
                else:
                    safe_speak(f"{cls} ahead")
                last_spoken[cls] = now

        cv2.imshow("Detector (press q to quit)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Quitting detector...")
            break

    cap.release()
    cv2.destroyAllWindows()


try:
    # try to reuse existing model object if defined
    model
except NameError:
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
    model.conf = 0.35

def run_once(frame):

    results = model(frame)
    df = results.pandas().xyxy[0]

    out = []

    for _, row in df.iterrows():

        cls = row['name']
        conf = float(row['confidence'])

        x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
        pixel_w = x2 - x1

        dist_m = None
        if cls in KNOWN_WIDTHS and pixel_w > 0:
            dist_m = (KNOWN_WIDTHS[cls] * FOCAL_LENGTH) / pixel_w

        out.append({
            "class": cls,
            "confidence": conf,
            "bbox": [x1, y1, x2, y2],
            "pixel_width": pixel_w,
            "distance_m": dist_m
        })

    return out