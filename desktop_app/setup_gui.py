import os
import sys
import zipfile
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Resource path handling for PyInstaller
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Instalador - Control Inventario I.E. Guaimaral")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        
        # Default install path: Documents
        self.default_path = os.path.join(os.path.expanduser("~"), "Documents", "Inventario_IE_Guaimaral")
        self.install_path = tk.StringVar(value=self.default_path)
        
        self.setup_ui()
        
    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_lbl = ttk.Label(main_frame, text="Bienvenido al Instalador", font=("Helvetica", 16, "bold"))
        title_lbl.pack(pady=(0, 10))
        
        desc_lbl = ttk.Label(main_frame, text="Este programa instalara el Control de Inventario en su equipo.\nPor favor seleccione la ruta de instalacion.", justify=tk.CENTER)
        desc_lbl.pack(pady=(0, 20))
        
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(path_frame, text="Ruta de instalacion:").pack(anchor=tk.W)
        path_entry = ttk.Entry(path_frame, textvariable=self.install_path, width=40)
        path_entry.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(path_frame, text="Examinar...", command=self.browse_path)
        browse_btn.pack(side=tk.RIGHT)
        
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=20)
        
        self.status_lbl = ttk.Label(main_frame, text="Listo para instalar.")
        self.status_lbl.pack(pady=5)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.install_btn = ttk.Button(btn_frame, text="Instalar", command=self.start_install)
        self.install_btn.pack(side=tk.RIGHT, padx=5)
        
        self.cancel_btn = ttk.Button(btn_frame, text="Cancelar", command=self.root.destroy)
        self.cancel_btn.pack(side=tk.RIGHT, padx=5)

    def browse_path(self):
        directory = filedialog.askdirectory(initialdir=self.default_path, title="Seleccione la carpeta destino")
        if directory:
            self.install_path.set(os.path.join(directory, "Inventario_IE_Guaimaral"))

    def start_install(self):
        self.install_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.DISABLED)
        self.status_lbl.config(text="Instalando... por favor espere.")
        self.root.update()
        
        target_dir = self.install_path.get()
        try:
            os.makedirs(target_dir, exist_ok=True)
            
            # Extract ZIP
            zip_path = resource_path('payload.zip')
            if not os.path.exists(zip_path):
                raise Exception(f"No se encontro el paquete de datos en {zip_path}")
                
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                total_files = len(zip_ref.infolist())
                for i, file_info in enumerate(zip_ref.infolist()):
                    zip_ref.extract(file_info, target_dir)
                    self.progress['value'] = (i / total_files) * 100
                    if i % 10 == 0:
                        self.root.update()
            
            self.progress['value'] = 100
            self.status_lbl.config(text="Creando accesos directos...")
            self.root.update()
            
            # Create Shortcut using native VBScript
            exe_path = os.path.join(target_dir, "Control_Inventario_IE_Guaimaral.exe")
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop, "Control Inventario I.E. Guaimaral.lnk")
            
            vbs_script = f'''
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{shortcut_path}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{exe_path}"
oLink.WorkingDirectory = "{target_dir}"
oLink.Save
'''
            vbs_path = os.path.join(target_dir, "create_shortcut.vbs")
            with open(vbs_path, "w") as f:
                f.write(vbs_script)
            
            import subprocess
            subprocess.run(["cscript.exe", "//Nologo", vbs_path], shell=True)
            os.remove(vbs_path)
            
            messagebox.showinfo("Instalacion Completa", "El programa se ha instalado correctamente.\\nSe ha creado un acceso directo en su escritorio.")
            self.root.destroy()
            
        except Exception as e:
            messagebox.showerror("Error de Instalacion", f"Ocurrio un error:\n{str(e)}")
            self.install_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()
