import sqlite3
import json
import sys
import os

from database import db, dict_compatibility_factory

conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'inventory.db'))
conn.row_factory = dict_compatibility_factory
c = conn.cursor()

# Insert a temporary multi-unit asset
print("Inserting temporary multi-unit asset...")
db.cursor.execute("""
    INSERT INTO assets (
        CODIGO, DESCRIPCION, VALOR, FECHAADQUISICION, MARCA, SERIAL, UBICACION,
        CODCONTABLE, VIDAUTIL, DEPRECIACUMULADA, EXISTENCIAINICIAL, SEDE, is_disposed
    ) VALUES ('NX-TEST-MATH', 'Sillas de prueba matematica', 100000.0, '2026-06-07', 'Generic', 'SN-MATH', 'PRUEBAS',
              '101', 10, 150000.0, 5, 'Guaimaral', 0)
""")
db.conn.commit()

c.execute("SELECT id, EXISTENCIAINICIAL, VALOR, DEPRECIACUMULADA FROM assets WHERE CODIGO='NX-TEST-MATH' AND is_disposed=0 LIMIT 1")
original = c.fetchone()

print(f"Original BEFORE: qty={original['quantity']}, ini_u={original['initial_unit_value']}, ini_t={original['initial_total_value']}, depr={original['depreciation_rate']}, cur={original['current_value']}")

print("DISPOSING 1 UNIT:")
db.dispose_asset(original['id'], "Test Math", "2026-03-22", qty_to_dispose=1)

c.execute("SELECT id, EXISTENCIAINICIAL, VALOR, DEPRECIACUMULADA FROM assets WHERE id=?", (original['id'],))
new_active = c.fetchone()
print(f"Active AFTER: qty={new_active['quantity']}, ini_u={new_active['initial_unit_value']}, ini_t={new_active['initial_total_value']}, depr={new_active['depreciation_rate']}, cur={new_active['current_value']}")

c.execute("SELECT id, EXISTENCIAINICIAL, VALOR, DEPRECIACUMULADA FROM assets WHERE is_disposed=1 AND disposal_reason='Test Math'")
new_hist = c.fetchone()
print(f"Hist AFTER: qty={new_hist['quantity']}, ini_u={new_hist['initial_unit_value']}, ini_t={new_hist['initial_total_value']}, depr={new_hist['depreciation_rate']}, cur={new_hist['current_value']}")

# Clean up
print("Cleaning up temporary records...")
db.cursor.execute("DELETE FROM assets WHERE CODIGO='NX-TEST-MATH'")
db.conn.commit()
print("Cleaned up successfully.")
conn.close()
