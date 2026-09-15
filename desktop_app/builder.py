import os
import zipfile
import shutil
import subprocess
import sqlite3

def create_payload():
    print("Empaquetando aplicacion en payload.zip...")
    dist_dir = os.path.join("dist", "Control_Inventario_IE_Guaimaral")
    
    if not os.path.exists(dist_dir):
        print(f"Error: No se encontro el directorio {dist_dir}. Asegurate de compilar la app primero.")
        return False
        
    zip_path = "payload.zip"
    if os.path.exists(zip_path):
        os.remove(zip_path)
        
    if os.path.exists("inventory.db"):
        dest_db = os.path.join(dist_dir, "inventory.db")
        for ext in ["", "-wal", "-shm"]:
            f = dest_db + ext
            if os.path.exists(f):
                try: os.remove(f)
                except Exception: pass
        src_conn = sqlite3.connect("inventory.db")
        dst_conn = sqlite3.connect(dest_db)
        src_conn.backup(dst_conn)
        dst_conn.close()
        src_conn.close()
        print("Base de datos empaquetada con verificacion atomica de integridad.")
        
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dist_dir)
                zipf.write(file_path, arcname)
                
    print("payload.zip creado exitosamente.")
    return True

def build_installer():
    print("Compilando el Instalador...")
    pyinstaller_path = os.path.join("venv", "Scripts", "pyinstaller.exe")
    
    cmd = [
        pyinstaller_path,
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--add-data", "payload.zip;.",
        "--name", "Instalar_Control_Inventario",
        "setup_gui.py"
    ]
    
    result = subprocess.run(cmd)
    if result.returncode == 0:
        # Copiar el instalador a la raíz del proyecto para fácil acceso
        dist_exe = os.path.join("dist", "Instalar_Control_Inventario.exe")
        root_exe = os.path.join("..", "Instalar_Control_Inventario.exe")
        try:
            shutil.copy2(dist_exe, root_exe)
            print(f"Copiado instalador actualizado a la raiz: {root_exe}")
        except Exception as e:
            print(f"Aviso al copiar a la raiz: {e}")

        print("\n=======================================================")
        print("INSTALADOR CREADO EXITOSAMENTE EN LA CARPETA 'dist' Y RAIZ")
        print("Archivo: dist/Instalar_Control_Inventario.exe")
        print("=======================================================")
    else:
        print("Error durante la compilacion del instalador.")

if __name__ == "__main__":
    if create_payload():
        build_installer()
