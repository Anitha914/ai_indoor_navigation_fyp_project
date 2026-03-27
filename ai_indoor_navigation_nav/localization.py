import cv2, numpy as np
from embeddings import compute_embedding
from db_utils import get_db_conn

def localize(frame):
    emb = compute_embedding(frame)

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, embedding FROM nodes")

    best_sim = -1
    best_node = None

    for node_id, blob in cur.fetchall():
        node_emb = np.frombuffer(blob, dtype=np.float32)

        # Normalize embeddings
        emb_norm = emb / np.linalg.norm(emb)
        node_emb_norm = node_emb / np.linalg.norm(node_emb)

        # Cosine similarity
        sim = np.dot(emb_norm, node_emb_norm)

        if sim > best_sim:
            best_sim = sim
            best_node = node_id

    conn.close()

    # 🔥 KEY IDEA FROM REPO
    if best_sim > 0.70:   # tune 0.6–0.75
        print(f"[LOCALIZATION] Node {best_node}, similarity {best_sim:.3f}")
        return best_node,best_sim
    else:
        print(f"[LOCALIZATION] No match, similarity {best_sim:.3f}")
        return None,best_sim