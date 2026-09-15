import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'inventory.db')

def deduct_active():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all active loans
    cursor.execute("SELECT asset_id, SUM(quantity) as sum_qty FROM loans WHERE status = 'ACTIVE' GROUP BY asset_id")
    active_loans = cursor.fetchall()
    
    for row in active_loans:
        asset_id = row['asset_id']
        qty = row['sum_qty']
        
        # Deduct this from EXISTENCIAINICIAL
        cursor.execute("UPDATE assets SET EXISTENCIAINICIAL = EXISTENCIAINICIAL - ? WHERE id = ?", (qty, asset_id))
        print(f"Deducted {qty} from asset {asset_id}")
    
    conn.commit()
    conn.close()
    print("Database consistency updated for available quantities.")

if __name__ == '__main__':
    deduct_active()
