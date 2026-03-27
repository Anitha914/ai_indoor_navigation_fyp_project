import sqlite3
import matplotlib.pyplot as plt

DB_PATH = "data/map.db"

def load_map():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Load nodes (id, x, y)
    c.execute("SELECT id, x, y FROM nodes")
    nodes = c.fetchall()

    # Load edges (a, b)
    c.execute("SELECT a, b FROM edges")
    edges = c.fetchall()

    conn.close()
    return nodes, edges

def visualize_map():
    nodes, edges = load_map()

    if len(nodes) == 0:
        print("No nodes found! Run map_builder.py first.")
        return

    plt.figure(figsize=(8, 5))

    # Plot nodes
    for node_id, x, y in nodes:
        plt.scatter(x, y, s=120, color='blue')
        plt.text(x + 0.05, y + 0.05, f"{node_id}", fontsize=12)

    # Plot edges
    for a, b in edges:
        x1 = next(n[1] for n in nodes if n[0] == a)
        y1 = next(n[2] for n in nodes if n[0] == a)
        x2 = next(n[1] for n in nodes if n[0] == b)
        y2 = next(n[2] for n in nodes if n[0] == b)
        plt.plot([x1, x2], [y1, y2], 'k--', linewidth=1)

    plt.title("Indoor Navigation – Map Visualization")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    visualize_map()
