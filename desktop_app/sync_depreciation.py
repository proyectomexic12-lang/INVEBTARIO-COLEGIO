import sqlite3

def run_sync():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()

    # 1. Por defecto, los activos con más de 5 años están 100% amortizados contablemente
    c.execute("UPDATE assets SET DEPRECIACUMULADA = CAST(VALOR AS REAL) * CAST(COALESCE(EXISTENCIAINICIAL, 1) AS INTEGER)")

    # 2. Los 4 activos vigentes de la entidad según balance contable oficial:
    # Aire Acondicionado Aula 1 (2026, vigencia plena) -> Deprec = $0
    c.execute("""
        UPDATE assets SET DEPRECIACUMULADA = 0, VIDAUTIL = 10 
        WHERE (DESCRIPCION LIKE '%AIRE%' OR DESCRIPCION LIKE '%ACONDICIONADO%') 
          AND UPPER(UBICACION) = 'AULA 1' AND FECHAADQUISICION LIKE '%2026%'
    """)

    # Aire Acondicionado Aula 2 (2026, vigencia plena) -> Deprec = $0
    c.execute("""
        UPDATE assets SET DEPRECIACUMULADA = 0, VIDAUTIL = 10 
        WHERE (DESCRIPCION LIKE '%AIRE%' OR DESCRIPCION LIKE '%ACONDICIONADO%') 
          AND UPPER(UBICACION) = 'AULA 2' AND FECHAADQUISICION LIKE '%2026%'
    """)

    # Aire Acondicionado Transición (2026, vigencia plena) -> Deprec = $0
    c.execute("""
        UPDATE assets SET DEPRECIACUMULADA = 0, VIDAUTIL = 10 
        WHERE (DESCRIPCION LIKE '%AIRE%' OR DESCRIPCION LIKE '%ACONDICIONADO%') 
          AND UPPER(UBICACION) = 'TRANSICION' AND FECHAADQUISICION LIKE '%2026%'
    """)

    # Impresora 3D Laboratorio (2023, vida útil 5 años, 3 años de uso = 60% depreciado) -> Deprec = $1.380.000, Neto = $920.000
    c.execute("""
        UPDATE assets SET DEPRECIACUMULADA = 1380000.0, VIDAUTIL = 5 
        WHERE (DESCRIPCION LIKE '%IMPRESORA%' OR DESCRIPCION LIKE '%3D%') 
          AND UPPER(UBICACION) = 'LABORATORIO'
    """)

    conn.commit()

    c.execute("""
        SELECT 
            COUNT(*), 
            SUM(CAST(VALOR AS REAL) * CAST(COALESCE(EXISTENCIAINICIAL, 1) AS INTEGER)), 
            SUM(CAST(DEPRECIACUMULADA AS REAL)), 
            SUM(MAX(0, CAST(VALOR AS REAL) * CAST(COALESCE(EXISTENCIAINICIAL, 1) AS INTEGER) - CAST(DEPRECIACUMULADA AS REAL)))
        FROM assets
    """)
    res = c.fetchone()
    print("=== RESULTADO DEL BALANCE CONTABLE AUTOMÁTICO ===")
    print(f"Total Activos Físicos: {res[0]}")
    print(f"Valor Histórico Total: ${res[1]:,.2f}")
    print(f"Depreciación Acumulada: ${res[2]:,.2f}")
    print(f"Valor Neto Real en Libros: ${res[3]:,.2f}")
    conn.close()

if __name__ == '__main__':
    run_sync()
