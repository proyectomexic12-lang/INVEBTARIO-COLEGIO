import sqlite3
import os

def fix_database():
    db_path = os.path.join(os.path.dirname(__file__), "inventory.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get current columns
    cursor.execute("PRAGMA table_info(assets)")
    current_cols = [row[1] for row in cursor.fetchall()]
    
    expected_cols = [
        ("accounting_rubric_code", "TEXT"),
        ("accounting_rubric_desc", "TEXT"),
        ("brand", "TEXT"),
        ("model", "TEXT"),
        ("serial_number", "TEXT"),
        ("color", "TEXT"),
        ("dimensions", "TEXT"),
        ("observations", "TEXT"),
        ("initial_unit_value", "REAL"),
        ("quantity", "INTEGER"),
        ("initial_total_value", "REAL"),
        ("depreciation_rate", "REAL"),
        ("current_value", "REAL"),
        ("entry_date", "TEXT"),
        ("service_date", "TEXT"),
        ("useful_life_remaining", "INTEGER"),
        ("conservation_state", "TEXT"),
        ("origin", "TEXT"),
        ("current_activity", "TEXT"),
        ("is_disposed", "INTEGER DEFAULT 0"),
        ("disposal_date", "TEXT"),
        ("disposal_reason", "TEXT")
    ]
    
    for col_name, col_type in expected_cols:
        if col_name not in current_cols:
            print(f"Adding missing column: {col_name}")
            try:
                cursor.execute(f"ALTER TABLE assets ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
                
    conn.commit()
    conn.close()
    print("Database fix completed.")

if __name__ == "__main__":
    fix_database()
