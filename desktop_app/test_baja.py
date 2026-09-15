from database import DatabaseManager, AssetRepository, SettingRepository, AuditRepository
db_manager = DatabaseManager()
setting_repo = SettingRepository(db_manager)
audit_repo = AuditRepository(db_manager)
asset_repo = AssetRepository(db_manager, setting_repo, audit_repo)

db_manager.cursor.execute("SELECT * FROM assets WHERE is_disposed=0 LIMIT 1")
row = db_manager.cursor.fetchone()
if row:
    dep = row['dependency']
    print(f"Testing on dependency: {dep}")
    rows, units, init_val, val = asset_repo.get_dep_stats(dep)
    print(f"BEFORE: Dep Stats -> Rows: {rows}, Units: {units}, Real Value: {val}")
    
    # Try a partial Baja
    qty = int(row['quantity'] or 1)
    if qty == 1:
        print("Asset only has 1 unit, doing a total baja instead.")
        asset_repo.dispose_asset(row['id'], "Test Dispose", "2026-03-22")
    else:
        print(f"Asset has {qty} units, disposing 1.")
        asset_repo.dispose_asset(row['id'], "Test Partial Dispose", "2026-03-22", qty_to_dispose=1)
        
    rows2, units2, init_val2, val2 = asset_repo.get_dep_stats(dep)
    print(f"AFTER:  Dep Stats -> Rows: {rows2}, Units: {units2}, Real Value: {val2}")
    print(f"DIFFERENCE: Units: {units - units2}, Value: {val - val2}")
    
    # Revert the test
    db_manager.cursor.execute("UPDATE assets SET is_disposed=0, EXISTENCIAINICIAL=? WHERE id=?", (qty, row['id']))
    db_manager.cursor.execute("DELETE FROM assets WHERE is_disposed=1 AND disposal_reason LIKE 'Test%'")
    db_manager.conn.commit()
    print("Test reverted.")
