import sqlite3
import os

DB_PATH = os.path.join("data", "map.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Add new columns safely
try:
    cur.execute("ALTER TABLE nodes ADD COLUMN heading REAL DEFAULT 0")
except sqlite3.OperationalError:
    print("Column 'heading' already exists")

try:
    cur.execute("ALTER TABLE nodes ADD COLUMN type TEXT")
except sqlite3.OperationalError:
    print("Column 'type' already exists")

conn.commit()
conn.close()

print("Database schema updated successfully")
