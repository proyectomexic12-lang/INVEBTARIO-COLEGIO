import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'inventory.db')

def update_date():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Update FECHAADQUISICION to '01/01/2016' for the recent laptops
    cursor.execute("""
        UPDATE assets 
        SET FECHAADQUISICION = '01/01/2016'
        WHERE VALOR = 850000.0 
          AND MARCA = 'Hewlett Packard'
          AND DESCRIPCION = 'PORTÁTIL'
          AND id >= 3111
    """)
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"Updated {affected} laptops with acquisition date 01/01/2016.")

if __name__ == '__main__':
    update_date()
