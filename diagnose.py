import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "desktop_app"))
from database import db


print("=== DIAGNOSTICO NEXUS ===")
print(f"Activos activos: {db.get_active_assets_count()}")

db.cursor.execute("SELECT COUNT(*) FROM assets WHERE is_disposed=1")
print(f"Bajas: {db.cursor.fetchone()[0]}")

db.cursor.execute("SELECT name FROM dependencies")
deps = [r[0] for r in db.cursor.fetchall()]
print(f"Dependencias ({len(deps)}): {deps}")

db.cursor.execute("PRAGMA table_info(loans)")
loan_cols = [r[1] for r in db.cursor.fetchall()]
print(f"Columnas loans: {loan_cols}")

db.cursor.execute("SELECT COUNT(*) FROM settings")
print(f"Settings registrados: {db.cursor.fetchone()[0]}")

db.cursor.execute("SELECT key, value FROM settings")
for r in db.cursor.fetchall():
    print(f"  {r[0]}: {r[1]}")

print("\n=== VERIFICACION DE METODOS DB ===")
methods = ["get_active_assets","get_active_loans","get_global_stats","get_all_dep_stats","bulk_add_assets","dispose_asset"]
for m in methods:
    print(f"  {'OK' if hasattr(db, m) else 'FALTA'} -> db.{m}")
