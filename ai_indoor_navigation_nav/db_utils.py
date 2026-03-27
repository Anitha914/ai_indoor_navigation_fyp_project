# utils.py
import cv2
import numpy as np
import sqlite3
import os
from typing import Tuple, List, Dict

DB_PATH = os.path.join("data", "map.db")
os.makedirs("data", exist_ok=True)

def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            img_path TEXT,
            keypoints BLOB,
            descriptors BLOB,
            x REAL,
            y REAL,
            embedding BLOB
        );
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            a INTEGER,
            b INTEGER,
            weight REAL,
            FOREIGN KEY(a) REFERENCES nodes(id),
            FOREIGN KEY(b) REFERENCES nodes(id)
        );
    ''')
    # in db_utils.py (add after nodes and edges creation)
    c.execute('''
    CREATE TABLE IF NOT EXISTS node_embeddings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        node_id INTEGER,
        embedding BLOB,
        FOREIGN KEY(node_id) REFERENCES nodes(id)
    );
    ''')
    conn.commit()
    conn.close()

def array_to_blob(arr: np.ndarray) -> bytes:
    return arr.tobytes()

def blob_to_array(blob: bytes, dtype=np.uint8) -> np.ndarray:
    return np.frombuffer(blob, dtype=dtype)

# small helper to draw bbox
def draw_bbox(img, box, label=None, conf=None):
    x, y, w, h = box
    cv2.rectangle(img, (x,y), (x+w, y+h), (0,255,0), 2)
    if label or conf:
        text = f"{label or ''} {conf:.2f}" if conf else label or ""
        cv2.putText(img, text, (x,y-8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
    return img
