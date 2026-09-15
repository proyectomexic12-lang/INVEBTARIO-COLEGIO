import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
import re
from theme import theme

class ModernRegistry(ctk.CTkScrollableFrame):
    def __init__(self, master, controller, asset_repo, dep_repo, setting_repo):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.asset_repo = asset_repo
        self.dep_repo = dep_repo
        self.setting_repo = setting_repo
        self.get_entries = {}
        
        # --- Technical Sheet Header ---
        self.header_card = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=20, border_width=1, border_color=theme.BORDER)
        self.header_card.pack(fill="x", padx=40, pady=(35, 15))
        
        h_inner = ctk.CTkFrame(self.header_card, fg_color="transparent")
        h_inner.pack(padx=30, pady=22, fill="x")
        
        meta_f = ctk.CTkFrame(h_inner, fg_color="transparent")
        meta_f.pack(side="left")
        ctk.CTkLabel(meta_f, text="PROTOCOLO DE INCORPORACIÓN ACTIVA", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.PRIMARY_LIGHT).pack(anchor="w")
        ctk.CTkLabel(meta_f, text="Ficha Técnica de Activos", font=ctk.CTkFont(size=28, weight="bold"), text_color=theme.TEXT_MAIN).pack(anchor="w")
        
        self.stat_badge = ctk.CTkFrame(h_inner, fg_color=theme.SUCCESS_BG, border_width=1, border_color=theme.SUCCESS, corner_radius=10)
        self.stat_badge.pack(side="right", padx=10)
        ctk.CTkLabel(self.stat_badge, text="● SISTEMA LISTO", font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.SUCCESS).pack(padx=16, pady=8)

        # --- High-Definition Form Body ---
        self.form_body = ctk.CTkFrame(self, fg_color="transparent")
        self.form_body.pack(fill="both", expand=True, padx=40)

        init_sede = getattr(self.controller, "global_sede", "Guaimaral")
        if not init_sede or init_sede == "Todas":
            init_sede = "Guaimaral"

        all_sedes = self.asset_repo.get_all_sedes()
        db_deps = self.dep_repo.get_dependencies(sede=init_sede)
        available_deps = db_deps if db_deps else ["SIN DEPENDENCIAS"]

        self.section_origin = self.create_hd_section("I. IDENTIFICACIÓN Y UBICACIÓN PRIMARIA", "🏢")
        self.create_entry_grid(self.section_origin, [
            ("Sede Institucional", "sede", all_sedes),
            ("Dependencia / Salón", "dep", available_deps),
            ("Código Artículo", "code", None),
            ("Código Contable", "acc_code", None),
            ("Descripción", "desc", None, 2)
        ], cols=2)

        self.section_specs = self.create_hd_section("II. ESPECIFICACIONES", "🔧")
        self.create_entry_grid(self.section_specs, [
            ("Marca", "brand", None),
            ("Serial No.", "serial", None),
            ("Estado de Conservación", "state", ["Excelente", "Bueno", "Regular", "Malo"]),
        ], cols=2)

        self.section_accounting = self.create_hd_section("III. VALORIZACIÓN Y CICLO DE VIDA", "💰")
        self.create_entry_grid(self.section_accounting, [
            ("Valor de Adquisición", "val_uni", None),
            ("Cantidad (Existencia Inicial)", "qty", None),
            ("Depreciación Acumulada", "depr", None),
            ("Vida Útil", "life", None),
            ("Fecha Adquisición", "date_in", None)
        ], cols=2)

        self.section_sede = self.create_hd_section("IV. DATOS CONTABLES Y ASIGNACIÓN ESPECÍFICA", "📋")
        self.create_entry_grid(self.section_sede, [
            ("Código Depreciación", "cod_depr", None),
            ("Código Gasto", "cod_gasto", None),
            ("Funcionario Responsable", "func", None),
            ("Identificación (NIT/CC)", "ident", None),
            ("Código Grupo", "grupo", None),
            ("Código Subgrupo", "subgrupo", None),
            ("Tipo", "tipo", None)
        ], cols=2)

        # --- Submission Command Center ---
        self.footer = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=25, border_width=1, border_color="#1e293b")
        self.footer.pack(pady=(40, 100), fill="x", padx=40)
        
        f_inner = ctk.CTkFrame(self.footer, fg_color="transparent")
        f_inner.pack(padx=30, pady=25, fill="x")
        
        ctk.CTkButton(f_inner, text="💾 PROCESAR E INCORPORAR ACTIVO", 
                                 font=ctk.CTkFont(size=15, weight="bold"), 
                                 height=60, fg_color="#3b82f6", hover_color="#2563eb", 
                                 corner_radius=15, command=self.save_asset).pack(side="right", padx=10, fill="x", expand=True)
        
        ctk.CTkButton(f_inner, text="📂 IMPORTACIÓN MASIVA (EXCEL)", 
                                 font=ctk.CTkFont(size=14, weight="bold"), 
                                 height=60, fg_color="#1e293b", hover_color="#334155", 
                                 border_width=1, border_color="#334155",
                                 corner_radius=15, command=self.load_from_excel).pack(side="right", padx=10, fill="x", expand=True)
        
        ctk.CTkButton(f_inner, text="Limpiar Ficha", 
                                   height=60, width=180, fg_color="transparent", 
                                   border_width=1, border_color="#ef4444", text_color="#ef4444", 
                                   corner_radius=15, command=self.refresh_form).pack(side="left")
        
        ctk.CTkButton(f_inner, text="⚙️ CONFIGURAR MAPEO", 
                                   height=60, width=180, fg_color="transparent", 
                                   border_width=1, border_color="#e5e7eb", text_color="#e5e7eb", 
                                   corner_radius=15, command=self.configure_mapping).pack(side="left", padx=10)

        # Initial form population with active sede and auto-generated code
        self.refresh_form()

    def create_hd_section(self, title, icon):
        card = ctk.CTkFrame(self.form_body, fg_color=theme.BG_CARD, corner_radius=18, border_width=1, border_color=theme.BORDER)
        card.pack(fill="x", pady=10)
        
        header = ctk.CTkFrame(card, fg_color=theme.BG_SIDEBAR, height=42, corner_radius=0)
        header.pack(fill="x", padx=1, pady=1)
        ctk.CTkLabel(header, text=f"{icon}  {title}", font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.PRIMARY_LIGHT).pack(side="left", padx=20)
        
        grid_f = ctk.CTkFrame(card, fg_color="transparent")
        grid_f.pack(fill="x", padx=20, pady=(15, 20))
        return grid_f

    def create_entry_grid(self, parent, items, cols=2):
        for i, item in enumerate(items):
            label_text, key, values, *extra = item
            span = extra[0] if extra else 1
            
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.grid(row=i // cols, column=i % cols, columnspan=span, sticky="nsew", padx=12, pady=10)
            
            ctk.CTkLabel(f, text=label_text.upper(), font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_FAINT).pack(anchor="w", padx=4, pady=(0, 5))
            
            if values:
                cmd = self.on_sede_selection_changed if key == "sede" else None
                w = ctk.CTkComboBox(f, values=values, height=42, corner_radius=10, border_width=1, border_color=theme.BORDER, fg_color=theme.BG_INPUT, command=cmd)
            else:
                w = ctk.CTkEntry(f, height=42, corner_radius=10, border_width=1, border_color=theme.BORDER, fg_color=theme.BG_INPUT, placeholder_text="---")
            w.pack(fill="x")
            self.get_entries[key] = w
            
            # Bind Return key for barcode scanners / enter key navigation (Task 19)
            if isinstance(w, ctk.CTkEntry):
                w.bind("<Return>", lambda e, k=key: self.on_field_enter(k))
        
        for c in range(cols): parent.grid_columnconfigure(c, weight=1)

    def on_sede_selection_changed(self, selected_sede):
        if "dep" in self.get_entries:
            deps = self.dep_repo.get_dependencies(sede=selected_sede)
            new_vals = deps if deps else ["SIN DEPENDENCIAS"]
            self.get_entries["dep"].configure(values=new_vals)
            self.get_entries["dep"].set(new_vals[0])

        if "code" in self.get_entries:
            curr = self.get_entries["code"].get().strip()
            if not curr or curr.startswith("NX-"):
                new_code = self.asset_repo.generate_next_code(sede=selected_sede)
                self.get_entries["code"].delete(0, 'end')
                self.get_entries["code"].insert(0, new_code)

    def on_field_enter(self, key):
        if key == "code":
            code_val = self.get_entries["code"].get().strip()
            if code_val:
                self.load_asset_by_code(code_val)
            else:
                self.focus_next_field(key)
        else:
            self.focus_next_field(key)

    def load_asset_by_code(self, code_val):
        asset = self.asset_repo.get_asset_by_code(code_val)
        if asset:
            mapping = {
                "dep": "UBICACION",
                "code": "CODIGO",
                "acc_code": "CODCONTABLE",
                "desc": "DESCRIPCION",
                "brand": "MARCA",
                "serial": "SERIAL",
                "val_uni": "VALOR",
                "qty": "EXISTENCIAINICIAL",
                "depr": "DEPRECIACUMULADA",
                "date_in": "FECHAADQUISICION",
                "date_svc": "FECHAADQUISICION",
                "life": "VIDAUTIL",
                "state": "conservation_state",
                "cod_depr": "CODDEPRECIACION",
                "cod_gasto": "CODGASTO",
                "func": "FUNCIONARIO",
                "ident": "IDENTIFICACION",
                "sede": "SEDE"
            }
            for key, widget in self.get_entries.items():
                db_col = mapping.get(key)
                if db_col:
                    val = asset.get(db_col)
                    if val is not None:
                        if isinstance(widget, ctk.CTkComboBox):
                            widget.set(str(val))
                        elif isinstance(widget, ctk.CTkEntry):
                            widget.delete(0, 'end')
                            widget.insert(0, str(val))
            messagebox.showinfo("Activo Encontrado", f"El activo con código '{code_val}' ya existe. Se han cargado sus datos para edición.")
            self.focus_next_field("code")
        else:
            self.focus_next_field("code")

    def focus_next_field(self, current_key):
        keys_seq = [
            "sede", "dep", "code", "acc_code", "desc", "brand", "serial", 
            "state", "val_uni", "qty", "depr", 
            "life", "date_in", 
            "cod_depr", "cod_gasto", "func", "ident", "grupo", "subgrupo", "tipo"
        ]
        try:
            idx = keys_seq.index(current_key)
            if idx + 1 < len(keys_seq):
                next_key = keys_seq[idx + 1]
                widget = self.get_entries[next_key]
                widget.focus_set()
                if isinstance(widget, ctk.CTkEntry):
                    widget.select_range(0, 'end')
                    widget.icursor('end')
        except ValueError:
            pass

    def refresh_form(self):
        for w in self.get_entries.values():
            if isinstance(w, ctk.CTkEntry): w.delete(0, 'end')

        active_sede = getattr(self.controller, "global_sede", "Guaimaral")
        if not active_sede or active_sede == "Todas":
            active_sede = "Guaimaral"

        all_sedes = self.asset_repo.get_all_sedes()
        if "sede" in self.get_entries:
            self.get_entries["sede"].configure(values=all_sedes)
            if active_sede in all_sedes:
                self.get_entries["sede"].set(active_sede)
            elif all_sedes:
                self.get_entries["sede"].set(all_sedes[0])
            chosen_sede = self.get_entries["sede"].get()
        else:
            chosen_sede = active_sede

        if "dep" in self.get_entries:
            deps = self.dep_repo.get_dependencies(sede=chosen_sede)
            new_vals = deps if deps else ["SIN DEPENDENCIAS"]
            self.get_entries["dep"].configure(values=new_vals)
            self.get_entries["dep"].set(new_vals[0])

        if "code" in self.get_entries:
            new_code = self.asset_repo.generate_next_code(sede=chosen_sede)
            self.get_entries["code"].delete(0, 'end')
            self.get_entries["code"].insert(0, new_code)

        if "state" in self.get_entries:
            self.get_entries["state"].set("Excelente")

    def save_asset(self):
        try:
            def v(k): return self.get_entries[k].get().strip()
            
            def validate_date(date_str):
                if not date_str: return True
                try:
                    datetime.strptime(date_str, "%d/%m/%Y")
                    return True
                except ValueError:
                    return False

            def is_non_negative_float(val_str):
                if not val_str: return True
                try:
                    f = float(str(val_str).replace('$','').replace(',','').replace(' ',''))
                    return f >= 0.0
                except ValueError:
                    return False

            def is_positive_int(val_str):
                if not val_str: return True
                try:
                    i = int(str(val_str).replace(',','').replace(' ',''))
                    return i > 0
                except ValueError:
                    return False

            def validate_ident(ident_str):
                if not ident_str: return True
                return bool(re.match(r'^[0-9a-zA-Z.-]+$', ident_str))

            def clean_f(val):
                if not val: return None
                try: return float(str(val).replace('$','').replace(',','').replace(' ',''))
                except: return None


            if not v("desc"):
                messagebox.showwarning("Campo Obligatorio", "La descripción del activo es obligatoria.")
                return
            if not v("qty"):
                messagebox.showwarning("Campo Obligatorio", "La cantidad es obligatoria.")
                return
            if not v("val_uni"):
                messagebox.showwarning("Campo Obligatorio", "El valor unitario inicial es obligatorio.")
                return

            # Validar Fechas (Task 15)
            if v("date_in") and not validate_date(v("date_in")):
                messagebox.showwarning("Fecha Inválida", "La fecha de ingreso debe tener el formato AAAA-MM-DD.")
                return
            if v("date_svc") and not validate_date(v("date_svc")):
                messagebox.showwarning("Fecha Inválida", "La fecha de puesta en servicio debe tener el formato AAAA-MM-DD.")
                return

            # Validar Valores Contables (Task 15)
            if v("val_uni") and not is_non_negative_float(v("val_uni")):
                messagebox.showwarning("Valor Inválido", "El valor unitario inicial debe ser un número no negativo.")
                return
            if v("depr") and not is_non_negative_float(v("depr")):
                messagebox.showwarning("Valor Inválido", "La depreciación acumulada debe ser un número no negativo.")
                return

            # Validar Cantidad y Vida Útil (Task 15)
            if v("qty") and not is_positive_int(v("qty")):
                messagebox.showwarning("Cantidad Inválida", "La cantidad debe ser un número entero mayor a 0.")
                return
            if v("life"):
                try:
                    life_val = int(v("life"))
                    if life_val < 0: raise ValueError()
                except ValueError:
                    messagebox.showwarning("Vida Útil Inválida", "La vida útil restante debe ser un número entero no negativo.")
                    return

            # Validar Identificación/NIT (Task 15)
            if v("ident") and not validate_ident(v("ident")):
                messagebox.showwarning("Identificación Inválida", "La identificación / NIT debe contener únicamente números, letras, puntos o guiones.")
                return

            dep_val = v("dep")
            if not dep_val or str(dep_val).strip().upper() in ("SIN DEPENDENCIAS", "GENERAL"):
                dep_val = "SIN ASIGNAR"
            sede_val = v("sede") or getattr(self.controller, "global_sede", "Guaimaral")
            if not sede_val or sede_val == "Todas":
                sede_val = "Guaimaral"

            # Auto-register room in dependencies for this sede if not present
            if dep_val and dep_val != "SIN ASIGNAR":
                self.dep_repo.add_dependency(dep_val, "AULA", sede=sede_val)

            qty_raw = v("qty")
            try: qty = int(qty_raw) if qty_raw else 1
            except: qty = 1
            
            val_uni = clean_f(v("val_uni")) or 0.0
            val_tot = clean_f(v("val_tot")) or (val_uni * qty)
            depr_val = clean_f(v("depr")) or 0.0
            val_cur = clean_f(v("val_cur")) or max(0.0, val_tot - depr_val)
            
            life = 10
            try: life = int(v("life"))
            except: pass

            code_val = v("code") or self.asset_repo.generate_next_code(sede=sede_val)

            data = (
                code_val,
                v("acc_code") or "101",
                "General",
                v("desc"),
                v("brand") or "N/A",
                "N/A",
                v("serial") or "N/A",
                "N/A",
                "N/A",
                "N/A",
                val_uni, qty, val_tot, depr_val, val_cur,
                v("date_in") or datetime.now().strftime("%d/%m/%Y"),
                datetime.now().strftime("%d/%m/%Y"),
                life,
                v("state") or "Bueno",
                "Propio",
                "En Uso",
                dep_val,
                v("cod_depr") or "",
                v("cod_gasto") or "",
                v("func") or "",
                v("ident") or "",
                v("grupo") or "",
                v("subgrupo") or "",
                v("tipo") or "",
                sede_val
            )
            if self.asset_repo.add_asset(data):
                self.controller.invalidate_all_pages()
                messagebox.showinfo("Proceso Exitoso", "El activo se ha registrado exitosamente en el inventario.")
                self.refresh_form()
            else:
                messagebox.showerror("Falla de Motor", "No se pudo integrar el activo. Verifique los datos o el estado de la base de datos.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al guardar: {e}")

    def load_from_excel(self):
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(filetypes=(("Libros de Excel (*.xlsx)", "*.xlsx *.xlsm"), ("Archivos Excel", "*.xlsx *.xls"), ("Todos los archivos", "*.*")))
        if not filepath: return
        self.controller.run_in_thread_with_loader("Analizando e importando archivo Excel...", self.controller.run_intelligent_import, self._import_finished, filepath)

    def _import_finished(self, added):
        if added > 0:
            if hasattr(self.controller, "change_global_sede"):
                self.controller.change_global_sede("Todas")
            else:
                self.controller.invalidate_all_pages()
            messagebox.showinfo(
                "¡Importación Exitosa!", 
                f"¡Importación Masiva completada con éxito!\n\n"
                f"Se han incorporado {added} activos al inventario.\n\n"
                f"La vista global se ha fijado en 'Todas las Sedes' para visualizarlos de inmediato."
            )
            self.controller.select_page("ModernInventory", "Gestión Global")
        else:
            messagebox.showwarning(
                "Importación Incompleta", 
                "No se incorporó ningún activo (0 registros procesados).\n\n"
                "Posibles causas:\n"
                "• Los encabezados no coinciden. Pulse '⚙️ CONFIGURAR MAPEO' para asociar las columnas.\n"
                "• La hoja seleccionada no contiene registros válidos."
            )

    def configure_mapping(self):
        ConfigureKeywordsDialog(self)


class ConfigureKeywordsDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        self.title("CONFIGURAR MAPEO INTELIGENTE EXCEL")
        self.geometry("600x650")
        self.configure(fg_color="#0a0f1d")
        
        self.grab_set()
        self.focus()
        self.transient(parent)
        
        # Center dialog
        self.update_idletasks()
        width, height = 600, 650
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        container = ctk.CTkScrollableFrame(self, fg_color="#0f172a", corner_radius=20, border_width=1, border_color="#1e293b")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(container, text="MAPEO DE COLUMNAS EXCEL", font=ctk.CTkFont(size=11, weight="bold"), text_color="#3b82f6").pack(anchor="w", padx=15, pady=(15, 2))
        ctk.CTkLabel(container, text="Personalizar Palabras Clave (Separadas por Comas)", font=ctk.CTkFont(size=20, weight="bold"), text_color="#f8fafc").pack(anchor="w", padx=15, pady=(0, 10))
        
        self.keywords = self.parent.setting_repo.get_excel_keywords()
        self.entries = {}
        
        fields = [
            ("Código Artículo", "code", "Palabras para identificar la columna del código (placa)"),
            ("Descripción", "desc", "Palabras para identificar la columna de descripción"),
            ("Valor Unitario", "val_uni", "Palabras para identificar el precio unitario"),
            ("Cantidad", "qty", "Palabras para identificar existencias / unidades"),
            ("Responsable / Funcionario", "func", "Palabras para el responsable del bien"),
            ("Ubicación / Dependencia", "dep", "Palabras para la dependencia o aula"),
            ("Serial", "serial", "Palabras para el número de serie"),
            ("Marca", "brand", "Palabras para la marca")
        ]
        
        for label, key, desc in fields:
            f = ctk.CTkFrame(container, fg_color="transparent")
            f.pack(fill="x", padx=15, pady=10)
            
            ctk.CTkLabel(f, text=label.upper(), font=ctk.CTkFont(size=11, weight="bold"), text_color="#f8fafc").pack(anchor="w")
            ctk.CTkLabel(f, text=desc, font=ctk.CTkFont(size=9), text_color="#475569").pack(anchor="w", pady=(0, 4))
            
            curr_val = ", ".join(self.keywords.get(key, []))
            entry = ctk.CTkEntry(f, height=40, corner_radius=10, border_width=1, border_color="#1e293b", fg_color="#020617")
            entry.pack(fill="x")
            entry.insert(0, curr_val)
            self.entries[key] = entry
            
        actions = ctk.CTkFrame(container, fg_color="transparent")
        actions.pack(fill="x", padx=15, pady=20)
        
        ctk.CTkButton(actions, text="💾 GUARDAR CONFIGURACIÓN", font=ctk.CTkFont(size=13, weight="bold"), height=44, fg_color="#3b82f6", hover_color="#2563eb", text_color="white", corner_radius=10, command=self.save).pack(side="right", fill="x", expand=True, padx=(8, 0))
        ctk.CTkButton(actions, text="Cancelar", font=ctk.CTkFont(size=13), height=44, fg_color="#1e293b", hover_color="#334155", corner_radius=10, command=self.destroy).pack(side="left", padx=(0, 8))

    def save(self):
        from tkinter import messagebox
        for key, entry in self.entries.items():
            val = entry.get().strip()
            kws = [x.strip().upper() for x in val.split(",") if x.strip()]
            self.keywords[key] = kws
            
        if self.parent.setting_repo.save_excel_keywords(self.keywords):
            messagebox.showinfo("Éxito", "Configuración de mapeo guardada correctamente.")
            self.destroy()
        else:
            messagebox.showerror("Error", "No se pudo guardar la configuración.")
