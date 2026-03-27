import cv2, sqlite3, time
from embeddings import compute_embedding
from db_utils import get_db_conn
import numpy as np

def add_node(name):
    cap = cv2.VideoCapture(0)
    frames = []

    print(f"\n📸 Move camera around for {name}")
    print("Press 'c' to capture, 'q' to finish")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        cv2.imshow("Capture View", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):
            frames.append(frame.copy())
            print(f"Captured frame {len(frames)}")
            cv2.imwrite(f"debug_{name}_{len(frames)}.jpg", frame)

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if len(frames) == 0:
        print("No frames captured!")
        return None

    embedding = np.mean([compute_embedding(f) for f in frames], axis=0)

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO nodes (name, x, y, embedding) VALUES (?, ?, ?, ?)",
        (name, 0, 0, embedding.tobytes())
    )
    node_id = cur.lastrowid
    conn.commit()
    conn.close()

    print(f"✅ Saved node {node_id} ({name})")
    return node_id

# def add_node(name):
#     cap = cv2.VideoCapture(0)
#     frames = []

#     print(f"Capturing images for {name}...")
#     for i in range(5):
#         ret, frame = cap.read()
#         if not ret:
#             continue
#         frames.append(frame)
#         time.sleep(0.2)

#     cap.release()

#     # Compute average embedding
#     embedding = np.mean([compute_embedding(f) for f in frames], axis=0)

#     conn = get_db_conn()
#     cur = conn.cursor()

#     # Insert node into nodes table
#     cur.execute("INSERT INTO nodes (name, x, y) VALUES (?, ?, ?)",
#                 (name, 0, 0))
#     node_id = cur.lastrowid

#     # Insert embedding into node_embeddings table
#     cur.execute("INSERT INTO node_embeddings (node_id, embedding) VALUES (?, ?)",
#                 (node_id, embedding.tobytes()))

#     conn.commit()
#     conn.close()
#     print(f"Saved node {node_id} ({name})")
#     return node_id

from db_utils import get_db_conn

def add_edge(a, b, weight=1):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO edges (a, b, weight) VALUES (?, ?, ?)", (a, b, weight))
    conn.commit()
    conn.close()
    print(f"Connected {a} <--> {b}")