import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'inventory.db')

def check_db():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("--- LOANS ---")
    cursor.execute("SELECT id, asset_id, status FROM loans")
    for row in cursor.fetchall():
        print(dict(row))
        
    print("\n--- RETURNED LOANS ---")
    cursor.execute("""
            SELECT l.id, l.asset_id, l.status, a.DESCRIPCION as description 
            FROM loans l 
            JOIN assets a ON l.asset_id = a.id
            WHERE l.status='RETURNED'
    """)
    for row in cursor.fetchall():
        print(dict(row))

if __name__ == '__main__':
    check_db()
