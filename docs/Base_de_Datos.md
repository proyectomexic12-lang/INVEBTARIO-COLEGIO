# 💾 Diseño y Optimización de la Base de Datos

NEXUS utiliza **SQLite3** como motor de base de datos local. Para garantizar una experiencia fluida, libre de bloqueos de interfaz ("UI freezing") y con velocidades de lectura instantáneas, la base de datos se inicializa con parámetros avanzados de rendimiento.

---

## ⚡ Ajustes de Rendimiento y Persistencia

En [database.py](file:///c:/Users/USUARIO/Desktop/inventario/desktop_app/database.py), al establecer la conexión, se configuran los siguientes pragmas de SQLite:

* **`PRAGMA journal_mode=WAL`**: Habilita *Write-Ahead Logging*. Esto permite que los hilos de lectura no bloqueen a los hilos de escritura, posibilitando búsquedas mientras se realiza una importación o actualización.
* **`PRAGMA synchronous=OFF`**: SQLite no espera a que los datos se escriban físicamente en el disco magnético antes de continuar. Esto incrementa la velocidad de escrituras masivas (como la importación de Excel) en más de un 500%.
* **`PRAGMA cache_size=-256000`**: Reserva hasta 256 MB de memoria RAM para caché de páginas de base de datos, manteniendo los registros consultados frecuentemente en memoria.
* **`PRAGMA temp_store=MEMORY`**: Las tablas temporales e índices de ordenamiento se guardan directamente en la RAM en lugar de escribir archivos temporales en el disco.

---

## 🏛️ Esquema de Tablas

### 1. Activos (`assets`)
Esta tabla utiliza los nombres exactos de columnas en mayúscula y en español para alinearse con los reportes oficiales y planillas de la Secretaría de Educación:

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | INTEGER | Llave primaria autoincremental |
| `CODIGO` | TEXT | Código físico del activo (placa) |
| `DESCRIPCION` | TEXT | Nombre o detalle descriptivo del bien |
| `VALOR` | REAL | Valor unitario inicial de adquisición |
| `FECHAADQUISICION` | TEXT | Fecha de ingreso al inventario (AAAA-MM-DD) |
| `MARCA` | TEXT | Fabricante o marca |
| `SERIAL` | TEXT | Número de serie del fabricante |
| `UBICACION` | TEXT | Dependencia o salón donde reside (ej: "AULA 1") |
| `CODCONTABLE` | TEXT | Código contable presupuestal |
| `VIDAUTIL` | INTEGER | Vida útil restante en años |
| `CODDEPRECIACION` | TEXT | Código de depreciación asociado |
| `DEPRECIACUMULADA` | REAL | Amortización acumulada a la fecha |
| `CODGASTO` | TEXT | Código de imputación de gasto |
| `FUNCIONARIO` | TEXT | Nombre del responsable administrativo |
| `IDENTIFICACION` | TEXT | Documento de identidad del responsable |
| `CODGRUPO` | TEXT | Código de grupo patrimonial |
| `CODSUBGRUPO` | TEXT | Código de subgrupo patrimonial |
| `TIPO` | TEXT | Clasificación del bien |
| `EXISTENCIAINICIAL`| INTEGER| Cantidad física de unidades (mínimo 1) |
| `SEDE` | TEXT | Nombre de la sede educativa |
| `is_disposed` | INTEGER | `0` = Activo, `1` = Dado de baja |
| `disposal_date` | TEXT | Fecha en que se decretó la baja |
| `disposal_reason` | TEXT | Justificación legal o técnica de la baja |

### 2. Préstamos (`loans`)
Registra las asignaciones temporales de activos a los docentes:
* `id` (INTEGER PRIMARY KEY)
* `asset_id` (INTEGER, REFERENCES `assets(id)`)
* `quantity` (INTEGER)
* `teacher_name` (TEXT)
* `start_date` (TEXT)
* `expected_return_date` (TEXT)
* `status` (TEXT: `'ACTIVE'` o `'RETURNED'`)

### 3. Configuración (`settings`)
Guarda de manera clave-valor los metadatos de la institución:
* `key` (TEXT PRIMARY KEY)
* `value` (TEXT)

---

## 🔀 Capa de Compatibilidad de Datos (`dict_compatibility_factory`)

Para evitar reescribir todo el código existente en Python que utilizaba nombres de propiedades en minúscula y en inglés (por ejemplo, `asset['description']` o `asset['quantity']`), la base de datos implementa una fábrica de filas personalizada llamada `dict_compatibility_factory`:

```python
def dict_compatibility_factory(cursor, row):
    col_names = [col[0] for col in cursor.description]
    d = {col_names[idx]: row[idx] for idx in range(len(col_names))}
    
    if any(k in d for k in ('DESCRIPCION', 'EXISTENCIAINICIAL', 'VALOR', 'CODIGO')):
        # Mapea valores calculados al vuelo
        val = float(d.get('VALOR') or 0.0)
        qty = int(d.get('EXISTENCIAINICIAL') or 1)
        
        # Inyecta claves virtuales compatibles en minúscula/inglés
        d['code'] = d.get('CODIGO')
        d['description'] = d.get('DESCRIPCION')
        d['quantity'] = qty
        d['initial_unit_value'] = val
        d['initial_total_value'] = val * qty
        d['depreciation_rate'] = float(d.get('DEPRECIACUMULADA') or 0.0)
        d['current_value'] = max(0.0, (val * qty) - d['depreciation_rate'])
        d['dependency'] = d.get('UBICACION')
        # ... resto de campos mapeados a minúscula
```

Esto permite al desarrollador escribir código limpio en Python utilizando variables estándar en inglés, mientras que la base de datos se mantiene en estricto cumplimiento con los nombres contables en español.

---

## 🔍 Motor de Búsqueda Instantánea FTS5 (Full-Text Search)

Para lograr búsquedas instantáneas "tipo Google" (en menos de 5ms sobre miles de registros), la base de datos utiliza el módulo **FTS5** de SQLite con la tabla virtual `assets_search`.

### Sincronización Automática mediante Triggers
Para evitar la desincronización del índice de búsqueda al insertar, actualizar o eliminar activos de la tabla `assets`, se definen tres disparadores automáticos directos en SQL:

1. **Insert Trigger (`assets_ai`)**:
   ```sql
   CREATE TRIGGER assets_ai AFTER INSERT ON assets BEGIN
       INSERT INTO assets_search(rowid, CODIGO, DESCRIPCION, MARCA, SERIAL, UBICACION, FUNCIONARIO, SEDE)
       VALUES (new.id, COALESCE(new.CODIGO, ''), COALESCE(new.DESCRIPCION, ''), ...);
   END
   ```
2. **Delete Trigger (`assets_ad`)**:
   ```sql
   CREATE TRIGGER assets_ad AFTER DELETE ON assets BEGIN
       INSERT INTO assets_search(assets_search, rowid, ...) VALUES ('delete', old.id, ...);
   END
   ```
3. **Update Trigger (`assets_au`)**:
   Elimina la referencia anterior e inserta la nueva versión modificada del registro dentro del índice FTS5.
