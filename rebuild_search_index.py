import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), "desktop_app", "inventory.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()

print("Eliminando FTS5 viejo y trigger...")
cur.execute("DROP TRIGGER IF EXISTS assets_ai")
cur.execute("DROP TABLE IF EXISTS assets_search")
conn.commit()

print("Creando FTS5 nuevo...")
cur.execute("""
    CREATE VIRTUAL TABLE assets_search USING fts5(
        CODIGO,
        DESCRIPCION,
        MARCA,
        SERIAL,
        UBICACION,
        FUNCIONARIO,
        SEDE,
        content='assets',
        content_rowid='id'
    )
""")

cur.execute("""
    CREATE TRIGGER assets_ai AFTER INSERT ON assets BEGIN
        INSERT INTO assets_search(rowid, CODIGO, DESCRIPCION, MARCA, SERIAL, UBICACION, FUNCIONARIO, SEDE)
        VALUES (new.id, COALESCE(new.CODIGO,''), COALESCE(new.DESCRIPCION,''),
                COALESCE(new.MARCA,''), COALESCE(new.SERIAL,''),
                COALESCE(new.UBICACION,''), COALESCE(new.FUNCIONARIO,''), COALESCE(new.SEDE,''));
    END
""")
conn.commit()

print("Poblando con activos existentes...")
cur.execute("""
    INSERT INTO assets_search(rowid, CODIGO, DESCRIPCION, MARCA, SERIAL, UBICACION, FUNCIONARIO, SEDE)
    SELECT id,
        COALESCE(CODIGO,''),
        COALESCE(DESCRIPCION,''),
        COALESCE(MARCA,''),
        COALESCE(SERIAL,''),
        COALESCE(UBICACION,''),
        COALESCE(FUNCIONARIO,''),
        COALESCE(SEDE,'')
    FROM assets
""")
conn.commit()

cur.execute("SELECT COUNT(*) FROM assets")
total = cur.fetchone()[0]
print(f"Activos en BD: {total}")
print("LISTO - Busqueda instantanea reparada.")
conn.close()
