import os
import shutil
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, filedialog
from theme import theme

class ModernSettings(ctk.CTkScrollableFrame):
    def __init__(self, master, controller, setting_repo, audit_repo):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.setting_repo = setting_repo
        self.audit_repo = audit_repo
        self.entries = {}
        self.refresh_form()

    def refresh_form(self):
        for w in self.winfo_children(): w.destroy()
        self.entries = {}

        h = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=25)
        h.pack(fill="x", padx=40, pady=40)
        ctk.CTkLabel(h, text="⚙️ Configuración del Sistema",
                     font=ctk.CTkFont(size=32, weight="bold"),
                     text_color=theme.TEXT_MAIN).pack(pady=30, anchor="w", padx=40)

        # Tabview (Task 20)
        self.tabview = ctk.CTkTabview(self, fg_color="transparent")
        self.tabview.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        
        self.tab_config = self.tabview.add("Configuración de la Entidad")
        self.tab_backup = self.tabview.add("🛡️ Seguridad y Respaldo")
        self.tab_audit = self.tabview.add("Registro de Auditoría")

        settings = {
            "entidad": self.setting_repo.get_setting("entidad", ""),
            "nit": self.setting_repo.get_setting("nit", ""),
            "dane": self.setting_repo.get_setting("dane", ""),
            "representante": self.setting_repo.get_setting("representante", ""),
            "direccion": self.setting_repo.get_setting("direccion", ""),
            "telefono": self.setting_repo.get_setting("telefono", ""),
            "ciudad": self.setting_repo.get_setting("ciudad", ""),
            "año_trabajo": self.setting_repo.get_setting("año_trabajo", ""),
            "tema": self.setting_repo.get_setting("tema", "Slate Blue"),
        }

        card = ctk.CTkFrame(self.tab_config, fg_color=theme.BG_CARD, corner_radius=20,
                            border_width=1, border_color=theme.BORDER)
        card.pack(fill="x", padx=10, pady=10)

        fields = [
            ("Nombre Entidad",     "entidad", "entry"),
            ("NIT",                "nit", "entry"),
            ("Código DANE",        "dane", "entry"),
            ("Representante Legal","representante", "entry"),
            ("Dirección",          "direccion", "entry"),
            ("Teléfono",           "telefono", "entry"),
            ("Ciudad",             "ciudad", "entry"),
            ("Año de Trabajo",     "año_trabajo", "entry"),
            ("Tema del Sistema",   "tema", "theme_select"),
        ]

        for lbl, key, field_type in fields:
            f = ctk.CTkFrame(card, fg_color="transparent")
            f.pack(fill="x", padx=30, pady=10)
            ctk.CTkLabel(f, text=lbl.upper(),
                         font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=theme.TEXT_MUTED, width=220, anchor="w").pack(side="left")
            
            if field_type == "entry":
                e = ctk.CTkEntry(f, height=44, fg_color=theme.BG_INPUT,
                                 border_color=theme.BORDER, width=500,
                                 font=ctk.CTkFont(size=13),
                                 text_color=theme.TEXT_MAIN)
                e.insert(0, settings.get(key, ""))
                e.pack(side="left", fill="x", expand=True)
                self.entries[key] = e
            elif field_type == "theme_select":
                themes_list = list(theme.THEMES.keys())
                current_theme = settings.get(key, "Slate Blue")
                
                om = ctk.CTkOptionMenu(f, values=themes_list, height=44, width=500,
                                       fg_color=theme.BG_INPUT, button_color=theme.BORDER,
                                       button_hover_color=theme.PRIMARY, dropdown_fg_color=theme.BG_CARD,
                                       font=ctk.CTkFont(size=13), text_color=theme.TEXT_MAIN,
                                       dropdown_text_color=theme.TEXT_MAIN, dropdown_hover_color=theme.PRIMARY)
                om.set(current_theme)
                om.pack(side="left", fill="x", expand=True)
                self.entries[key] = om

        ctk.CTkButton(self.tab_config, text="💾 GUARDAR CAMBIOS",
                      height=60, font=ctk.CTkFont(size=15, weight="bold"),
                      fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER, corner_radius=15,
                      text_color="white",
                      command=self.save_settings).pack(fill="x", padx=10, pady=20)
                      
        # Setup Backup Tab & Audit Logs
        self.setup_backup_tab()
        self.setup_audit_tab()

    def save_settings(self):
        theme_changed = False
        
        for key, widget in self.entries.items():
            val = widget.get().strip()
            self.setting_repo.set_setting(key, val)
            if key == "tema":
                # Apply theme if changed
                if theme.set_theme_by_name(val):
                    theme_changed = True
                
        messagebox.showinfo("Control de Inventario", "✅ Configuración guardada correctamente.")
        
        if theme_changed:
            self.controller.recreate_all_pages()
        else:
            self.controller.invalidate_all_pages()

    def setup_backup_tab(self):
        container = ctk.CTkFrame(self.tab_backup, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Card 1: Exportar Respaldo
        c1 = ctk.CTkFrame(container, fg_color=theme.BG_CARD, corner_radius=18, border_width=1, border_color=theme.BORDER)
        c1.pack(fill="x", pady=(0, 15), padx=10)
        
        c1_top = ctk.CTkFrame(c1, fg_color="transparent")
        c1_top.pack(fill="x", padx=25, pady=(20, 10))
        ctk.CTkLabel(c1_top, text="💾 Copia de Seguridad Atómica (Exportar a USB o Disco)", font=ctk.CTkFont(size=16, weight="bold"), text_color=theme.TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(c1_top, text="Genera un respaldo íntegro y protegido del inventario en formato .db. Puede guardarse en una memoria USB, disco externo o enviarse por correo para resguardo institucional.",
                     font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED, wraplength=800, justify="left").pack(anchor="w", pady=(5, 0))

        c1_btn_f = ctk.CTkFrame(c1, fg_color="transparent")
        c1_btn_f.pack(fill="x", padx=25, pady=(10, 20))
        ctk.CTkButton(c1_btn_f, text="📦 CREAR COPIA DE SEGURIDAD AHORA", height=45, corner_radius=12,
                       fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER, font=ctk.CTkFont(size=13, weight="bold"),
                       command=self.export_backup).pack(side="left")

        # Card 2: Restaurar Respaldo
        c2 = ctk.CTkFrame(container, fg_color=theme.BG_CARD, corner_radius=18, border_width=1, border_color=theme.BORDER)
        c2.pack(fill="x", pady=(0, 15), padx=10)
        
        c2_top = ctk.CTkFrame(c2, fg_color="transparent")
        c2_top.pack(fill="x", padx=25, pady=(20, 10))
        ctk.CTkLabel(c2_top, text="📥 Restaurar Inventario desde una Copia de Seguridad", font=ctk.CTkFont(size=16, weight="bold"), text_color=theme.TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(c2_top, text="Carga un archivo de respaldo (.db) generado previamente. Útil para recuperar datos en caso de cambio de computador o formateo del sistema.",
                     font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED, wraplength=800, justify="left").pack(anchor="w", pady=(5, 5))
        
        warn_f = ctk.CTkFrame(c2_top, fg_color="#451a03", corner_radius=8, border_width=1, border_color="#b45309")
        warn_f.pack(fill="x", pady=5)
        ctk.CTkLabel(warn_f, text="⚠️ ADVERTENCIA: Esta acción reemplazará los datos actuales por los del archivo de copia. El sistema creará automáticamente un respaldo de emergencia de tus datos actuales antes de proceder.",
                     font=ctk.CTkFont(size=11, weight="bold"), text_color="#fde68a", wraplength=780, justify="left").pack(padx=12, pady=8, anchor="w")

        c2_btn_f = ctk.CTkFrame(c2, fg_color="transparent")
        c2_btn_f.pack(fill="x", padx=25, pady=(10, 20))
        ctk.CTkButton(c2_btn_f, text="⚠️ RESTAURAR BASE DE DATOS DESDE ARCHIVO", height=45, corner_radius=12,
                       fg_color=theme.WARNING, hover_color="#b45309", font=ctk.CTkFont(size=13, weight="bold"),
                       text_color="black", command=self.restore_backup).pack(side="left")

        # Card 3: Optimización y Mantenimiento
        c3 = ctk.CTkFrame(container, fg_color=theme.BG_CARD, corner_radius=18, border_width=1, border_color=theme.BORDER)
        c3.pack(fill="x", pady=(0, 15), padx=10)
        
        c3_top = ctk.CTkFrame(c3, fg_color="transparent")
        c3_top.pack(fill="x", padx=25, pady=(20, 10))
        ctk.CTkLabel(c3_top, text="⚡ Optimización y Mantenimiento del Sistema (VACUUM)", font=ctk.CTkFont(size=16, weight="bold"), text_color=theme.TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(c3_top, text="Compacta la base de datos eliminando espacio residual, reordena las páginas de memoria y reindexa los motores de búsqueda para máxima velocidad.",
                     font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED, wraplength=800, justify="left").pack(anchor="w", pady=(5, 0))

        c3_btn_f = ctk.CTkFrame(c3, fg_color="transparent")
        c3_btn_f.pack(fill="x", padx=25, pady=(10, 20))
        ctk.CTkButton(c3_btn_f, text="⚡ OPTIMIZAR Y COMPACTAR BASE DE DATOS", height=45, corner_radius=12,
                       fg_color="#334155", hover_color="#475569", font=ctk.CTkFont(size=13, weight="bold"),
                       command=self.optimize_database).pack(side="left")

    def export_backup(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"Copia_Seguridad_Inventario_Guaimaral_{timestamp}.db"
            target_path = filedialog.asksaveasfilename(
                title="Guardar Copia de Seguridad",
                defaultextension=".db",
                initialfile=default_name,
                filetypes=[("Base de Datos SQLite", "*.db"), ("Todos los archivos", "*.*")]
            )
            if not target_path:
                return

            if self.controller.db_manager.backup_to_file(target_path):
                self.audit_repo.log_event("database", 0, "BACKUP_EXPORTADO", None, {"archivo": target_path})
                messagebox.showinfo("Control de Inventario", f"✅ Copia de seguridad atómica creada exitosamente en:\n\n{target_path}")
            else:
                messagebox.showerror("Error", "No se pudo completar la copia de seguridad.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al crear la copia de seguridad: {e}")

    def restore_backup(self):
        try:
            confirm = messagebox.askyesno(
                "Confirmación de Seguridad",
                "⚠️ ¿Está completamente seguro de que desea restaurar una copia de seguridad?\n\n"
                "• Los datos actuales serán reemplazados por los de la copia.\n"
                "• El sistema guardará un respaldo previo de emergencia de sus datos actuales.\n\n"
                "¿Desea continuar?"
            )
            if not confirm:
                return

            source_path = filedialog.askopenfilename(
                title="Seleccionar Archivo de Respaldo",
                filetypes=[("Base de Datos SQLite", "*.db"), ("Todos los archivos", "*.*")]
            )
            if not source_path:
                return

            # Crear respaldo de emergencia previo
            db_dir = os.path.dirname(self.controller.db_manager.db_path)
            backup_dir = os.path.join(db_dir, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            emergency_path = os.path.join(backup_dir, f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            self.controller.db_manager.backup_to_file(emergency_path)

            # Restaurar
            if self.controller.db_manager.restore_from_file(source_path):
                self.audit_repo.log_event("database", 0, "BACKUP_RESTAURADO", None, {"archivo": source_path, "respaldo_previo": emergency_path})
                messagebox.showinfo("Control de Inventario", "✅ Base de datos restaurada correctamente.\nTodas las vistas del sistema han sido actualizadas.")
                self.controller.recreate_all_pages()
            else:
                messagebox.showerror("Error", "No se pudo restaurar la base de datos.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al restaurar la copia de seguridad:\n{e}")

    def optimize_database(self):
        try:
            if self.controller.db_manager.optimize_database():
                messagebox.showinfo("Control de Inventario", "✅ Mantenimiento preventivo completado con éxito.\nLa base de datos fue compactada y reindexada para máximo rendimiento.")
            else:
                messagebox.showerror("Error", "No se pudo completar la optimización.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al optimizar la base de datos: {e}")

    def setup_audit_tab(self):
        container = ctk.CTkFrame(self.tab_audit, fg_color=theme.BG_CARD, corner_radius=15, 
                                 border_width=1, border_color=theme.BORDER)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        desc_lbl = ctk.CTkLabel(container, text="Registro histórico de modificaciones del inventario (Últimos 200 eventos)", 
                                font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED)
        desc_lbl.pack(anchor="w", padx=20, pady=15)
        
        self.audit_scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.audit_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        h_row = ctk.CTkFrame(self.audit_scroll, fg_color=theme.BG_SIDEBAR, corner_radius=5)
        h_row.pack(fill="x", pady=2)
        
        ctk.CTkLabel(h_row, text="FECHA Y HORA", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED, width=150, anchor="w", padx=10).pack(side="left")
        ctk.CTkLabel(h_row, text="TABLA", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED, width=100, anchor="w").pack(side="left")
        ctk.CTkLabel(h_row, text="ID REGISTRO", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED, width=90).pack(side="left")
        ctk.CTkLabel(h_row, text="ACCIÓN", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED, width=100).pack(side="left")
        ctk.CTkLabel(h_row, text="DETALLES DE MODIFICACIÓN", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED, anchor="w", padx=10).pack(side="left", fill="x", expand=True)
        
        logs = self.audit_repo.get_audit_logs()
        if not logs:
            ctk.CTkLabel(self.audit_scroll, text="No hay eventos registrados en la bitácora de auditoría.", text_color=theme.TEXT_MUTED).pack(pady=40)
        else:
            def render_chunk(start_idx):
                end_idx = min(start_idx + 25, len(logs))
                for i in range(start_idx, end_idx):
                    log = logs[i]
                    bg = theme.BG_CARD if i % 2 == 0 else theme.BG_APP
                    row = ctk.CTkFrame(self.audit_scroll, fg_color=bg, corner_radius=5)
                    row.pack(fill="x", pady=1)
                    
                    # Format variables safely for dict compatibility vs normal rows
                    try:
                        ts = log.get('timestamp') if hasattr(log, 'get') else log[6]
                        tbl = (log.get('table_name') if hasattr(log, 'get') else log[1] or "").upper()
                        rec_id = str(log.get('record_id') if hasattr(log, 'get') else log[2] or "")
                        act = (log.get('action') if hasattr(log, 'get') else log[3] or "").upper()
                        old_val = log.get('old_data') if hasattr(log, 'get') else log[4] or ""
                        new_val = log.get('new_data') if hasattr(log, 'get') else log[5] or ""
                    except Exception:
                        continue
                    
                    details = f"Nuevo valor: {new_val}"
                    if old_val and old_val != "null" and old_val != '""':
                        details = f"Antes: {old_val} | Ahora: {new_val}"
                    
                    act_color = theme.PRIMARY
                    if "DELETE" in act or "BAJA" in act:
                        act_color = theme.ERROR
                    elif "INSERT" in act or "ADD" in act:
                        act_color = theme.SUCCESS
                    elif "UPDATE" in act or "TRANSFER" in act:
                        act_color = theme.WARNING
                        
                    ctk.CTkLabel(row, text=str(ts), font=ctk.CTkFont(size=11), text_color="#94a3b8", width=150, anchor="w", padx=10).pack(side="left")
                    ctk.CTkLabel(row, text=str(tbl), font=ctk.CTkFont(size=11, weight="bold"), text_color="#cbd5e1", width=100, anchor="w").pack(side="left")
                    ctk.CTkLabel(row, text=str(rec_id), font=ctk.CTkFont(size=11), text_color="#94a3b8", width=90).pack(side="left")
                    
                    act_lbl = ctk.CTkLabel(row, text=str(act), font=ctk.CTkFont(size=10, weight="bold"), text_color="white", fg_color=act_color, corner_radius=4, width=80)
                    act_lbl.pack(side="left", padx=10, pady=8)
                    
                    ctk.CTkLabel(row, text=str(details)[:120], font=ctk.CTkFont(size=11), text_color="#e2e8f0", anchor="w", padx=10).pack(side="left", fill="x", expand=True)

                if end_idx < len(logs):
                    self.after(15, lambda: render_chunk(end_idx))
            
            # Start rendering first chunk
            render_chunk(0)
