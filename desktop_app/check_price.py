import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'inventory.db')

def inspect_db():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("--- Typical Laptops ---")
    cursor.execute("SELECT DESCRIPCION, MARCA, SERIAL, VALOR, DEPRECIACUMULADA, FECHAADQUISICION, VIDAUTIL FROM assets WHERE DESCRIPCION LIKE '%PORT%' OR DESCRIPCION LIKE '%COMPUTADOR%' LIMIT 5")
    for row in cursor.fetchall():
        print(dict(row))
        
    print("\n--- The recent loans ---")
    cursor.execute("SELECT id, CODIGO, DESCRIPCION, MARCA, VALOR, DEPRECIACUMULADA, FECHAADQUISICION, VIDAUTIL FROM assets WHERE id >= 3111")
    for row in cursor.fetchall():
        print(dict(row))

if __name__ == '__main__':
    inspect_db()
