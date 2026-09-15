import sqlite3
import os
db_path = r"c:\Users\USUARIO\Desktop\inventario\desktop_app\inventory.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Find and delete by checking if columns match the strings
cursor.execute("SELECT id, code, description FROM assets")
rows = cursor.fetchall()
to_delete = []
for row_id, code, desc in rows:
    if "INVENTARIO GENERAL" in str(code) or "INVENTARIO GENERAL" in str(desc):
        to_delete.append(row_id)
    elif "Código Artículo" in str(code) or "Código Artículo" in str(desc):
        to_delete.append(row_id)
    elif "Fecha análisis" in str(code) or "Fecha análisis" in str(desc):
        to_delete.append(row_id)

if to_delete:
    print(f"Deleting IDs: {to_delete}")
    for id_del in to_delete:
        cursor.execute("DELETE FROM assets WHERE id = ?", (id_del,))
    conn.commit()
    print(f"Deleted {len(to_delete)} rows.")
else:
    print("No junk rows found.")

conn.close()
