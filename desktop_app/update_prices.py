import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'inventory.db')

def update_laptops():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Update VALOR and DEPRECIACUMULADA to 850000.0 for the recent imports
    cursor.execute("""
        UPDATE assets 
        SET VALOR = 850000.0, 
            DEPRECIACUMULADA = 850000.0
        WHERE VALOR = 0.0 
          AND MARCA = 'Hewlett Packard'
          AND DESCRIPCION = 'PORTÁTIL'
    """)
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"Updated {affected} laptops with price 850,000.0 and 100% depreciation.")

if __name__ == '__main__':
    update_laptops()
