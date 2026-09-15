import sqlite3
import os

DB_PATH = "inventory.db"

def sync_dependencies():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all dependencies for Guaimaral
    cursor.execute("SELECT name FROM dependencies WHERE sede = 'Guaimaral'")
    guaimaral_deps = set(row[0] for row in cursor.fetchall())
    print(f"Guaimaral has {len(guaimaral_deps)} dependencies.")

    # Get all dependencies for Cuatro Bocas
    cursor.execute("SELECT name FROM dependencies WHERE sede = 'Cuatro Bocas'")
    cb_deps = set(row[0] for row in cursor.fetchall())
    print(f"Cuatro Bocas has {len(cb_deps)} dependencies.")

    # Find missing in Cuatro Bocas
    missing_in_cb = guaimaral_deps - cb_deps
    
    # Find missing in Guaimaral
    missing_in_guaimaral = cb_deps - guaimaral_deps

    print(f"Missing in Cuatro Bocas: {len(missing_in_cb)}")
    print(f"Missing in Guaimaral: {len(missing_in_guaimaral)}")

    # Sync to Cuatro Bocas
    for dep in missing_in_cb:
        try:
            cursor.execute("INSERT INTO dependencies (name, sede) VALUES (?, ?)", (dep, 'Cuatro Bocas'))
            print(f"Added {dep} to Cuatro Bocas")
        except Exception as e:
            print(f"Error adding {dep} to Cuatro Bocas: {e}")

    # Sync to Guaimaral
    for dep in missing_in_guaimaral:
        try:
            cursor.execute("INSERT INTO dependencies (name, sede) VALUES (?, ?)", (dep, 'Guaimaral'))
            print(f"Added {dep} to Guaimaral")
        except Exception as e:
            print(f"Error adding {dep} to Guaimaral: {e}")

    conn.commit()
    conn.close()
    print("Sync complete.")

if __name__ == '__main__':
    sync_dependencies()
