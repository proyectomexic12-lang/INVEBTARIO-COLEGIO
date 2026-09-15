import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'inventory.db')

def update_func():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Update all laptops that are NOT active loans to RECTOR
    cursor.execute("""
        UPDATE assets 
        SET FUNCIONARIO = 'RECTOR'
        WHERE id IN (
            SELECT a.id FROM assets a
            LEFT JOIN loans l ON a.id = l.asset_id AND l.status = 'ACTIVE'
            WHERE l.id IS NULL AND a.MARCA = 'Hewlett Packard'
        )
    """)
    print(f"Set RECTOR to {cursor.rowcount} free laptops.")
    
    # 2. Update all laptops that ARE active loans to the teacher's name
    cursor.execute("""
        SELECT l.asset_id, l.teacher_name 
        FROM loans l 
        WHERE l.status = 'ACTIVE'
    """)
    active_loans = cursor.fetchall()
    
    for row in active_loans:
        cursor.execute("UPDATE assets SET FUNCIONARIO = ? WHERE id = ?", (row['teacher_name'], row['asset_id']))
        print(f"Set FUNCIONARIO={row['teacher_name']} for asset {row['asset_id']}")
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    update_func()
