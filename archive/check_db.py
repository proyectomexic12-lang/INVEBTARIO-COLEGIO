import sqlite3
import os
db_path = r"c:\Users\USUARIO\Desktop\inventario\desktop_app\inventory.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT id, code, description, dependency FROM assets LIMIT 20")
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()
