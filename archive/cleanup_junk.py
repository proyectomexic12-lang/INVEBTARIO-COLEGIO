import sqlite3
import os
db_path = r"c:\Users\USUARIO\Desktop\inventario\desktop_app\inventory.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Delete records that are clearly junk from Excel headers/titles
junk_patterns = [
    "INVENTARIO GENERAL",
    "Código Artículo",
    "Fecha análisis%"
]

for pattern in junk_patterns:
    if "%" in pattern:
        cursor.execute("DELETE FROM assets WHERE description LIKE ?", (pattern,))
        cursor.execute("DELETE FROM assets WHERE code LIKE ?", (pattern,))
    else:
        cursor.execute("DELETE FROM assets WHERE description = ?", (pattern,))
        cursor.execute("DELETE FROM assets WHERE code = ?", (pattern,))

print(f"Deleted junk rows. Rows affected: {cursor.rowcount}")
conn.commit()
conn.close()
