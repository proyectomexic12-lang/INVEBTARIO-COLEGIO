import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'inventory.db')

def run_fix():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Update descriptions that contain "Acta", "Serial", or "Activo importado"
    # to simply "PORTÁTIL"
    cursor.execute("""
        UPDATE assets 
        SET DESCRIPCION = 'PORTÁTIL' 
        WHERE DESCRIPCION LIKE '%Acta%' 
           OR DESCRIPCION LIKE '%Serial%' 
           OR DESCRIPCION LIKE '%Activo importado%'
    """)
    
    rows_affected = cursor.rowcount
    
    # Because of sqlite's FTS (Full Text Search) virtual table we might also want to trigger
    # an update on assets_search if there are triggers, but typically triggers handle it.
    
    conn.commit()
    conn.close()
    print(f"Fixed {rows_affected} records in database.")

if __name__ == '__main__':
    run_fix()
