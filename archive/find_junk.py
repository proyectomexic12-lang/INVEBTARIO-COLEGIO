import sqlite3
db_path = r"c:\Users\USUARIO\Desktop\inventario\desktop_app\inventory.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT id, code, description, accounting_rubric_code, dependency FROM assets")
rows = cursor.fetchall()
for row in rows:
    # Print if it looks like junk
    id, code, desc, acc, dep = row
    if any(k in str(code) or k in str(desc) or k in str(acc) for k in ["INVENTARIO", "Código", "Fecha análisis", "Rubro"]):
        print(f"JUNK FOUND: {row}")
conn.close()
