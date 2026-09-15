import sqlite3
import os
import time

def borrar_todo():
    print("Iniciando borrado de la base de datos (MODO PRUEBAS)...")
    db_path = os.path.join(os.path.dirname(__file__), "inventory.db")
    
    if not os.path.exists(db_path):
        print("La base de datos no existe aún.")
        time.sleep(3)
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Borrar registros de las tablas principales
        cursor.execute("DELETE FROM assets;")
        cursor.execute("DELETE FROM dependencies;")
        cursor.execute("DELETE FROM loans;")
        cursor.execute("DELETE FROM audit_log;")
        
        # Limpiar y optimizar la base de datos
        cursor.execute("VACUUM;")
        
        conn.commit()
        conn.close()
        print("\n" + "="*50)
        print("¡ÉXITO! Se han borrado todos los inventarios (Guaimaral, Cuatro Bocas, etc).")
        print("La base de datos está completamente limpia para volver a importar.")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"Error al borrar la base de datos: {e}")
        print("Asegúrate de que la aplicación principal esté CERRADA antes de correr este script.")
        
    time.sleep(5)

if __name__ == "__main__":
    borrar_todo()
