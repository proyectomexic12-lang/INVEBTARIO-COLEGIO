import sqlite3
db_path = r"c:\Users\USUARIO\Desktop\inventario\desktop_app\inventory.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Find all assets
cursor.execute("SELECT id, code, description, accounting_rubric_code FROM assets")
rows = cursor.fetchall()
to_delete = []

junk_terms = ["INVENTARIO", "CÓDIGO", "CODIGO", "FECHA ANÁLISIS", "FECHA ANALISIS", "RUBRO"]

for row_id, code, desc, acc in rows:
    combined = f"{code} {desc} {acc}".upper()
    if any(term in combined for term in junk_terms):
        to_delete.append(row_id)

if to_delete:
    print(f"Deleting {len(to_delete)} junk rows: {to_delete}")
    for id_del in to_delete:
        cursor.execute("DELETE FROM assets WHERE id = ?", (id_del,))
    conn.commit()
else:
    print("No junk rows found.")

conn.close()
