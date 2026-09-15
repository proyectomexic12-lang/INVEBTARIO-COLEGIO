import sqlite3
import os
import sys
import threading
import functools
import json
from datetime import datetime

class CompatibilityRow(dict):
    def __init__(self, d, col_names):
        super().__init__(d)
        self._col_names = col_names
        
    def __getitem__(self, key):
        if isinstance(key, int):
            if 0 <= key < len(self._col_names):
                return super().__getitem__(self._col_names[key])
            raise IndexError("Row index out of range")
        return super().__getitem__(key)
        
    def get(self, key, default=None):
        try:
            return self[key]
        except (KeyError, IndexError):
            return default

def dict_compatibility_factory(cursor, row):
    col_names = [col[0] for col in cursor.description]
    d = {col_names[idx]: row[idx] for idx in range(len(col_names))}
    
    # If the dictionary represents an asset row (check major fields)
    if any(k in d for k in ('DESCRIPCION', 'EXISTENCIAINICIAL', 'VALOR', 'CODIGO', 'UBICACION')):
        # Calculate derived values
        val = float(d.get('VALOR') or 0.0)
        raw_qty = d.get('EXISTENCIAINICIAL')
        try:
            qty = int(raw_qty) if raw_qty is not None and str(raw_qty).strip() != '' else 1
        except (ValueError, TypeError):
            qty = 1
        val_tot = val * qty
        depr = float(d.get('DEPRECIACUMULADA') or 0.0)
        val_cur = max(0.0, val_tot - depr)
        
        # Add English/lowercase compatibility fields
        d['id'] = d.get('id')
        d['code'] = d.get('CODIGO')
        d['accounting_rubric_code'] = d.get('CODCONTABLE')
        d['accounting_rubric_desc'] = 'GENERAL'
        d['description'] = d.get('DESCRIPCION')
        d['brand'] = d.get('MARCA') or 'N/A'
        d['model'] = 'N/A'
        d['serial_number'] = d.get('SERIAL') or 'N/A'
        d['color'] = 'N/A'
        d['dimensions'] = 'N/A'
        d['observations'] = 'Migrado de Excel'
        d['initial_unit_value'] = val
        d['quantity'] = qty
        d['initial_total_value'] = val_tot
        d['depreciation_rate'] = depr
        d['current_value'] = val_cur
        d['entry_date'] = d.get('FECHAADQUISICION')
        d['service_date'] = d.get('FECHAADQUISICION')
        d['useful_life_remaining'] = d.get('VIDAUTIL') or 10
        d['conservation_state'] = d.get('conservation_state') or 'Bueno'
        d['origin'] = 'Propio'
        d['current_activity'] = 'En Uso'
        d['dependency'] = d.get('UBICACION')
        d['cod_depreciacion'] = d.get('CODDEPRECIACION')
        d['cod_gasto'] = d.get('CODGASTO')
        d['funcionario'] = d.get('FUNCIONARIO')
        d['identificacion'] = d.get('IDENTIFICACION')
        d['cod_grupo'] = d.get('CODGRUPO')
        d['cod_subgrupo'] = d.get('CODSUBGRUPO')
        d['tipo'] = d.get('TIPO')
        d['sede'] = d.get('SEDE')
        
    return CompatibilityRow(d, list(d.keys()))

UPDATE_MAP_KEYS = {
    'code': 'CODIGO',
    'CODIGO': 'CODIGO',
    'accounting_rubric_code': 'CODCONTABLE',
    'CODCONTABLE': 'CODCONTABLE',
    'description': 'DESCRIPCION',
    'DESCRIPCION': 'DESCRIPCION',
    'brand': 'MARCA',
    'MARCA': 'MARCA',
    'serial_number': 'SERIAL',
    'SERIAL': 'SERIAL',
    'initial_unit_value': 'VALOR',
    'VALOR': 'VALOR',
    'quantity': 'EXISTENCIAINICIAL',
    'EXISTENCIAINICIAL': 'EXISTENCIAINICIAL',
    'depreciation_rate': 'DEPRECIACUMULADA',
    'DEPRECIACUMULADA': 'DEPRECIACUMULADA',
    'entry_date': 'FECHAADQUISICION',
    'FECHAADQUISICION': 'FECHAADQUISICION',
    'useful_life_remaining': 'VIDAUTIL',
    'VIDAUTIL': 'VIDAUTIL',
    'dependency': 'UBICACION',
    'UBICACION': 'UBICACION',
    'cod_depreciacion': 'CODDEPRECIACION',
    'CODDEPRECIACION': 'CODDEPRECIACION',
    'cod_gasto': 'CODGASTO',
    'CODGASTO': 'CODGASTO',
    'funcionario': 'FUNCIONARIO',
    'FUNCIONARIO': 'FUNCIONARIO',
    'identificacion': 'IDENTIFICACION',
    'IDENTIFICACION': 'IDENTIFICACION',
    'cod_grupo': 'CODGRUPO',
    'CODGRUPO': 'CODGRUPO',
    'cod_subgrupo': 'CODSUBGRUPO',
    'CODSUBGRUPO': 'CODSUBGRUPO',
    'tipo': 'TIPO',
    'TIPO': 'TIPO',
    'sede': 'SEDE',
    'SEDE': 'SEDE',
    'is_disposed': 'is_disposed',
    'disposal_date': 'disposal_date',
    'disposal_reason': 'disposal_reason',
    'conservation_state': 'conservation_state'
}

def db_lock(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # We acquire lock on the db_manager object
        manager = self.db_manager if hasattr(self, 'db_manager') else self.manager
        with manager.lock:
            return func(self, *args, **kwargs)
    return wrapper

def lock_all_methods(cls):
    for attr_name, attr_value in list(cls.__dict__.items()):
        if callable(attr_value) and not attr_name.startswith("__") and attr_name != "_map_input_tuple":
            setattr(cls, attr_name, db_lock(attr_value))
    return cls

class DatabaseManager:
    def __init__(self, db_name="inventory.db"):
        self.lock = threading.RLock()
        
        # Smart database path resolution: supports dev environment, PyInstaller onedir, and installed location
        candidates = [
            # 1. Same directory as the executable (if frozen with PyInstaller)
            os.path.join(os.path.dirname(sys.executable), db_name) if getattr(sys, 'frozen', False) else None,
            # 2. Current working directory
            os.path.join(os.getcwd(), db_name),
            # 3. Same directory as database.py
            os.path.join(os.path.dirname(os.path.abspath(__file__)), db_name),
            # 4. Parent directory if inside _internal
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), db_name),
        ]
        
        chosen_path = None
        for c in candidates:
            if c and os.path.exists(c):
                chosen_path = c
                break
                
        if not chosen_path:
            if getattr(sys, 'frozen', False):
                chosen_path = os.path.join(os.path.dirname(sys.executable), db_name)
            else:
                chosen_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_name)
                
        self.db_path = chosen_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = dict_compatibility_factory
        self.cursor = self.conn.cursor()
        
        # PERFORMANCE & ULTRA-FLUIDITY TWEAKS
        self.cursor.execute("PRAGMA journal_mode=WAL")
        self.cursor.execute("PRAGMA synchronous=NORMAL")
        self.cursor.execute("PRAGMA foreign_keys=ON")
        self.cursor.execute("PRAGMA cache_size=-256000")
        self.cursor.execute("PRAGMA mmap_size=536870912")
        self.cursor.execute("PRAGMA temp_store=MEMORY")
        self.cursor.execute("PRAGMA count_changes=OFF")
        self.conn.commit()

        # Integrity quick check and self-healing for corrupted indexes
        try:
            self.cursor.execute("PRAGMA quick_check")
            chk = self.cursor.fetchone()
            chk_val = chk.get('quick_check') if isinstance(chk, dict) else (chk[0] if chk else 'ok')
            if chk_val and str(chk_val).lower() != 'ok':
                print(f"[DB] Inconsistencia de índices detectada ({chk_val}). Reparando con REINDEX...")
                self.cursor.execute("REINDEX")
                self.conn.commit()
        except Exception as e:
            print(f"[DB] Aviso en verificación de integridad: {e}")

        self.create_tables()
        self._run_migrations()

    def _run_migrations(self):
        """
        Sistema de control de versiones de esquema.
        Garantiza que la base de datos se actualice automáticamente 
        en futuras versiones sin perder datos.
        """
        self.cursor.execute("PRAGMA user_version")
        current_version = self.cursor.fetchone()['user_version']
        
        # Version 1: Add conservation_state if not exists
        if current_version < 1:
            import logger_config
            logger_config.global_logger.info("Migrando base de datos a versión 1...")
            self.cursor.execute("PRAGMA table_info(assets)")
            columns = [col['name'] for col in self.cursor.fetchall()]
            if 'conservation_state' not in columns:
                self.cursor.execute("ALTER TABLE assets ADD COLUMN conservation_state TEXT DEFAULT 'Bueno'")
            self.cursor.execute("PRAGMA user_version = 1")
            self.conn.commit()
            
        # Version 2: Future updates go here
        # if current_version < 2: ...

    def create_tables(self):
        # 1. Dependencies Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT,
                sede TEXT DEFAULT 'Guaimaral'
            )
        """)
        # Ensure 'sede' column exists if table existed previously
        self.cursor.execute("PRAGMA table_info(dependencies)")
        dep_cols = [r['name'] if isinstance(r, dict) else r[1] for r in self.cursor.fetchall()]
        if 'sede' not in dep_cols:
            try:
                self.cursor.execute("ALTER TABLE dependencies ADD COLUMN sede TEXT DEFAULT 'Guaimaral'")
                self.cursor.execute("UPDATE dependencies SET sede = 'Guaimaral' WHERE sede IS NULL OR sede = ''")
                self.conn.commit()
            except Exception as e:
                print(f"[DB] Error adding sede to dependencies: {e}")

        try:
            self.cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_dependencies_name_sede ON dependencies(name, sede)")
            # Clean up unwanted default dependencies like 'GENERAL' or 'SIN ASIGNAR'
            self.cursor.execute("DELETE FROM dependencies WHERE UPPER(TRIM(name)) IN ('GENERAL', 'SIN ASIGNAR', 'SIN DEPENDENCIAS')")
            self.cursor.execute("UPDATE assets SET UBICACION = 'SIN ASIGNAR' WHERE UPPER(TRIM(UBICACION)) = 'GENERAL'")
            self.conn.commit()
        except Exception:
            pass

        # Drop old assets table if it has the old 'description' column
        self.cursor.execute("PRAGMA table_info(assets)")
        columns = [r['name'] for r in self.cursor.fetchall()]
        if columns and 'description' in columns:
            print("Detected old schema. Dropping old assets table and dependent triggers/indexes for clean schema...")
            self.cursor.execute("DROP INDEX IF EXISTS idx_assets_speed_pivot")
            self.cursor.execute("DROP TRIGGER IF EXISTS assets_ai")
            self.cursor.execute("DROP TRIGGER IF EXISTS assets_ad")
            self.cursor.execute("DROP TRIGGER IF EXISTS assets_au")
            self.cursor.execute("DROP TABLE IF EXISTS assets_search")
            self.cursor.execute("DROP TABLE IF EXISTS assets")
            self.conn.commit()

        # 2. New Assets Table with Exact Uppercase Spanish Columns
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                CODIGO TEXT,
                DESCRIPCION TEXT NOT NULL,
                VALOR REAL DEFAULT 0,
                FECHAADQUISICION TEXT,
                MARCA TEXT,
                SERIAL TEXT,
                UBICACION TEXT,
                CODCONTABLE TEXT,
                VIDAUTIL INTEGER,
                CODDEPRECIACION TEXT,
                DEPRECIACUMULADA REAL DEFAULT 0,
                CODGASTO TEXT,
                FUNCIONARIO TEXT,
                IDENTIFICACION TEXT,
                CODGRUPO TEXT,
                CODSUBGRUPO TEXT,
                TIPO TEXT,
                EXISTENCIAINICIAL INTEGER DEFAULT 1,
                SEDE TEXT,
                is_disposed INTEGER DEFAULT 0,
                disposal_date TEXT,
                disposal_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. FTS5 Virtual Table for INSTANT SEARCH
        self.cursor.execute("SELECT sql FROM sqlite_master WHERE name='assets_search'")
        row = self.cursor.fetchone()
        rebuild_fts = False
        if row:
            sql = row['sql'] if 'sql' in row else row[0]
            if "description" in sql or "CODIGO" not in sql:
                self.cursor.execute("DROP TRIGGER IF EXISTS assets_ai")
                self.cursor.execute("DROP TRIGGER IF EXISTS assets_ad")
                self.cursor.execute("DROP TRIGGER IF EXISTS assets_au")
                self.cursor.execute("DROP TABLE IF EXISTS assets_search")
                rebuild_fts = True

        self.cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS assets_search USING fts5(
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
        
        # Triggers to sync FTS5 on INSERT, UPDATE, and DELETE
        self.cursor.execute("DROP TRIGGER IF EXISTS assets_ai")
        self.cursor.execute("DROP TRIGGER IF EXISTS assets_ad")
        self.cursor.execute("DROP TRIGGER IF EXISTS assets_au")

        self.cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS assets_ai AFTER INSERT ON assets BEGIN
                INSERT INTO assets_search(rowid, CODIGO, DESCRIPCION, MARCA, SERIAL, UBICACION, FUNCIONARIO, SEDE)
                VALUES (
                    new.id, 
                    COALESCE(new.CODIGO, ''), 
                    COALESCE(new.DESCRIPCION, ''), 
                    COALESCE(new.MARCA, ''), 
                    COALESCE(new.SERIAL, ''), 
                    COALESCE(new.UBICACION, ''), 
                    COALESCE(new.FUNCIONARIO, ''),
                    COALESCE(new.SEDE, '')
                );
            END
        """)

        self.cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS assets_ad AFTER DELETE ON assets BEGIN
                INSERT INTO assets_search(assets_search, rowid, CODIGO, DESCRIPCION, MARCA, SERIAL, UBICACION, FUNCIONARIO, SEDE)
                VALUES (
                    'delete', 
                    old.id, 
                    COALESCE(old.CODIGO, ''), 
                    COALESCE(old.DESCRIPCION, ''), 
                    COALESCE(old.MARCA, ''), 
                    COALESCE(old.SERIAL, ''), 
                    COALESCE(old.UBICACION, ''), 
                    COALESCE(old.FUNCIONARIO, ''),
                    COALESCE(old.SEDE, '')
                );
            END
        """)

        self.cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS assets_au AFTER UPDATE ON assets BEGIN
                INSERT INTO assets_search(assets_search, rowid, CODIGO, DESCRIPCION, MARCA, SERIAL, UBICACION, FUNCIONARIO, SEDE)
                VALUES (
                    'delete', 
                    old.id, 
                    COALESCE(old.CODIGO, ''), 
                    COALESCE(old.DESCRIPCION, ''), 
                    COALESCE(old.MARCA, ''), 
                    COALESCE(old.SERIAL, ''), 
                    COALESCE(old.UBICACION, ''), 
                    COALESCE(old.FUNCIONARIO, ''),
                    COALESCE(old.SEDE, '')
                );
                INSERT INTO assets_search(rowid, CODIGO, DESCRIPCION, MARCA, SERIAL, UBICACION, FUNCIONARIO, SEDE)
                VALUES (
                    new.id, 
                    COALESCE(new.CODIGO, ''), 
                    COALESCE(new.DESCRIPCION, ''), 
                    COALESCE(new.MARCA, ''), 
                    COALESCE(new.SERIAL, ''), 
                    COALESCE(new.UBICACION, ''), 
                    COALESCE(new.FUNCIONARIO, ''),
                    COALESCE(new.SEDE, '')
                );
            END
        """)

        if rebuild_fts:
            self.cursor.execute("""
                INSERT INTO assets_search(rowid, CODIGO, DESCRIPCION, MARCA, SERIAL, UBICACION, FUNCIONARIO, SEDE)
                SELECT id, COALESCE(CODIGO,''), COALESCE(DESCRIPCION,''), COALESCE(MARCA,''), COALESCE(SERIAL,''), COALESCE(UBICACION,''), COALESCE(FUNCIONARIO,''), COALESCE(SEDE,'')
                FROM assets
            """)

        # 4. Audit Log
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT,
                record_id INTEGER,
                action TEXT,
                old_data TEXT,
                new_data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Settings, Loans, Officials
        self.cursor.execute("PRAGMA table_info(officials)")
        cols = [r[1] for r in self.cursor.fetchall()]
        if cols and 'code' not in cols:
            self.cursor.execute("DROP TABLE IF EXISTS officials")

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS officials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                name TEXT,
                identification TEXT,
                address TEXT,
                phone TEXT,
                birth_place TEXT,
                birth_date TEXT,
                gender TEXT,
                civil_status TEXT,
                dependency TEXT,
                position TEXT,
                hire_date TEXT
            )
        """)
        self.cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS loans (id INTEGER PRIMARY KEY, asset_id INTEGER, quantity INTEGER, teacher_name TEXT, teacher_phone TEXT, start_date TEXT, expected_return_date TEXT, status TEXT, FOREIGN KEY(asset_id) REFERENCES assets(id))")
        self.cursor.execute("PRAGMA table_info(loans)")
        loan_cols = [row[1] if isinstance(row, (tuple, list)) else row['name'] for row in self.cursor.fetchall()]
        if 'teacher_phone' not in loan_cols:
            try:
                self.cursor.execute("ALTER TABLE loans ADD COLUMN teacher_phone TEXT DEFAULT ''")
                self.conn.commit()
            except Exception as e:
                print(f"[DB] Error adding teacher_phone to loans: {e}")

        # Alter table if missing conservation_state
        self.cursor.execute("PRAGMA table_info(assets)")
        columns = [row[1] for row in self.cursor.fetchall()]
        if 'conservation_state' not in columns:
            self.cursor.execute("ALTER TABLE assets ADD COLUMN conservation_state TEXT DEFAULT 'Bueno'")
            self.conn.commit()

        # Indices de alto rendimiento
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_speed_pivot ON assets(UBICACION, is_disposed)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_sede_disp ON assets(SEDE, is_disposed)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_codigo ON assets(CODIGO)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_loans_asset_status ON loans(asset_id, status)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_loans_status_ret ON loans(status, expected_return_date)")
        self.conn.commit()

    def backup_to_file(self, target_filepath):
        with self.lock:
            try:
                self.cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            except Exception:
                pass
            dest_conn = sqlite3.connect(target_filepath)
            try:
                self.conn.backup(dest_conn)
                return True
            finally:
                dest_conn.close()

    def restore_from_file(self, source_filepath):
        with self.lock:
            if not os.path.exists(source_filepath):
                raise FileNotFoundError(f"No se encontró el archivo: {source_filepath}")
            test_conn = sqlite3.connect(source_filepath)
            try:
                test_cursor = test_conn.cursor()
                test_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [r[0] for r in test_cursor.fetchall()]
                if 'assets' not in tables:
                    raise ValueError("El archivo seleccionado no es una copia válida del inventario (falta la tabla de activos).")
            finally:
                test_conn.close()

            src_conn = sqlite3.connect(source_filepath)
            try:
                src_conn.backup(self.conn)
                try:
                    self.cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                except Exception:
                    pass
                return True
            finally:
                src_conn.close()

    def optimize_database(self):
        with self.lock:
            try:
                self.cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                self.cursor.execute("VACUUM")
                self.cursor.execute("PRAGMA optimize")
                self.conn.commit()
                return True
            except Exception as e:
                print(f"[INVENTARIO] Error optimizando base de datos: {e}")
                return False


@lock_all_methods
class AuditRepository:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def log_event(self, table, record_id, action, old_data=None, new_data=None):
        try:
            sql = "INSERT INTO audit_log (table_name, record_id, action, old_data, new_data) VALUES (?, ?, ?, ?, ?)"
            self.db_manager.cursor.execute(sql, (table, record_id, action, json.dumps(old_data), json.dumps(new_data)))
            self.db_manager.conn.commit()
            return True
        except Exception as e:
            self.db_manager.conn.rollback()
            print(f"Error in log_event: {e}")
            return False

    def get_audit_logs(self):
        try:
            self.db_manager.cursor.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 200")
            return self.db_manager.cursor.fetchall()
        except Exception as e:
            print(f"Error querying audit logs: {e}")
            return []


@lock_all_methods
class SettingRepository:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_setting(self, key, default=None):
        try:
            self.db_manager.cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = self.db_manager.cursor.fetchone()
            if row:
                return row[0] if isinstance(row, (list, tuple)) else row.get('value')
            return default
        except Exception:
            return default

    def set_setting(self, key, value):
        try:
            self.db_manager.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
            self.db_manager.conn.commit()
            return True
        except Exception as e:
            self.db_manager.conn.rollback()
            print(f"Error setting configuration: {e}")
            return False

    def get_excel_keywords(self):
        defaults = {
            "code":     ["CÓDIGO ARTÍCULO", "CÓDIGO", "PLACA", "ID PATRIM", "CODIGO", "COD", "NUMERO PLACA"],
            "rubro":    ["RUBRO CONTABLE", "RUBRO CONTADOR", "RUBRO", "CATEGORÍA", "CATEGORIA"],
            "acc_code": ["CÓDIGO CONTABLE", "CODCONTABLE", "COD CONTABLE", "CUENTA"],
            "desc":     ["DESCRIPCIÓN", "DESCRIPCION", "ARTÍCULO", "ARTICULO", "NOMBRE", "DETALLE", "ELEMENTO", "BIEN"],
            "brand":    ["MARCA / DETALLE", "MARCA", "FABRICANTE"],
            "model":    ["REFERENCIA / MODELO", "MODELO", "REFERENCIA"],
            "serial":   ["SERIAL NO.", "SERIAL", "SERIE", "NRO SERIE", "NUMERO DE SERIE"],
            "color":    ["COLOR"],
            "qty":      ["CANTIDAD", "CANT", "UNIDADES", "EXISTENCIAINICIAL", "EXISTENCIAS"],
            "val_uni":  ["VALOR UNITARIO INICIAL", "VALOR UNITARIO", "COSTO UNIT", "VALOR", "PRECIO UNITARIO", "VALOR INICIAL"],
            "val_tot":  ["VALOR TOTAL INICIAL", "VALOR TOTAL", "COSTO TOTAL", "TOTAL"],
            "dep":      ["DEPENDENCIA", "UBICACIÓN", "UBICACION", "AREA", "SALON", "LUGAR"],
            "state":    ["ESTADO", "CONSERVACIÓN", "CONSERVACION", "ESTADO CONSERVACION"],
            "dims":     ["MEDIDAS FÍSICAS", "DIMENSIONES", "MEDIDAS"],
            "obs":      ["OBSERVACIONES / CARACTERÍSTICAS", "OBSERVACIONES", "OBS", "NOTAS"],
            "depr":     ["DEPRECIACIÓN", "DEPRECIACION", "DEPRECIACIÓN ACUMULADA", "DEPRECIACION ACUMULADA"],
            "val_cur":  ["VALOR ACTUAL", "VALOR CONTABLE", "VALOR PRESENTE", "VALOR EN LIBROS"],
            "date_in":  [
                "FECHA DE ADQUISICIÓN", "FECHA DE ADQUISICION", "FECHA ADQUISICIÓN", "FECHA ADQUISICION",
                "FECHA INGRESO", "FECHA DE INGRESO", "FECHA DE COMPRA", "FECHA COMPRA",
                "FECHA ADQ", "FECHA ADQ.", "F. ADQUISICION", "F. ADQUISICIÓN",
                "FECHA_ADQUISICION", "FECHA_DE_ADQUISICION", "FECHA_INGRESO", "FECHA",
                "ADQUISICION", "ADQUISICIÓN", "FECHA DE REGISTRO", "FECHA REGISTRO",
                "FECHAADQUISICION", "FECHA REG", "AÑO ADQUISICION", "ANIO ADQUISICION", "FECHA COMPROBANTE"
            ],
            "life":     ["VIDA ÚTIL REST.", "VIDA UTIL", "VIDAUTIL", "VIDA UTIL RESTANTE"],
            "origin":   ["ORIGEN", "FUENTE", "PROCEDENCIA"],
            "activity": ["ACTIVIDAD ACTUAL", "ESTATUS", "DESTINO"],
            "cod_depr": ["CODDEPRECIACION", "COD DEPRECIACION"],
            "depr_cum": ["DEPRECIACUMULADA", "DEPRECIACION ACUMULADA", "DEPRECIACONACUMULADA"],
            "cod_gasto":["CODGASTO", "COD GASTO"],
            "func":     ["FUNCIONARIO", "RESPONSABLE", "DOCENTE", "CUSTODIO", "ASIGNADO A"],
            "ident":    ["IDENTIFICACION", "CÉDULA", "CEDULA", "DOCUMENTO"],
            "grupo":    ["CODGRUPO", "GRUPO"],
            "subgrupo": ["CODSUBGRUPO", "SUBGRUPO"],
            "tipo":     ["TIPO", "TIPO ACTIVO"],
            "sede":     ["SEDE", "SEDE EDUCATIVA"]
        }
        try:
            val = self.get_setting("excel_keywords")
            if val:
                saved = json.loads(val)
                modified = False
                for k, default_kws in defaults.items():
                    if k not in saved:
                        saved[k] = default_kws
                        modified = True
                    else:
                        for kw in default_kws:
                            if kw not in saved[k]:
                                saved[k].append(kw)
                                modified = True
                if modified:
                    self.set_setting("excel_keywords", json.dumps(saved))
                return saved
        except Exception as e:
            print(f"Error fetching excel_keywords: {e}")
            
        self.set_setting("excel_keywords", json.dumps(defaults))
        return defaults

    def save_excel_keywords(self, keywords):
        return self.set_setting("excel_keywords", json.dumps(keywords))


@lock_all_methods
class DependencyRepository:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_dependencies(self, sede=None):
        if sede and str(sede).strip().lower() != "todas":
            clean_s = str(sede).strip()
            self.db_manager.cursor.execute("""
                SELECT name FROM dependencies 
                WHERE LOWER(sede) = LOWER(?) 
                  AND UPPER(TRIM(name)) NOT IN ('GENERAL', 'SIN ASIGNAR', 'SIN DEPENDENCIAS', 'NONE', 'NULL', '')
                UNION
                SELECT DISTINCT UBICACION FROM assets 
                WHERE LOWER(SEDE) = LOWER(?) 
                  AND UBICACION IS NOT NULL AND UBICACION != '' 
                  AND UPPER(TRIM(UBICACION)) NOT IN ('GENERAL', 'SIN ASIGNAR', 'SIN DEPENDENCIAS', 'NONE', 'NULL', '')
                ORDER BY 1
            """, (clean_s, clean_s))
            return [r[0] for r in self.db_manager.cursor.fetchall()]
        else:
            self.db_manager.cursor.execute("""
                SELECT name FROM dependencies 
                WHERE UPPER(TRIM(name)) NOT IN ('GENERAL', 'SIN ASIGNAR', 'SIN DEPENDENCIAS', 'NONE', 'NULL', '')
                UNION
                SELECT DISTINCT UBICACION FROM assets 
                WHERE UBICACION IS NOT NULL AND UBICACION != '' 
                  AND UPPER(TRIM(UBICACION)) NOT IN ('GENERAL', 'SIN ASIGNAR', 'SIN DEPENDENCIAS', 'NONE', 'NULL', '')
                ORDER BY 1
            """)
            return [r[0] for r in self.db_manager.cursor.fetchall()]

    def add_dependency(self, name, type="AULA", sede="Guaimaral"):
        clean_name = str(name).strip().upper()
        if not clean_name or clean_name in ("GENERAL", "SIN ASIGNAR"):
            return False
        clean_sede = str(sede).strip() if sede and str(sede).strip().lower() != "todas" else "Guaimaral"
        try:
            self.db_manager.cursor.execute(
                "SELECT id FROM dependencies WHERE UPPER(name) = ? AND LOWER(sede) = LOWER(?)",
                (clean_name, clean_sede)
            )
            if self.db_manager.cursor.fetchone():
                return True
            self.db_manager.cursor.execute(
                "INSERT INTO dependencies (name, type, sede) VALUES (?, ?, ?)",
                (clean_name, type, clean_sede)
            )
            self.db_manager.conn.commit()
            return True
        except Exception as e:
            print(f"[DB] Error adding dependency {name}: {e}")
            self.db_manager.conn.rollback()
            return False

    def delete_dependency(self, name, sede=None):
        clean_name = str(name).strip()
        try:
            if sede and str(sede).strip().lower() != "todas":
                clean_sede = str(sede).strip()
                self.db_manager.cursor.execute(
                    "DELETE FROM dependencies WHERE UPPER(name) = UPPER(?) AND LOWER(sede) = LOWER(?)",
                    (clean_name, clean_sede)
                )
                self.db_manager.cursor.execute(
                    "UPDATE assets SET UBICACION = 'SIN ASIGNAR' WHERE UPPER(UBICACION) = UPPER(?) AND LOWER(SEDE) = LOWER(?)",
                    (clean_name, clean_sede)
                )
            else:
                self.db_manager.cursor.execute(
                    "DELETE FROM dependencies WHERE UPPER(name) = UPPER(?)",
                    (clean_name,)
                )
                self.db_manager.cursor.execute(
                    "UPDATE assets SET UBICACION = 'SIN ASIGNAR' WHERE UPPER(UBICACION) = UPPER(?)",
                    (clean_name,)
                )
            self.db_manager.conn.commit()
            return True
        except Exception as e:
            print(f"[DB] Error deleting dependency {name}: {e}")
            self.db_manager.conn.rollback()
            return False


@lock_all_methods
class AssetRepository:
    def __init__(self, db_manager, setting_repo, audit_repo):
        self.db_manager = db_manager
        self.setting_repo = setting_repo
        self.audit_repo = audit_repo
        self._stats_cache = None
        self._search_cache = {}
        self.sync_accounting_integrity()

    def invalidate_cache(self):
        self._stats_cache = None
        self._search_cache = {}

    def sync_accounting_integrity(self):
        """
        Lógica de depreciación forzada deshabilitada a petición del usuario
        para evitar que afecte a los nuevos activos registrados.
        """
        pass


    def _map_input_tuple(self, data):
        # Defaults
        d = {
            'CODIGO': 'NX-SYS', 'DESCRIPCION': '', 'VALOR': 0.0, 'FECHAADQUISICION': '',
            'MARCA': 'N/A', 'SERIAL': 'N/A', 'UBICACION': 'SIN ASIGNAR', 'CODCONTABLE': '101',
            'VIDAUTIL': 10, 'CODDEPRECIACION': '', 'DEPRECIACUMULADA': 0.0, 'CODGASTO': '',
            'FUNCIONARIO': '', 'IDENTIFICACION': '', 'CODGRUPO': '', 'CODSUBGRUPO': '',
            'TIPO': '', 'EXISTENCIAINICIAL': 1, 'SEDE': 'Guaimaral',
            'is_disposed': 0, 'disposal_date': None, 'disposal_reason': None,
            'conservation_state': 'Bueno'
        }
        
        if isinstance(data, dict):
            for k, v in data.items():
                if k in d:
                    d[k] = v
                elif k.upper() in d:
                    d[k.upper()] = v
        def parse_currency(val):
            if val is None: return 0.0
            if isinstance(val, (int, float)): return float(val)
            s = str(val).strip()
            if not s or s.lower() == 'nan': return 0.0
            
            import re
            if re.match(r'^-?\d+(\.\d+)?$', s):
                return float(s)
                
            s = s.replace('$', '').replace(' ', '')
            if ',' in s:
                s = s.replace('.', '').replace(',', '.')
            else:
                if s.count('.') > 1:
                    s = s.replace('.', '')
            try: return float(s)
            except: return 0.0

        if len(data) == 22:
            d['CODIGO'] = data[0]
            d['CODCONTABLE'] = data[1]
            d['DESCRIPCION'] = data[3]
            d['MARCA'] = data[4]
            d['SERIAL'] = data[6]
            d['VALOR'] = parse_currency(data[10])
            d['EXISTENCIAINICIAL'] = data[11]
            d['DEPRECIACUMULADA'] = data[13]
            d['FECHAADQUISICION'] = data[15]
            d['VIDAUTIL'] = data[17]
            d['UBICACION'] = data[21]
        elif len(data) == 30:
            d['CODIGO'] = data[0]
            d['CODCONTABLE'] = data[1]
            d['DESCRIPCION'] = data[3]
            d['MARCA'] = data[4]
            d['SERIAL'] = data[6]
            d['VALOR'] = parse_currency(data[10])
            d['EXISTENCIAINICIAL'] = data[11]
            d['DEPRECIACUMULADA'] = data[13]
            d['FECHAADQUISICION'] = data[15]
            d['VIDAUTIL'] = data[17]
            d['conservation_state'] = data[18]
            d['UBICACION'] = data[21]
            d['CODDEPRECIACION'] = data[22]
            d['CODGASTO'] = data[23]
            d['FUNCIONARIO'] = data[24]
            d['IDENTIFICACION'] = data[25]
            d['CODGRUPO'] = data[26]
            d['CODSUBGRUPO'] = data[27]
            d['TIPO'] = data[28]
            d['SEDE'] = data[29]
        elif len(data) >= 33:
            d['CODIGO'] = data[0]
            d['CODCONTABLE'] = data[1]
            d['DESCRIPCION'] = data[3]
            d['MARCA'] = data[4]
            d['SERIAL'] = data[6]
            d['VALOR'] = parse_currency(data[10])
            d['EXISTENCIAINICIAL'] = data[11]
            d['DEPRECIACUMULADA'] = data[13]
            d['FECHAADQUISICION'] = data[15]
            d['VIDAUTIL'] = data[17]
            d['conservation_state'] = data[18]
            d['UBICACION'] = data[21]
            d['is_disposed'] = data[22]
            d['disposal_date'] = data[23]
            d['disposal_reason'] = data[24]
            d['CODDEPRECIACION'] = data[25]
            d['CODGASTO'] = data[26]
            d['FUNCIONARIO'] = data[27]
            d['IDENTIFICACION'] = data[28]
            d['CODGRUPO'] = data[29]
            d['CODSUBGRUPO'] = data[30]
            d['TIPO'] = data[31]
            d['SEDE'] = data[32]

        # 1. Prioridad a la columna importada DEPRECIACUMULADA:
        from utils import parse_currency, calculate_depreciation
        try:
            d['VALOR'] = parse_currency(d.get('VALOR', 0))
            d['EXISTENCIAINICIAL'] = d.get('EXISTENCIAINICIAL') or 1
            
            raw_depr = d.get('DEPRECIACUMULADA')
            has_explicit = False
            raw_str = str(raw_depr).strip().lower()
            if raw_depr is not None and raw_str != "" and raw_str != "nan":
                explicit_depr = parse_currency(raw_depr)
                if explicit_depr > 0:
                    d['DEPRECIACUMULADA'] = explicit_depr
                    has_explicit = True

            if not has_explicit:
                # 2. Recálculo dinámico centralizado
                d['DEPRECIACUMULADA'] = calculate_depreciation(
                    valor=d['VALOR'],
                    existencia_inicial=d['EXISTENCIAINICIAL'],
                    descripcion=d.get('DESCRIPCION'),
                    ubicacion=d.get('UBICACION'),
                    fecha_adquisicion=d.get('FECHAADQUISICION'),
                    vida_util=d.get('VIDAUTIL')
                )
                
                # Ajustes específicos que quedaron en el motor viejo (Vida Útil para casos fijos)
                desc_upper = str(d.get('DESCRIPCION') or '').upper()
                ubi_upper = str(d.get('UBICACION') or '').upper()
                if 'AIRE' in desc_upper and ubi_upper in ('AULA 1', 'AULA 2', 'TRANSICION'):
                    d['VIDAUTIL'] = 10
                elif 'IMPRESORA 3D' in desc_upper and 'LABORATORIO' in ubi_upper:
                    d['VIDAUTIL'] = 5
        except Exception as e:
            print(f"Error mapping tuple: {e}")

        return (
            d['CODIGO'], d['DESCRIPCION'], d['VALOR'], d['FECHAADQUISICION'], d['MARCA'], d['SERIAL'], d['UBICACION'],
            d['CODCONTABLE'], d['VIDAUTIL'], d['CODDEPRECIACION'], d['DEPRECIACUMULADA'], d['CODGASTO'], d['FUNCIONARIO'],
            d['IDENTIFICACION'], d['CODGRUPO'], d['CODSUBGRUPO'], d['TIPO'], d['EXISTENCIAINICIAL'], d['SEDE'],
            d['is_disposed'], d['disposal_date'], d['disposal_reason'], d['conservation_state']
        )

    def instant_search(self, query, filter_field="Todo"):
        if not query or len(query) < 2: return []
        cache_key = f"{query}_{filter_field}"
        if cache_key in self._search_cache: return self._search_cache[cache_key]
        try:
            if filter_field == "Código":
                match_query = f"CODIGO:{query}*"
            elif filter_field == "Descripción":
                match_query = f"DESCRIPCION:{query}*"
            elif filter_field == "Funcionario":
                match_query = f"FUNCIONARIO:{query}*"
            else:
                match_query = f"{query}*"

            sql = """
                SELECT a.* FROM assets a
                JOIN assets_search s ON a.id = s.rowid
                WHERE assets_search MATCH ?
                AND a.is_disposed = 0
                ORDER BY rank
                LIMIT 100
            """
            self.db_manager.cursor.execute(sql, (match_query,))
            res = self.db_manager.cursor.fetchall()
        except Exception:
            col_map = {
                "Código": "CODIGO",
                "Descripción": "DESCRIPCION",
                "Funcionario": "FUNCIONARIO"
            }
            db_col = col_map.get(filter_field)
            if db_col:
                sql = f"SELECT * FROM assets WHERE is_disposed=0 AND {db_col} LIKE ? LIMIT 100"
                self.db_manager.cursor.execute(sql, (f"%{query}%",))
            else:
                sql = "SELECT * FROM assets WHERE is_disposed=0 AND (DESCRIPCION LIKE ? OR CODIGO LIKE ? OR FUNCIONARIO LIKE ?) LIMIT 100"
                self.db_manager.cursor.execute(sql, (f"%{query}%", f"%{query}%", f"%{query}%"))
            res = self.db_manager.cursor.fetchall()
        self._search_cache[cache_key] = res
        return res

    def add_asset(self, data):
        try:
            mapped = self._map_input_tuple(data)
            sql = """
                INSERT INTO assets (
                    CODIGO, DESCRIPCION, VALOR, FECHAADQUISICION, MARCA, SERIAL, UBICACION,
                    CODCONTABLE, VIDAUTIL, CODDEPRECIACION, DEPRECIACUMULADA, CODGASTO, FUNCIONARIO,
                    IDENTIFICACION, CODGRUPO, CODSUBGRUPO, TIPO, EXISTENCIAINICIAL, SEDE,
                    is_disposed, disposal_date, disposal_reason, conservation_state
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """
            self.db_manager.cursor.execute(sql, mapped)
            self.db_manager.conn.commit()
            self.invalidate_cache()
            return True
        except Exception as e:
            self.db_manager.conn.rollback()
            print(f"Error in add_asset: {e}")
            return False

    def bulk_add_assets(self, data_list):
        if not data_list: return False
        try:
            mapped_list = [self._map_input_tuple(row) for row in data_list]
            sql = """
                INSERT INTO assets (
                    CODIGO, DESCRIPCION, VALOR, FECHAADQUISICION, MARCA, SERIAL, UBICACION,
                    CODCONTABLE, VIDAUTIL, CODDEPRECIACION, DEPRECIACUMULADA, CODGASTO, FUNCIONARIO,
                    IDENTIFICACION, CODGRUPO, CODSUBGRUPO, TIPO, EXISTENCIAINICIAL, SEDE,
                    is_disposed, disposal_date, disposal_reason, conservation_state
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """
            self.db_manager.cursor.executemany(sql, mapped_list)
            self.db_manager.conn.commit()
            self.invalidate_cache()
            return True
        except Exception as e:
            self.db_manager.conn.rollback()
            print(f"Error in bulk_add_assets: {e}")
            return False

    def get_all_assets(self):
        self.db_manager.cursor.execute("SELECT * FROM assets")
        return self.db_manager.cursor.fetchall()

    def get_active_assets(self, limit=None, offset=None, sede=None):
        sql = "SELECT * FROM assets WHERE is_disposed=0"
        params = []
        if sede and sede != "Todas":
            sql += " AND LOWER(SEDE) = LOWER(?)"
            params.append(sede)
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            sql += " OFFSET ?"
            params.append(offset)
        self.db_manager.cursor.execute(sql, params)
        return self.db_manager.cursor.fetchall()

    def get_active_assets_count(self):
        self.db_manager.cursor.execute("SELECT COUNT(*) FROM assets WHERE is_disposed=0")
        row = self.db_manager.cursor.fetchone()
        return row['COUNT(*)'] if 'COUNT(*)' in row else row[0]

    def update_asset(self, asset_id, data):
        if not data:
            return False
        
        mapped_data = {}
        for k, v in data.items():
            db_col = UPDATE_MAP_KEYS.get(k)
            if db_col:
                mapped_data[db_col] = v
                
        if not mapped_data:
            return False
            
        # --- Auto-depreciation on edit ---
        try:
            self.db_manager.cursor.execute("SELECT * FROM assets WHERE id = ?", (asset_id,))
            current_asset = self.db_manager.cursor.fetchone()
            if current_asset:
                temp_dict = dict(current_asset)
                for k, v in mapped_data.items():
                    temp_dict[k] = v
                
                from utils import parse_currency, calculate_depreciation
                
                raw_depr = mapped_data.get('DEPRECIACUMULADA')
                raw_str = str(raw_depr).strip().lower() if raw_depr is not None else ""
                
                # Check if date or value changed
                date_changed = 'FECHAADQUISICION' in mapped_data and str(mapped_data['FECHAADQUISICION']) != str(temp_dict.get('FECHAADQUISICION'))
                val_changed = 'VALOR' in mapped_data and float(parse_currency(mapped_data['VALOR'])) != float(parse_currency(temp_dict.get('VALOR')))
                
                explicit_depr = parse_currency(raw_depr)
                
                # Force recalculate if date/value changed, OR if depreciation was explicitly cleared to 0
                needs_recalc = date_changed or val_changed or (explicit_depr == 0 and (raw_str == "0" or raw_str == "0.0" or raw_str == "0,00" or raw_str == "0.00" or raw_str == "" or raw_str == "nan"))
                
                if needs_recalc:
                    mapped_data['DEPRECIACUMULADA'] = calculate_depreciation(
                        valor=temp_dict.get('VALOR'),
                        existencia_inicial=temp_dict.get('EXISTENCIAINICIAL'),
                        descripcion=temp_dict.get('DESCRIPCION'),
                        ubicacion=temp_dict.get('UBICACION'),
                        fecha_adquisicion=temp_dict.get('FECHAADQUISICION'),
                        vida_util=temp_dict.get('VIDAUTIL')
                    )
                    
                    # Ajustes de vida útil para casos especiales
                    desc_upper = str(temp_dict.get('DESCRIPCION') or '').upper()
                    ubi_upper = str(temp_dict.get('UBICACION') or '').upper()
                    if 'AIRE' in desc_upper and ubi_upper in ('AULA 1', 'AULA 2', 'TRANSICION'):
                        mapped_data['VIDAUTIL'] = 10
                    elif 'IMPRESORA 3D' in desc_upper and 'LABORATORIO' in ubi_upper:
                        mapped_data['VIDAUTIL'] = 5
                else:
                    if explicit_depr > 0:
                        mapped_data['DEPRECIACUMULADA'] = explicit_depr
        except Exception as e:
            print("Error auto-calculando en update_asset:", e)
            
        set_clause = []
        params = []
        for key, val in mapped_data.items():
            set_clause.append(f"{key} = ?")
            params.append(val)
        
        params.append(asset_id)
        sql = f"UPDATE assets SET {', '.join(set_clause)} WHERE id = ?"
        
        try:
            self.db_manager.cursor.execute(sql, params)
            self.db_manager.conn.commit()
            self.invalidate_cache()
            return True
        except Exception as e:
            self.db_manager.conn.rollback()
            print(f"Error updating asset: {e}")
            return False

    def transfer_asset(self, asset_id, new_dependency):
        # Route through update_asset to ensure all smart depreciation rules 
        # (like Air Conditioners resetting in AULA 1) are re-evaluated perfectly.
        return self.update_asset(asset_id, {
            "UBICACION": new_dependency, 
            "DEPRECIACUMULADA": 0.0 # Force recalculation based on new location
        })

    def dispose_asset(self, asset_id, reason, date, qty_to_dispose=None):
        try:
            self.db_manager.cursor.execute("SELECT EXISTENCIAINICIAL, VALOR, DEPRECIACUMULADA, TIPO, CODIGO, CODCONTABLE, DESCRIPCION, MARCA, SERIAL, FECHAADQUISICION, VIDAUTIL, UBICACION, CODDEPRECIACION, CODGASTO, FUNCIONARIO, IDENTIFICACION, CODGRUPO, CODSUBGRUPO, SEDE FROM assets WHERE id=?", (asset_id,))
            row = self.db_manager.cursor.fetchone()
            if not row:
                return False

            current_qty = int(row['EXISTENCIAINICIAL'] or 1)

            if qty_to_dispose is None or qty_to_dispose >= current_qty:
                # BAJA TOTAL
                self.db_manager.cursor.execute(
                    "UPDATE assets SET is_disposed=1, disposal_reason=?, disposal_date=? WHERE id=?",
                    (reason, date, asset_id)
                )
            elif qty_to_dispose <= 0:
                return False
            else:
                # BAJA PARCIAL: insertar registro histórico con la cantidad dada de baja
                unit_val = float(row['VALOR'] or 0)
                orig_qty = float(current_qty)
                ratio = qty_to_dispose / orig_qty if orig_qty > 0 else 1
                depr_portion = float(row['DEPRECIACUMULADA'] or 0) * ratio

                sql = """
                    INSERT INTO assets (
                        CODIGO, DESCRIPCION, VALOR, FECHAADQUISICION, MARCA, SERIAL, UBICACION,
                        CODCONTABLE, VIDAUTIL, CODDEPRECIACION, DEPRECIACUMULADA, CODGASTO, FUNCIONARIO,
                        IDENTIFICACION, CODGRUPO, CODSUBGRUPO, TIPO, EXISTENCIAINICIAL, SEDE,
                        is_disposed, disposal_date, disposal_reason
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,?)
                """
                self.db_manager.cursor.execute(sql, (
                    row['CODIGO'], row['DESCRIPCION'], unit_val, row['FECHAADQUISICION'], row['MARCA'], row['SERIAL'],
                    row['UBICACION'], row['CODCONTABLE'], row['VIDAUTIL'], row['CODDEPRECIACION'], depr_portion,
                    row['CODGASTO'], row['FUNCIONARIO'], row['IDENTIFICACION'], row['CODGRUPO'], row['CODSUBGRUPO'],
                    row['TIPO'], qty_to_dispose, row['SEDE'], date, reason
                ))

                # Actualizar la cantidad restante en el activo original
                new_qty = current_qty - qty_to_dispose
                new_depr = float(row['DEPRECIACUMULADA'] or 0) - depr_portion
                
                self.db_manager.cursor.execute(
                    "UPDATE assets SET EXISTENCIAINICIAL=?, DEPRECIACUMULADA=? WHERE id=?",
                    (new_qty, new_depr, asset_id)
                )

            self.db_manager.conn.commit()
            self.invalidate_cache()
            return True
        except Exception as e:
            self.db_manager.conn.rollback()
            print(f"Error disposing asset: {e}")
            return False

    def clear_dependency_assets(self, dep_name):
        try:
            self.db_manager.cursor.execute("DELETE FROM assets WHERE UBICACION=?", (dep_name,))
            self.db_manager.conn.commit()
            self.invalidate_cache()
            return True
        except Exception as e:
            self.db_manager.conn.rollback()
            print(f"Error clearing dependency assets: {e}")
            return False

    def delete_asset(self, asset_id):
        try:
            self.db_manager.cursor.execute("DELETE FROM loans WHERE asset_id = ?", (asset_id,))
            self.db_manager.cursor.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
            self.db_manager.conn.commit()
            self.invalidate_cache()
            return True
        except Exception as e:
            self.db_manager.conn.rollback()
            print(f"Error deleting asset: {e}")
            return False

    def bulk_delete_assets(self, asset_ids):
        if not asset_ids:
            return False
        try:
            placeholders = ','.join('?' for _ in asset_ids)
            self.db_manager.cursor.execute(f"DELETE FROM loans WHERE asset_id IN ({placeholders})", tuple(asset_ids))
            self.db_manager.cursor.execute(f"DELETE FROM assets WHERE id IN ({placeholders})", tuple(asset_ids))
            self.db_manager.conn.commit()
            self.invalidate_cache()
            return True
        except Exception as e:
            self.db_manager.conn.rollback()
            print(f"Error in bulk_delete_assets: {e}")
            return False

    def get_assets_by_dependency(self, dep_name, limit=None, offset=None, sede=None):
        sql = "SELECT * FROM assets WHERE UBICACION=? AND is_disposed=0 AND CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) > 0"
        params = [dep_name]
        
        if sede and sede != "Todas":
            sql += " AND LOWER(SEDE) = LOWER(?)"
            params.append(sede)
            
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            sql += " OFFSET ?"
            params.append(offset)
        self.db_manager.cursor.execute(sql, params)
        return self.db_manager.cursor.fetchall()

    def get_disposed_assets_by_dependency(self, dep_name, sede=None):
        sql = "SELECT * FROM assets WHERE UBICACION=? AND is_disposed=1"
        params = [dep_name]
        if sede and sede != "Todas":
            sql += " AND LOWER(SEDE) = LOWER(?)"
            params.append(sede)
        self.db_manager.cursor.execute(sql, params)
        return self.db_manager.cursor.fetchall()

    def get_global_stats(self, sede=None):
        sql = """
            SELECT 
                SUM(CASE WHEN is_disposed=0 THEN (CASE WHEN CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) < 0 THEN 0 ELSE CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) END) ELSE 0 END) as units,
                SUM(CASE WHEN is_disposed=0 THEN CAST(COALESCE(VALOR, 0) AS REAL) * (CASE WHEN CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) < 0 THEN 0 ELSE CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) END) ELSE 0 END) as initial_val,
                SUM(CASE WHEN is_disposed=0 THEN (
                    CAST(COALESCE(VALOR, 0) AS REAL) * (CASE WHEN CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) < 0 THEN 0 ELSE CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) END) - CAST(COALESCE(DEPRECIACUMULADA, 0) AS REAL)
                ) ELSE 0 END) as real_val,
                SUM(CASE WHEN is_disposed=1 THEN (CASE WHEN CAST(COALESCE(EXISTENCIAINICIAL, 1) AS INTEGER) < 1 THEN 1 ELSE CAST(COALESCE(EXISTENCIAINICIAL, 1) AS INTEGER) END) ELSE 0 END) as bajas
            FROM assets
        """
        params = []
        if sede and sede != "Todas":
            sql += " WHERE LOWER(SEDE) = LOWER(?)"
            params.append(sede)

        self.db_manager.cursor.execute(sql, params)
        res = self.db_manager.cursor.fetchone()
        if res:
            self._stats_cache = (int(res['units'] or 0), float(res['initial_val'] or 0), float(res['real_val'] or 0), int(res['bajas'] or 0))
            return self._stats_cache
        return (0, 0.0, 0.0, 0)

    def get_depreciation_projection(self, sede=None):
        sql = """
            SELECT VALOR, EXISTENCIAINICIAL, DEPRECIACUMULADA, VIDAUTIL 
            FROM assets 
            WHERE is_disposed = 0
        """
        params = []
        if sede and sede != "Todas":
            sql += " AND LOWER(SEDE) = LOWER(?)"
            params.append(sede)

        self.db_manager.cursor.execute(sql, params)
        rows = self.db_manager.cursor.fetchall()
        
        current_val = 0.0
        for r in rows:
            val = float(r['VALOR'] or 0.0)
            qty = int(r['EXISTENCIAINICIAL'] or 1)
            depr = float(r['DEPRECIACUMULADA'] or 0.0)
            current_val += max(0.0, (val * qty) - depr)
            
        projection = [current_val]
        for year in range(1, 6):
            projected_val = 0.0
            for r in rows:
                val = float(r['VALOR'] or 0.0)
                qty = int(r['EXISTENCIAINICIAL'] or 1)
                depr = float(r['DEPRECIACUMULADA'] or 0.0)
                useful_life = int(r['VIDAUTIL'] or 10)
                val_tot = val * qty
                
                annual_depr = val_tot / max(1, useful_life)
                proj_depr = depr + (year * annual_depr)
                projected_val += max(0.0, val_tot - proj_depr)
            projection.append(projected_val)
        return projection

    def get_all_dep_stats(self, sede=None):
        sql = """
            SELECT 
                UPPER(UBICACION) as dep,
                COUNT(*) as rows,
                SUM(CASE WHEN CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) < 0 THEN 0 ELSE CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) END) as units,
                SUM(CAST(COALESCE(VALOR, 0) AS REAL) * (CASE WHEN CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) < 0 THEN 0 ELSE CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) END)) as initial_val,
                SUM(
                    CAST(COALESCE(VALOR, 0) AS REAL) * (CASE WHEN CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) < 0 THEN 0 ELSE CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) END) - CAST(COALESCE(DEPRECIACUMULADA, 0) AS REAL)
                ) as real_val
            FROM assets
            WHERE is_disposed=0 AND CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) > 0
        """
        params = []
        if sede and sede != "Todas":
            sql += " AND LOWER(SEDE) = LOWER(?)"
            params.append(sede)

        sql += " GROUP BY UPPER(UBICACION)"
        self.db_manager.cursor.execute(sql, params)
        rows = self.db_manager.cursor.fetchall()
        return {r['dep']: (int(r['rows']), int(r['units'] or 0), float(r['initial_val'] or 0), float(r['real_val'] or 0)) for r in rows}

    def get_dep_states_breakdown(self, sede=None):
        sql = """
            SELECT UPPER(UBICACION) as dep, conservation_state, SUM(EXISTENCIAINICIAL) as qty
            FROM assets
            WHERE is_disposed = 0 AND CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) > 0
        """
        params = []
        if sede and sede != "Todas":
            sql += " AND LOWER(SEDE) = LOWER(?)"
            params.append(sede)
            
        sql += " GROUP BY UPPER(UBICACION), conservation_state"
        self.db_manager.cursor.execute(sql, params)
        rows = self.db_manager.cursor.fetchall()
        
        breakdown = {}
        for r in rows:
            dep = r['dep']
            state = (r['conservation_state'] or 'Bueno').upper()
            qty = int(r['qty'] or 0)
            
            if dep not in breakdown:
                breakdown[dep] = {"BUENO": 0, "REGULAR": 0, "MALO": 0}
                
            if "EXCELENTE" in state or "BUENO" in state:
                breakdown[dep]["BUENO"] += qty
            elif "REGULAR" in state:
                breakdown[dep]["REGULAR"] += qty
            elif "MALO" in state:
                breakdown[dep]["MALO"] += qty
        return breakdown

    def get_dep_stats(self, dep_name):
        self.db_manager.cursor.execute("""
            SELECT 
                COUNT(*) as rows,
                SUM(CASE WHEN CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) < 0 THEN 0 ELSE CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) END) as units,
                SUM(CAST(COALESCE(VALOR, 0) AS REAL) * (CASE WHEN CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) < 0 THEN 0 ELSE CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) END)) as initial_val,
                SUM(
                    CAST(COALESCE(VALOR, 0) AS REAL) * (CASE WHEN CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) < 0 THEN 0 ELSE CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) END) - CAST(COALESCE(DEPRECIACUMULADA, 0) AS REAL)
                ) as real_val
            FROM assets
            WHERE TRIM(UBICACION) = TRIM(?) COLLATE NOCASE AND is_disposed=0 AND CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) > 0
        """, (dep_name,))
        res = self.db_manager.cursor.fetchone()
        if res and res['rows'] > 0:
            return int(res['rows']), int(res['units'] or 0), float(res['initial_val'] or 0), float(res['real_val'] or 0)
        return 0, 0, 0.0, 0.0

    def get_dep_disposal_stats(self, dep_name, sede=None):
        sql = """
            SELECT 
                COALESCE(SUM(CASE WHEN CAST(EXISTENCIAINICIAL AS INTEGER) < 1 THEN 1 ELSE CAST(EXISTENCIAINICIAL AS INTEGER) END), 0) as cnt,
                COALESCE(SUM(
                    CAST(COALESCE(VALOR, 0) AS REAL) * CAST(COALESCE(EXISTENCIAINICIAL, 1) AS INTEGER) - CAST(COALESCE(DEPRECIACUMULADA, 0) AS REAL)
                ), 0) as total
            FROM assets WHERE UPPER(UBICACION)=UPPER(?) AND is_disposed=1
        """
        params = [dep_name]
        if sede and sede != "Todas":
            sql += " AND LOWER(SEDE) = LOWER(?)"
            params.append(sede)
            
        self.db_manager.cursor.execute(sql, params)
        res = self.db_manager.cursor.fetchone()
        if res:
            return int(res['cnt'] or 0), float(res['total'] or 0)
        return (0, 0.0)

    def get_asset_summary_stats(self, dep_name, sede=None):
        sql_cat = """
            SELECT 
                'GENERAL' as rubro,
                SUM(CASE WHEN CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) < 0 THEN 0 ELSE CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) END) as qty,
                SUM(CAST(COALESCE(VALOR, 0) AS REAL) * (CASE WHEN CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) < 0 THEN 0 ELSE CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) END)) as val_tot,
                SUM(CAST(COALESCE(DEPRECIACUMULADA, 0) AS REAL)) as depr,
                SUM(CAST(COALESCE(VALOR, 0) AS REAL) * (CASE WHEN CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) < 0 THEN 0 ELSE CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) END) - CAST(COALESCE(DEPRECIACUMULADA, 0) AS REAL)) as val_cur
            FROM assets
            WHERE TRIM(UBICACION) = TRIM(?) COLLATE NOCASE AND is_disposed=0 AND CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) > 0
        """
        params_cat = [dep_name]
        if sede and sede != "Todas":
            sql_cat += " AND LOWER(SEDE) = LOWER(?)"
            params_cat.append(sede)
        sql_cat += " GROUP BY rubro"
        
        self.db_manager.cursor.execute(sql_cat, params_cat)
        cat_rows = self.db_manager.cursor.fetchall()
        categories = {r['rubro']: {
            'qty': int(r['qty'] or 0), 
            'val_tot': float(r['val_tot'] or 0), 
            'depr': float(r['depr'] or 0), 
            'val_cur': float(r['val_cur'] or 0)
        } for r in cat_rows}

        sql_items = """
            SELECT 
                UPPER(TRIM(DESCRIPCION)) as desc,
                UPPER(TRIM(COALESCE(MARCA, 'N/A'))) as brand,
                'N/A' as model,
                'Bueno' as state,
                SUM(CASE WHEN CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) < 0 THEN 0 ELSE CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) END) as qty,
                AVG(CAST(COALESCE(VALOR, 0) AS REAL)) as val_uni,
                SUM(CAST(COALESCE(VALOR, 0) AS REAL) * (CASE WHEN CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) < 0 THEN 0 ELSE CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) END)) as val_tot,
                SUM(CAST(COALESCE(DEPRECIACUMULADA, 0) AS REAL)) as depr,
                SUM(CAST(COALESCE(VALOR, 0) AS REAL) * (CASE WHEN CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) < 0 THEN 0 ELSE CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) END) - CAST(COALESCE(DEPRECIACUMULADA, 0) AS REAL)) as val_cur,
                GROUP_CONCAT(CODIGO) as codes
            FROM assets
            WHERE TRIM(UBICACION) = TRIM(?) COLLATE NOCASE AND is_disposed=0 AND CAST(COALESCE(EXISTENCIAINICIAL, 0) AS INTEGER) > 0
        """
        params_items = [dep_name]
        if sede and sede != "Todas":
            sql_items += " AND LOWER(SEDE) = LOWER(?)"
            params_items.append(sede)
        sql_items += " GROUP BY 1, 2"

        self.db_manager.cursor.execute(sql_items, params_items)
        item_rows = self.db_manager.cursor.fetchall()
        items = []
        for r in item_rows:
            items.append({
                'desc': r['desc'], 'brand': r['brand'], 'model': r['model'], 'state': r['state'],
                'qty': int(r['qty'] or 0), 'val_uni': float(r['val_uni'] or 0),
                'val_tot': float(r['val_tot'] or 0), 'depr': float(r['depr'] or 0),
                'val_cur': float(r['val_cur'] or 0), 'codes': (r['codes'] or "").split(',')
            })
        return {'categories': categories, 'items': items}

    def get_disposal_count(self):
        self.db_manager.cursor.execute("""
            SELECT COALESCE(SUM(CASE WHEN CAST(EXISTENCIAINICIAL AS INTEGER) < 1 THEN 1 ELSE CAST(EXISTENCIAINICIAL AS INTEGER) END), 0) as cnt
            FROM assets WHERE is_disposed=1
        """)
        return int(self.db_manager.cursor.fetchone()['cnt'])

    def get_active_alerts(self, sede=None):
        alerts = []
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        loans_sql = """
            SELECT COUNT(*) as cnt, SUM(l.quantity) as total_qty
            FROM loans l
            JOIN assets a ON l.asset_id = a.id
            WHERE l.status='ACTIVE' AND l.expected_return_date < ?
        """
        params = [today_str]
        if sede and sede != "Todas":
            loans_sql += " AND LOWER(a.SEDE) = LOWER(?)"
            params.append(sede)
            
        self.db_manager.cursor.execute(loans_sql, params)
        res_loans = self.db_manager.cursor.fetchone()
        overdue_cnt = int(res_loans['cnt'] or 0) if res_loans else 0
        if overdue_cnt > 0:
            alerts.append({
                'type': 'critical',
                'count': overdue_cnt,
                'title': 'Préstamos Vencidos',
                'description': f'{overdue_cnt} maestro(s) no han devuelto activos a tiempo.',
                'color': '#ef4444',
                'icon': '🧑‍🏫'
            })
        
        depr_sql = """
            SELECT SUM(CASE WHEN CAST(EXISTENCIAINICIAL AS INTEGER) < 1 THEN 1 ELSE CAST(EXISTENCIAINICIAL AS INTEGER) END) as cnt
            FROM assets 
            WHERE is_disposed=0 
            AND CAST(COALESCE(VALOR, 0) AS REAL) > 0 
            AND (
                MAX(0, CAST(COALESCE(VALOR, 0) AS REAL) * CAST(COALESCE(EXISTENCIAINICIAL, 1) AS INTEGER) - CAST(COALESCE(DEPRECIACUMULADA, 0) AS REAL))
            ) <= 0
        """
        depr_params = []
        if sede and sede != "Todas":
            depr_sql += " AND LOWER(SEDE) = LOWER(?)"
            depr_params.append(sede)
            
        self.db_manager.cursor.execute(depr_sql, depr_params)
        res_depr = self.db_manager.cursor.fetchone()
        depr_count = int(res_depr['cnt'] or 0) if res_depr else 0
        if depr_count > 0:
            alerts.append({
                'type': 'warning',
                'count': depr_count,
                'title': 'Depreciación Completada',
                'description': f'{depr_count} activo(s) amortizados financieramente.',
                'color': '#f59e0b',
                'icon': '💸'
            })

        if not alerts:
            alerts.append({
                'type': 'success',
                'count': 0,
                'title': 'Condiciones Óptimas',
                'description': 'Inventario en parámetros estables.',
                'color': '#10b981',
                'icon': '✅'
            })
        return alerts

    def get_filtered_assets(self, limit=None, offset=None, dependency=None, state=None, min_val=None, max_val=None, sede=None):
        where_clauses = ["a.is_disposed=0", "CAST(COALESCE(a.EXISTENCIAINICIAL, 0) AS INTEGER) > 0"]
        params = []
        if dependency and dependency != "Todas":
            where_clauses.append("a.UBICACION = ?")
            params.append(dependency)
        if state and state != "Todos":
            where_clauses.append("a.conservation_state = ?")
            params.append(state)
        if min_val is not None:
            where_clauses.append("a.VALOR >= ?")
            params.append(min_val)
        if max_val is not None:
            where_clauses.append("a.VALOR <= ?")
            params.append(max_val)
        if sede and sede != "Todas":
            where_clauses.append("LOWER(a.SEDE) = LOWER(?)")
            params.append(sede)

        where_sql = " AND ".join(where_clauses)
        base_params = list(params)

        sql = f"""
            SELECT a.*, 
                   (SELECT 1 FROM loans l WHERE l.asset_id = a.id AND l.status = 'ACTIVE' LIMIT 1) as is_loaned 
            FROM assets a 
            WHERE {where_sql} 
            ORDER BY a.id DESC
        """
        sql_count = f"SELECT COUNT(*) FROM assets a WHERE {where_sql}"
        sql_sums = f"""
            SELECT 
                COALESCE(SUM(CAST(COALESCE(a.VALOR, 0) AS REAL) * CAST(COALESCE(a.EXISTENCIAINICIAL, 1) AS INTEGER)), 0),
                COALESCE(SUM(CAST(COALESCE(a.DEPRECIACUMULADA, 0) AS REAL)), 0)
            FROM assets a 
            WHERE {where_sql}
        """

        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            sql += " OFFSET ?"
            params.append(offset)

        self.db_manager.cursor.execute(sql, params)
        assets = self.db_manager.cursor.fetchall()

        self.db_manager.cursor.execute(sql_count, base_params)
        row = self.db_manager.cursor.fetchone()
        total = row['COUNT(*)'] if 'COUNT(*)' in row else row[0]

        self.db_manager.cursor.execute(sql_sums, base_params)
        sum_row = self.db_manager.cursor.fetchone()
        sum_initial = sum_row[0] if sum_row and sum_row[0] else 0.0
        sum_depr = sum_row[1] if sum_row and sum_row[1] else 0.0

        return assets, total, float(sum_initial), float(sum_depr)

    def get_all_sedes(self):
        try:
            self.db_manager.cursor.execute("SELECT DISTINCT SEDE FROM assets WHERE SEDE IS NOT NULL AND SEDE != ''")
            sedes = [r[0] if isinstance(r, (list, tuple)) else r.get('SEDE') for r in self.db_manager.cursor.fetchall()]
        except Exception:
            sedes = []
        clean_sedes = ["Guaimaral", "Cuatro Bocas"]
        lower_clean = [s.lower() for s in clean_sedes]
        for s in sedes:
            if s:
                s_str = str(s).strip().title()
                if s_str and s_str.lower() not in lower_clean:
                    clean_sedes.append(s_str)
                    lower_clean.append(s_str.lower())
        return sorted(clean_sedes)

    def get_asset_by_code(self, code):
        try:
            self.db_manager.cursor.execute("SELECT * FROM assets WHERE CODIGO=? AND is_disposed=0 LIMIT 1", (code,))
            return self.db_manager.cursor.fetchone()
        except Exception as e:
            print(f"Error querying asset by code: {e}")
            return None

    def get_asset_by_id(self, asset_id):
        try:
            self.db_manager.cursor.execute("SELECT * FROM assets WHERE id=? LIMIT 1", (asset_id,))
            return self.db_manager.cursor.fetchone()
        except Exception as e:
            print(f"Error querying asset by id: {e}")
            return None

    def generate_next_code(self, sede="Guaimaral"):
        import re
        s = str(sede).strip().lower() if sede else "guaimaral"
        if "cuatro" in s or "boca" in s:
            prefix = "NX-CB-"
        elif "guaim" in s:
            prefix = "NX-GUA-"
        else:
            clean = re.sub(r'[^A-Z0-9]', '', str(sede).strip().upper())[:4] or "GEN"
            prefix = f"NX-{clean}-"

        try:
            self.db_manager.cursor.execute("SELECT CODIGO FROM assets WHERE CODIGO LIKE ?", (f"{prefix}%",))
            rows = self.db_manager.cursor.fetchall()
            max_num = 0
            for r in rows:
                code_str = r[0] if isinstance(r, (list, tuple)) else r.get('CODIGO', '')
                if code_str:
                    match = re.search(r'(\d+)', code_str.replace(prefix, ''))
                    if match:
                        try:
                            num = int(match.group(1))
                            if num > max_num:
                                max_num = num
                        except ValueError:
                            pass
            return f"{prefix}{max_num + 1:04d}"
        except Exception as e:
            print(f"[DB] Error generating code for {sede}: {e}")
            return f"{prefix}0001"

    def get_dashboard_data(self, sede=None):
        stats = self.get_global_stats(sede)
        projection = self.get_depreciation_projection(sede)
        dep_stats = self.get_all_dep_stats(sede)
        alerts = self.get_active_alerts(sede)
        return stats, projection, dep_stats, alerts


@lock_all_methods
class LoanRepository:
    def __init__(self, db_manager, asset_repo=None):
        self.db_manager = db_manager
        self.asset_repo = asset_repo

    def get_asset_available_quantity(self, asset_id):
        self.db_manager.cursor.execute("SELECT EXISTENCIAINICIAL FROM assets WHERE id = ?", (asset_id,))
        row = self.db_manager.cursor.fetchone()
        if not row:
            return 0
        return max(0, int(row['EXISTENCIAINICIAL'] or 0))

    def _invalidate_assets(self):
        if self.asset_repo and hasattr(self.asset_repo, 'invalidate_cache'):
            self.asset_repo.invalidate_cache()

    def create_loan(self, asset_id, qty, teacher_name, start_date, expected_return, teacher_phone=""):
        try:
            self.db_manager.cursor.execute("""
                INSERT INTO loans (asset_id, quantity, teacher_name, teacher_phone, start_date, expected_return_date, status)
                VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE')
            """, (asset_id, qty, teacher_name, teacher_phone or "", start_date, expected_return))
            
            # Descontar del inventario y actualizar responsable
            self.db_manager.cursor.execute("UPDATE assets SET FUNCIONARIO=?, EXISTENCIAINICIAL = EXISTENCIAINICIAL - ? WHERE id=?", (teacher_name, qty, asset_id))
            self.db_manager.conn.commit()
            self._invalidate_assets()
            return True
        except Exception as e:
            self.db_manager.conn.rollback()
            print(f"Error creating loan: {e}")
            return False

    def update_loan(self, loan_id, teacher_name, teacher_phone, expected_return, qty):
        try:
            self.db_manager.cursor.execute("SELECT asset_id, quantity, status FROM loans WHERE id=?", (loan_id,))
            res = self.db_manager.cursor.fetchone()
            if res and res['status'] == 'ACTIVE':
                old_qty = int(res['quantity']) if res['quantity'] is not None else 1
                new_qty = int(qty) if qty is not None else 1
                diff = new_qty - old_qty
                if diff != 0:
                    self.db_manager.cursor.execute("UPDATE assets SET EXISTENCIAINICIAL = EXISTENCIAINICIAL - ? WHERE id=?", (diff, res['asset_id']))
            self.db_manager.cursor.execute("""
                UPDATE loans 
                SET teacher_name = ?, teacher_phone = ?, expected_return_date = ?, quantity = ?
                WHERE id = ?
            """, (teacher_name, teacher_phone or "", expected_return, qty, loan_id))
            self.db_manager.conn.commit()
            self._invalidate_assets()
            return True
        except Exception as e:
            self.db_manager.conn.rollback()
            print(f"Error updating loan: {e}")
            return False

    def delete_loan(self, loan_id):
        try:
            self.db_manager.cursor.execute("SELECT asset_id, quantity, status FROM loans WHERE id=?", (loan_id,))
            res = self.db_manager.cursor.fetchone()
            if res and res['status'] == 'ACTIVE':
                restore_qty = int(res['quantity']) if res['quantity'] is not None else 1
                self.db_manager.cursor.execute("UPDATE assets SET EXISTENCIAINICIAL = EXISTENCIAINICIAL + ? WHERE id=?", (restore_qty, res['asset_id']))
            self.db_manager.cursor.execute("DELETE FROM loans WHERE id=?", (loan_id,))
            self.db_manager.conn.commit()
            self._invalidate_assets()
            return True
        except Exception as e:
            self.db_manager.conn.rollback()
            print(f"Error deleting loan: {e}")
            return False

    def return_loan(self, loan_id):
        try:
            self.db_manager.cursor.execute("SELECT asset_id, quantity, status FROM loans WHERE id=?", (loan_id,))
            res = self.db_manager.cursor.fetchone()
            if res and res['status'] == 'ACTIVE':
                restore_qty = int(res['quantity']) if res['quantity'] is not None else 1
                self.db_manager.cursor.execute("UPDATE assets SET FUNCIONARIO='RECTOR', EXISTENCIAINICIAL = EXISTENCIAINICIAL + ? WHERE id=?", (restore_qty, res['asset_id']))
                self.db_manager.cursor.execute("UPDATE loans SET status='RETURNED' WHERE id=?", (loan_id,))
                self.db_manager.conn.commit()
                self._invalidate_assets()
                return True
            elif res and res['status'] == 'RETURNED':
                return True
            return False
        except Exception as e:
            self.db_manager.conn.rollback()
            print(f"Error returning loan: {e}")
            return False

    def get_active_loans(self, sede=None):
        sql = """
            SELECT l.id, l.asset_id, l.quantity as loan_qty, l.teacher_name, l.teacher_phone, l.start_date, 
                   l.expected_return_date, a.DESCRIPCION as description, a.CODIGO as code, a.UBICACION as dependency, a.MARCA as brand
            FROM loans l 
            JOIN assets a ON l.asset_id = a.id
            WHERE l.status='ACTIVE'
        """
        params = []
        if sede and sede != "Todas":
            sql += " AND LOWER(a.SEDE) = LOWER(?)"
            params.append(sede)
        sql += " ORDER BY l.expected_return_date ASC"
        
        self.db_manager.cursor.execute(sql, params)
        return self.db_manager.cursor.fetchall()

    def get_returned_loans(self, sede=None):
        sql = """
            SELECT l.id, l.asset_id, l.quantity as loan_qty, l.teacher_name, l.teacher_phone, l.start_date, 
                   l.expected_return_date, a.DESCRIPCION as description, a.CODIGO as code, a.UBICACION as dependency, a.MARCA as brand
            FROM loans l 
            JOIN assets a ON l.asset_id = a.id
            WHERE l.status='RETURNED'
        """
        params = []
        if sede and sede != "Todas":
            sql += " AND LOWER(a.SEDE) = LOWER(?)"
            params.append(sede)
        sql += " ORDER BY l.id DESC"
        
        self.db_manager.cursor.execute(sql, params)
        return self.db_manager.cursor.fetchall()


@lock_all_methods
class OfficialRepository:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def add_official(self, data):
        try:
            sql = """INSERT INTO officials (code, name, identification, address, phone, birth_place, birth_date, gender, civil_status, dependency, position, hire_date)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            self.db_manager.cursor.execute(sql, data)
            self.db_manager.conn.commit()
            return True
        except Exception as e:
            self.db_manager.conn.rollback()
            print(f"Error in add_official: {e}")
            return False

    def get_officials(self):
        self.db_manager.cursor.execute("SELECT * FROM officials")
        return self.db_manager.cursor.fetchall()

    def get_all_responsible_names(self):
        try:
            self.db_manager.cursor.execute("SELECT DISTINCT FUNCIONARIO FROM assets WHERE FUNCIONARIO IS NOT NULL AND FUNCIONARIO != ''")
            asset_funcs = [r[0] if isinstance(r, (list, tuple)) else r.get('FUNCIONARIO') for r in self.db_manager.cursor.fetchall()]
        except Exception:
            asset_funcs = []
        try:
            self.db_manager.cursor.execute("SELECT DISTINCT name FROM officials WHERE name IS NOT NULL AND name != ''")
            official_funcs = [r[0] if isinstance(r, (list, tuple)) else r.get('name') for r in self.db_manager.cursor.fetchall()]
        except Exception:
            official_funcs = []
            
        clean_funcs = []
        for name in (asset_funcs + official_funcs):
            if name:
                name_str = str(name).strip()
                if name_str and name_str not in clean_funcs:
                    clean_funcs.append(name_str)
        return sorted(clean_funcs)


# COMPATIBILITY FACADE: Exposes the exact same interface as the old Database class
# so that existing scripts and the test suite keep working without modification.
class Database:
    def __init__(self, db_name="inventory.db"):
        self.manager = DatabaseManager(db_name)
        self.conn = self.manager.conn
        self.cursor = self.manager.cursor
        self.lock = self.manager.lock
        
        # Instantiate repositories
        self.audit_repo = AuditRepository(self.manager)
        self.setting_repo = SettingRepository(self.manager)
        self.dep_repo = DependencyRepository(self.manager)
        self.asset_repo = AssetRepository(self.manager, self.setting_repo, self.audit_repo)
        self.loan_repo = LoanRepository(self.manager, self.asset_repo)
        self.official_repo = OfficialRepository(self.manager)

    # Delegate all legacy method names
    def invalidate_cache(self):
        self.asset_repo.invalidate_cache()

    def instant_search(self, *args, **kwargs):
        return self.asset_repo.instant_search(*args, **kwargs)

    def log_event(self, *args, **kwargs):
        return self.audit_repo.log_event(*args, **kwargs)

    def add_asset(self, *args, **kwargs):
        return self.asset_repo.add_asset(*args, **kwargs)

    def bulk_add_assets(self, *args, **kwargs):
        return self.asset_repo.bulk_add_assets(*args, **kwargs)

    def add_official(self, *args, **kwargs):
        return self.official_repo.add_official(*args, **kwargs)

    def get_all_assets(self, *args, **kwargs):
        return self.asset_repo.get_all_assets(*args, **kwargs)

    def get_active_assets(self, *args, **kwargs):
        return self.asset_repo.get_active_assets(*args, **kwargs)

    def get_active_assets_count(self, *args, **kwargs):
        return self.asset_repo.get_active_assets_count(*args, **kwargs)

    def get_officials(self, *args, **kwargs):
        return self.official_repo.get_officials(*args, **kwargs)

    def get_all_responsible_names(self, *args, **kwargs):
        return self.official_repo.get_all_responsible_names(*args, **kwargs)

    def get_excel_keywords(self, *args, **kwargs):
        return self.setting_repo.get_excel_keywords(*args, **kwargs)

    def save_excel_keywords(self, *args, **kwargs):
        return self.setting_repo.save_excel_keywords(*args, **kwargs)

    def get_dependencies(self, *args, **kwargs):
        return self.dep_repo.get_dependencies(*args, **kwargs)

    def add_dependency(self, *args, **kwargs):
        return self.dep_repo.add_dependency(*args, **kwargs)

    def delete_dependency(self, *args, **kwargs):
        return self.dep_repo.delete_dependency(*args, **kwargs)

    def update_asset(self, *args, **kwargs):
        return self.asset_repo.update_asset(*args, **kwargs)

    def transfer_asset(self, *args, **kwargs):
        return self.asset_repo.transfer_asset(*args, **kwargs)

    def dispose_asset(self, *args, **kwargs):
        return self.asset_repo.dispose_asset(*args, **kwargs)

    def clear_dependency_assets(self, *args, **kwargs):
        return self.asset_repo.clear_dependency_assets(*args, **kwargs)

    def delete_asset(self, *args, **kwargs):
        return self.asset_repo.delete_asset(*args, **kwargs)

    def bulk_delete_assets(self, *args, **kwargs):
        return self.asset_repo.bulk_delete_assets(*args, **kwargs)

    def get_assets_by_dependency(self, *args, **kwargs):
        return self.asset_repo.get_assets_by_dependency(*args, **kwargs)

    def get_disposed_assets_by_dependency(self, *args, **kwargs):
        return self.asset_repo.get_disposed_assets_by_dependency(*args, **kwargs)

    def get_asset_available_quantity(self, *args, **kwargs):
        return self.loan_repo.get_asset_available_quantity(*args, **kwargs)

    def create_loan(self, *args, **kwargs):
        return self.loan_repo.create_loan(*args, **kwargs)

    def return_loan(self, *args, **kwargs):
        return self.loan_repo.return_loan(*args, **kwargs)

    def get_active_loans(self, *args, **kwargs):
        return self.loan_repo.get_active_loans(*args, **kwargs)

    def get_returned_loans(self, *args, **kwargs):
        return self.loan_repo.get_returned_loans(*args, **kwargs)

    def get_global_stats(self, *args, **kwargs):
        return self.asset_repo.get_global_stats(*args, **kwargs)

    def get_depreciation_projection(self, *args, **kwargs):
        return self.asset_repo.get_depreciation_projection(*args, **kwargs)

    def get_all_dep_stats(self, *args, **kwargs):
        return self.asset_repo.get_all_dep_stats(*args, **kwargs)

    def get_dep_states_breakdown(self, *args, **kwargs):
        return self.asset_repo.get_dep_states_breakdown(*args, **kwargs)

    def get_dep_stats(self, *args, **kwargs):
        return self.asset_repo.get_dep_stats(*args, **kwargs)

    def get_dep_disposal_stats(self, *args, **kwargs):
        return self.asset_repo.get_dep_disposal_stats(*args, **kwargs)

    def get_asset_summary_stats(self, *args, **kwargs):
        return self.asset_repo.get_asset_summary_stats(*args, **kwargs)

    def get_disposal_count(self, *args, **kwargs):
        return self.asset_repo.get_disposal_count(*args, **kwargs)

    def get_active_alerts(self, *args, **kwargs):
        return self.asset_repo.get_active_alerts(*args, **kwargs)

    def get_filtered_assets(self, *args, **kwargs):
        return self.asset_repo.get_filtered_assets(*args, **kwargs)

    def get_all_sedes(self, *args, **kwargs):
        return self.asset_repo.get_all_sedes(*args, **kwargs)

    def get_asset_by_code(self, *args, **kwargs):
        return self.asset_repo.get_asset_by_code(*args, **kwargs)

    def get_asset_by_id(self, *args, **kwargs):
        return self.asset_repo.get_asset_by_id(*args, **kwargs)

    def generate_next_code(self, *args, **kwargs):
        return self.asset_repo.generate_next_code(*args, **kwargs)

    def get_audit_logs(self, *args, **kwargs):
        return self.audit_repo.get_audit_logs(*args, **kwargs)

    def get_dashboard_data(self, *args, **kwargs):
        return self.asset_repo.get_dashboard_data(*args, **kwargs)

# Unified global database instance
db = Database()
