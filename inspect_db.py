import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), "desktop_app", "inventory.db")
conn = sqlite3.connect(DB)

cur = conn.cursor()

cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','trigger') ORDER BY name")
objects = cur.fetchall()
print("OBJETOS EN DB:")
for name, typ in objects:
    print(f"  [{typ.upper()}] {name}")

# Verificar FTS5 shadow tables
cur.execute("SELECT name FROM sqlite_master WHERE name LIKE 'assets_search%'")
fts = cur.fetchall()
print("\nFTS5 shadow tables:", [r[0] for r in fts])

conn.close()
