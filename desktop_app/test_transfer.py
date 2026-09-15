import sqlite3
import os
import sys

# Agregamos la ruta
sys.path.append(os.path.dirname(__file__))

from database import DatabaseManager, AssetRepository, SettingRepository, AuditRepository

def test_transfer():
    db = DatabaseManager('inventory.db')
    settings = SettingRepository(db)
    audit = AuditRepository(db)
    asset_repo = AssetRepository(db, settings, audit)
    
    # Try to transfer asset 3111 to AULA 1
    asset_id = 3111
    res = asset_repo.transfer_asset(asset_id, "AULA 1")
    print(f"Transfer result: {res}")
    
    cursor = db.cursor
    cursor.execute("SELECT UBICACION FROM assets WHERE id=?", (asset_id,))
    print(f"Current location: {cursor.fetchone()}")

if __name__ == '__main__':
    test_transfer()
