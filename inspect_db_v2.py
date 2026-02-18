import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "db", "health_companion.db")
OUTPUT_FILE = "schema_utf8.txt"

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"Tables: {[t[0] for t in tables]}\n")
        
        for table_name in tables:
            t = table_name[0]
            f.write(f"\n--- Schema for {t} ---\n")
            cursor.execute(f"PRAGMA table_info({t})")
            columns = cursor.fetchall()
            for col in columns:
                f.write(str(col) + "\n")
    print(f"Schema written to {OUTPUT_FILE}")
            
except Exception as e:
    print(f"Error: {e}")
