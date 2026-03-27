import cv2
import os
import argparse
import sqlite3

# ---------------- CONFIG ---------------- #
MODEL_PROTO = "models/MobileNetSSD_deploy.prototxt"
MODEL_WEIGHTS = "models/MobileNetSSD_deploy.caffemodel"
DB_PATH = "indoor_nav.db"

CONF_THRESHOLD = 0.5

# Class labels MobileNet SSD
CLASSES = [
    "background", "aeroplane", "bicycle", "bird", "boat",
    "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
    "dog", "horse", "motorbike", "person", "pottedplant",
    "sheep", "sofa", "train", "tvmonitor", "door", "bag", "fan", "window"
]

# ---------------------------------------- #

class Detector:
    def __init__(self):
        if not os.path.exists(MODEL_PROTO) or not os.path.exists(MODEL_WEIGHTS):
            raise FileNotFoundError("Model files not found in models/ folder")

        self.net = cv2.dnn.readNetFromCaffe(
            MODEL_PROTO,
            MODEL_WEIGHTS
        )

    def detect(self, frame):
        h, w = frame.shape[:2]

        blob = cv2.dnn.blobFromImage(
            frame, 0.007843, (300, 300), 127.5
        )
        self.net.setInput(blob)
        detections = self.net.forward()

        results = []

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > CONF_THRESHOLD:
                class_id = int(detections[0, 0, i, 1])
                label = CLASSES[class_id]

                box = detections[0, 0, i, 3:7] * [w, h, w, h]
                x1, y1, x2, y2 = box.astype("int")

                results.append((label, confidence, (x1, y1, x2, y2)))

        return results


def save_to_db(node_id, detections):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS objects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id INTEGER,
            object_name TEXT,
            confidence REAL
        )
    """)

    for obj, conf, _ in detections:
        cur.execute(
            "INSERT INTO objects (node_id, object_name, confidence) VALUES (?, ?, ?)",
            (node_id, obj, conf)
        )

    conn.commit()
    conn.close()


def run_live_detection(node_id):
    cap = cv2.VideoCapture(0)
    detector = Detector()

    print("Press 's' to save detections | 'q' to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        detections = detector.detect(frame)

        for label, conf, (x1, y1, x2, y2) in detections:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            text = f"{label}: {conf:.2f}"
            cv2.putText(
                frame, text, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2
            )

        cv2.imshow("Object Detection", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            save_to_db(node_id, detections)
            print(f"Saved {len(detections)} objects for node {node_id}")

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# ---------------- MAIN ---------------- #
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", type=int, required=True, help="Node ID")
    args = parser.parse_args()

    run_live_detection(args.node)
