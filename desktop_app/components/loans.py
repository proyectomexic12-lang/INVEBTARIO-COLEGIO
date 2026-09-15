import customtkinter as ctk
import tkinter as tk
from datetime import datetime
import re
from theme import theme
from scroll_helper import enable_smooth_scroll

def normalize_date_input(date_str):
    s = str(date_str).strip()
    if not s:
        return datetime.now().strftime("%Y-%m-%d")
    m = re.match(r'^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$', s)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.match(r'^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$', s)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return s

def format_date_display(iso_date):
    s = str(iso_date).strip()
    m = re.match(r'^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$', s)
    if m:
        return f"{int(m.group(3)):02d}/{int(m.group(2)):02d}/{m.group(1)}"
    return s


class EditLoanDialog(ctk.CTkToplevel):
    def __init__(self, parent, loan_data, on_save_callback):
        super().__init__(parent)
        self.parent = parent
        self.loan = loan_data
        self.on_save = on_save_callback

        self.title("✏️ EDITAR PRÉSTAMO")
        self.geometry("520x520")
        self.configure(fg_color="#0a0f1d")
        self.resizable(False, False)

        self.grab_set()
        self.focus()
        self.transient(parent)

        self.update_idletasks()
        width, height = 520, 520
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        container = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=20, border_width=1, border_color="#1e293b")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        ctk.CTkLabel(container, text="MODIFICAR REGISTRO DE PRÉSTAMO", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#3b82f6").pack(anchor="w", padx=25, pady=(20, 2))
        item_title = f"[{self.loan.get('code') or 'S/C'}] {self.loan.get('description') or 'Activo'}"
        ctk.CTkLabel(container, text=item_title[:42], font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#f8fafc").pack(anchor="w", padx=25, pady=(0, 15))

        # Teacher Name
        ctk.CTkLabel(container, text="DOCENTE / PROFESOR RESPONSABLE", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color="#94a3b8").pack(anchor="w", padx=25, pady=(0, 4))
        self.teacher_entry = ctk.CTkEntry(container, height=40, corner_radius=10, fg_color="#020617",
                                          border_color="#1e293b", font=ctk.CTkFont(size=13))
        self.teacher_entry.pack(fill="x", padx=25, pady=(0, 12))
        self.teacher_entry.insert(0, self.loan.get("teacher_name") or "")

        # Teacher Phone
        ctk.CTkLabel(container, text="CÉDULA DE CIUDADANÍA", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color="#94a3b8").pack(anchor="w", padx=25, pady=(0, 4))
        self.phone_entry = ctk.CTkEntry(container, height=40, corner_radius=10, fg_color="#020617",
                                        border_color="#1e293b", font=ctk.CTkFont(size=13),
                                        placeholder_text="Ej: 22.656.974")
        self.phone_entry.pack(fill="x", padx=25, pady=(0, 12))
        self.phone_entry.insert(0, self.loan.get("teacher_phone") or "")

        # Return Date
        ctk.CTkLabel(container, text="FECHA (DD/MM/AAAA)",
                     font=ctk.CTkFont(size=10, weight="bold"), text_color="#94a3b8").pack(anchor="w", padx=25, pady=(0, 4))
        self.date_entry = ctk.CTkEntry(container, height=40, corner_radius=10, fg_color="#020617",
                                       border_color="#1e293b", font=ctk.CTkFont(size=13))
        self.date_entry.pack(fill="x", padx=25, pady=(0, 12))
        disp_date = format_date_display(self.loan.get("expected_return_date") or "")
        self.date_entry.insert(0, disp_date)

        # Quantity
        ctk.CTkLabel(container, text="CANTIDAD DE UNIDADES", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color="#94a3b8").pack(anchor="w", padx=25, pady=(0, 4))
        self.qty_entry = ctk.CTkEntry(container, height=40, corner_radius=10, fg_color="#020617",
                                      border_color="#1e293b", font=ctk.CTkFont(size=13))
        self.qty_entry.pack(fill="x", padx=25, pady=(0, 20))
        self.qty_entry.insert(0, str(self.loan.get("loan_qty") or 1))

        # Action Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", padx=25, pady=(5, 10))

        ctk.CTkButton(btn_frame, text="💾 GUARDAR CAMBIOS", fg_color="#3b82f6", hover_color="#2563eb",
                      height=42, font=ctk.CTkFont(size=13, weight="bold"), corner_radius=10,
                      command=self.save_changes).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(btn_frame, text="Cancelar", fg_color="#334155", hover_color="#475569",
                      height=42, width=100, font=ctk.CTkFont(size=12), corner_radius=10,
                      command=self.destroy).pack(side="right")

    def save_changes(self):
        from tkinter import messagebox
        t_name = self.teacher_entry.get().strip()
        t_phone = self.phone_entry.get().strip()
        d_val = self.date_entry.get().strip()
        q_val = self.qty_entry.get().strip()

        if not t_name:
            messagebox.showwarning("Atención", "El nombre del docente es obligatorio.")
            return

        try:
            qty_num = int(q_val)
            if qty_num <= 0: raise ValueError()
        except:
            messagebox.showwarning("Atención", "La cantidad debe ser un número entero mayor a 0.")
            return

        iso_date = normalize_date_input(d_val)
        try:
            datetime.strptime(iso_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Fecha Inválida", "Por favor ingrese una fecha válida (ej: 25/12/2026).")
            return

        self.on_save(self.loan['id'], t_name, t_phone, iso_date, qty_num)
        self.destroy()

    def destroy(self):
        try:
            self.grab_release()
        except Exception:
            pass
        super().destroy()


class ReturnLoanDialog(ctk.CTkToplevel):
    def __init__(self, parent, loan_data, dependencies, on_return_callback):
        super().__init__(parent)
        self.parent = parent
        self.loan = loan_data
        self.dependencies = dependencies
        self.on_return = on_return_callback

        self.title("📦 DEVOLVER Y TRASLADAR")
        self.geometry("500x380")
        self.configure(fg_color="#0a0f1d")
        self.resizable(False, False)

        self.grab_set()
        self.focus()
        self.transient(parent)

        self.update_idletasks()
        width, height = 500, 380
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        container = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=20, border_width=1, border_color="#1e293b")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="CONFIRMAR DEVOLUCIÓN DE EQUIPO", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#10b981").pack(anchor="w", padx=25, pady=(20, 2))
        
        item_title = f"[{self.loan.get('code') or 'S/C'}] {self.loan.get('description') or 'Activo'}"
        ctk.CTkLabel(container, text=item_title[:45], font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#f8fafc").pack(anchor="w", padx=25, pady=(0, 15))

        ctk.CTkLabel(container, text="¿A qué salón desea trasladar el equipo devuelto?", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#94a3b8").pack(anchor="w", padx=25, pady=(10, 4))
                     
        self.dep_combo = ctk.CTkComboBox(container, values=self.dependencies, height=40, 
                                         corner_radius=10, fg_color="#020617", border_color="#1e293b",
                                         font=ctk.CTkFont(size=13))
        self.dep_combo.pack(fill="x", padx=25, pady=(0, 25))
        
        curr_dep = self.loan.get('dependency')
        if curr_dep and curr_dep in self.dependencies:
            self.dep_combo.set(curr_dep)
        elif self.dependencies:
            self.dep_combo.set(self.dependencies[0])

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", padx=25, pady=(5, 10))

        ctk.CTkButton(btn_frame, text="📦 DEVOLVER Y TRASLADAR", fg_color="#10b981", hover_color="#059669",
                      height=42, font=ctk.CTkFont(size=13, weight="bold"), corner_radius=10,
                      command=self.confirm_return).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(btn_frame, text="✖ CANCELAR", fg_color="transparent", hover_color="#1e293b",
                      height=42, font=ctk.CTkFont(size=13, weight="bold"), corner_radius=10,
                      border_width=1, border_color="#334155", text_color="#cbd5e1",
                      command=self.destroy).pack(side="right", fill="x", expand=True, padx=(8, 0))

    def confirm_return(self):
        new_dep = self.dep_combo.get()
        self.on_return(self.loan['id'], self.loan['asset_id'], new_dep)
        self.destroy()

    def destroy(self):
        try:
            self.grab_release()
        except Exception:
            pass
        super().destroy()

class ModernLoans(ctk.CTkFrame):
    def __init__(self, master, controller, loan_repo, asset_repo, official_repo):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.loan_repo = loan_repo
        self.asset_repo = asset_repo
        self.official_repo = official_repo
        self._asset_map = {}

        # Header Section
        self.header = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=20, border_width=1, border_color=theme.BORDER)
        self.header.pack(fill="x", padx=40, pady=(35, 15))
        ctk.CTkLabel(self.header, text="🤝 Módulo de Préstamos y Asignaciones", 
                     font=ctk.CTkFont(size=24, weight="bold"), text_color=theme.TEXT_MAIN).pack(pady=22, padx=30, side="left")

        self.btn_import = ctk.CTkButton(self.header, text="📥 Importar Préstamos (Excel)", height=38, corner_radius=10,
                                        fg_color="#107C41", hover_color="#185C37", font=ctk.CTkFont(size=13, weight="bold"),
                                        command=self.import_from_excel)
        self.btn_import.pack(side="right", padx=30, pady=22)


        # Form Section
        self.form_f = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=18, border_width=1, border_color=theme.BORDER)
        self.form_f.pack(fill="x", padx=40, pady=(0, 15))

        inner_f = ctk.CTkFrame(self.form_f, fg_color="transparent")
        inner_f.pack(padx=25, pady=20, fill="x")
        ctk.CTkLabel(inner_f, text="NUEVO PRÉSTAMO / ASIGNACIÓN DE EQUIPO", font=ctk.CTkFont(size=12, weight="bold"), 
                     text_color=theme.PRIMARY_LIGHT).pack(anchor="w", pady=(0, 12))

        # Row 1: Salón + Activo
        row1 = ctk.CTkFrame(inner_f, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 10))
        row1.columnconfigure(0, weight=1)
        row1.columnconfigure(1, weight=3)

        c1 = ctk.CTkFrame(row1, fg_color="transparent")
        c1.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(c1, text="SALÓN / DEPENDENCIA", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=theme.TEXT_FAINT).pack(anchor="w", padx=2, pady=(0, 5))
        self.dep_combo = ctk.CTkComboBox(c1, values=["Cargando..."], height=38, 
                                         fg_color=theme.BG_INPUT, border_color=theme.BORDER,
                                         command=self.on_dep_change)
        self.dep_combo.pack(fill="x")

        c2 = ctk.CTkFrame(row1, fg_color="transparent")
        c2.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        ctk.CTkLabel(c2, text="SERIAL DEL PORTÁTIL (BUSCAR)", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=theme.TEXT_FAINT).pack(anchor="w", padx=2, pady=(0, 5))
        self.asset_entry = ctk.CTkEntry(c2, placeholder_text="Escriba para buscar activo...",
                                        height=38, fg_color=theme.BG_INPUT, border_color=theme.BORDER)
        self.asset_entry.pack(fill="x")
        self.asset_entry.bind("<KeyRelease>", self.on_asset_key_release)
        self.available_assets = []

        # Row 2: Profesor + Celular
        row2 = ctk.CTkFrame(inner_f, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 10))
        row2.columnconfigure(0, weight=1)
        row2.columnconfigure(1, weight=1)

        c3 = ctk.CTkFrame(row2, fg_color="transparent")
        c3.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(c3, text="NOMBRE DEL PROFESOR / TUTOR", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=theme.TEXT_FAINT).pack(anchor="w", padx=2, pady=(0, 5))
        self.teacher_entry = ctk.CTkEntry(c3, placeholder_text="Nombre completo...",
                                          height=38, fg_color=theme.BG_INPUT, border_color=theme.BORDER)
        self.teacher_entry.pack(fill="x")
        self.teacher_entry.bind("<KeyRelease>", self.on_teacher_key_release)
        self.responsible_names = []

        c4 = ctk.CTkFrame(row2, fg_color="transparent")
        c4.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        ctk.CTkLabel(c4, text="CÉDULA DE CIUDADANÍA", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=theme.TEXT_FAINT).pack(anchor="w", padx=2, pady=(0, 5))
        self.phone_entry = ctk.CTkEntry(c4, placeholder_text="Número de cédula...",
                                        height=38, fg_color=theme.BG_INPUT, border_color=theme.BORDER)
        self.phone_entry.pack(fill="x")

        # Row 3: Metadata + Quantity + Action
        row3 = ctk.CTkFrame(inner_f, fg_color="transparent")
        row3.pack(fill="x", pady=(5, 0))

        ctk.CTkLabel(row3, text="FECHA DE ENTREGA / DEVOLUCIÓN:", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=theme.TEXT_MUTED).pack(side="left", padx=(0, 8))
        self.date_entry = ctk.CTkEntry(row3, width=130, height=36, fg_color=theme.BG_INPUT, border_color=theme.BORDER)
        self.date_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.date_entry.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(row3, text="CANTIDAD:", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=theme.TEXT_MUTED).pack(side="left", padx=(0, 8))
        self.qty_entry = ctk.CTkEntry(row3, width=70, height=36, fg_color=theme.BG_INPUT, border_color=theme.BORDER)
        self.qty_entry.insert(0, "1")
        self.qty_entry.pack(side="left", padx=(0, 20))

        ctk.CTkButton(row3, text="✔ REGISTRAR PRÉSTAMO", fg_color=theme.SUCCESS, hover_color="#059669",
                      height=38, width=210, font=ctk.CTkFont(size=12, weight="bold"),
                      command=self.create_loan).pack(side="right")

        # Table Container
        self.grid_container = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_container.pack(fill="both", expand=True, padx=40)

        # Tab View
        self.tabview = ctk.CTkTabview(self.grid_container, fg_color="transparent")
        self.tabview.pack(fill="both", expand=True, pady=(0, 15))
        
        self.tab_active = self.tabview.add("Préstamos Activos")
        self.tab_history = self.tabview.add("Historial de Devoluciones")
        
        # Setup tables
        self.setup_active_table()
        self.setup_history_table()

        self.refresh_list()

    def setup_active_table(self):
        # Column widths: FECHA, NOMBRE, CÉDULA, NOMBRE EQUIPO, MARCA, SERIAL, CANTIDAD, ACCIONES
        self._W0, self._W1, self._W2, self._W3, self._W4, self._W5, self._W6, self._W7 = 100, 160, 90, 120, 100, 110, 60, 140
        self._total_w = self._W0+self._W1+self._W2+self._W3+self._W4+self._W5+self._W6+self._W7 + 80

        self.table_outer = ctk.CTkFrame(self.tab_active, fg_color=theme.BG_CARD, corner_radius=15, 
                                        border_width=1, border_color=theme.BORDER)
        self.table_outer.pack(fill="both", expand=True, pady=5)

        self.h_sb = ctk.CTkScrollbar(self.table_outer, orientation="horizontal")
        self.h_sb.pack(side="bottom", fill="x", padx=2, pady=2)
        self.v_sb = ctk.CTkScrollbar(self.table_outer, orientation="vertical")
        self.v_sb.pack(side="right", fill="y", padx=2, pady=2)

        self.hdr_canvas = tk.Canvas(self.table_outer, bg=theme.BG_SIDEBAR, highlightthickness=0, height=44)
        self.hdr_canvas.pack(side="top", fill="x")
        self.hdr_frame = ctk.CTkFrame(self.hdr_canvas, fg_color=theme.BG_SIDEBAR, corner_radius=0, width=self._total_w)
        self.hdr_canvas.create_window((0, 0), window=self.hdr_frame, anchor="nw")

        cols = ["FECHA (DD/MM/AAAA)", "NOMBRE DEL PROFESOR / TUTOR", "CÉDULA DE CIUDADANÍA", "NOMBRE EQUIPO", "MARCA", "SERIAL DEL PORTÁTIL", "CANTIDAD", "ACCIONES"]
        ws = [self._W0, self._W1, self._W2, self._W3, self._W4, self._W5, self._W6, self._W7]
        for j, (txt, w) in enumerate(zip(cols, ws)):
            ctk.CTkLabel(self.hdr_frame, text=txt, font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=theme.TEXT_MUTED, width=w, anchor="w").grid(row=0, column=j, padx=8, pady=12)

        self.body_canvas = tk.Canvas(self.table_outer, bg=theme.BG_CARD, highlightthickness=0,
                                     yscrollcommand=self.v_sb.set, xscrollcommand=self.h_sb.set)
        self.body_canvas.pack(side="left", fill="both", expand=True)
        self.v_sb.configure(command=self.body_canvas.yview)

        def _h_scroll(*args):
            self.hdr_canvas.xview(*args)
            self.body_canvas.xview(*args)
        self.h_sb.configure(command=_h_scroll)
        self.body_canvas.configure(xscrollcommand=lambda *a: (self.h_sb.set(*a), self.hdr_canvas.xview_moveto(a[0])))

        self.body_f = ctk.CTkFrame(self.body_canvas, fg_color="transparent", width=self._total_w, corner_radius=0)
        self.body_canvas.create_window((0, 0), window=self.body_f, anchor="nw")

        def _resize_ev(e):
            fh = self.body_f.winfo_reqheight()
            self.body_canvas.configure(scrollregion=(0, 0, self._total_w, fh))
        self.body_f.bind("<Configure>", _resize_ev)
        enable_smooth_scroll(self.body_canvas, self.table_outer)

    def setup_history_table(self):
        self._h_W0, self._h_W1, self._h_W2, self._h_W3, self._h_W4, self._h_W5, self._h_W6, self._h_W7 = 100, 160, 90, 120, 100, 110, 60, 100
        self._h_total_w = self._h_W0+self._h_W1+self._h_W2+self._h_W3+self._h_W4+self._h_W5+self._h_W6+self._h_W7 + 80

        self.h_table_outer = ctk.CTkFrame(self.tab_history, fg_color=theme.BG_CARD, corner_radius=15, 
                                          border_width=1, border_color=theme.BORDER)
        self.h_table_outer.pack(fill="both", expand=True, pady=5)

        self.h_h_sb = ctk.CTkScrollbar(self.h_table_outer, orientation="horizontal")
        self.h_h_sb.pack(side="bottom", fill="x", padx=2, pady=2)
        self.h_v_sb = ctk.CTkScrollbar(self.h_table_outer, orientation="vertical")
        self.h_v_sb.pack(side="right", fill="y", padx=2, pady=2)

        self.h_hdr_canvas = tk.Canvas(self.h_table_outer, bg=theme.BG_SIDEBAR, highlightthickness=0, height=44)
        self.h_hdr_canvas.pack(side="top", fill="x")
        self.h_hdr_frame = ctk.CTkFrame(self.h_hdr_canvas, fg_color=theme.BG_SIDEBAR, corner_radius=0, width=self._h_total_w)
        self.h_hdr_canvas.create_window((0, 0), window=self.h_hdr_frame, anchor="nw")

        cols = ["FECHA (DD/MM/AAAA)", "NOMBRE DEL PROFESOR / TUTOR", "CÉDULA DE CIUDADANÍA", "NOMBRE EQUIPO", "MARCA", "SERIAL DEL PORTÁTIL", "CANTIDAD", "ESTADO"]
        ws = [self._h_W0, self._h_W1, self._h_W2, self._h_W3, self._h_W4, self._h_W5, self._h_W6, self._h_W7]
        for j, (txt, w) in enumerate(zip(cols, ws)):
            ctk.CTkLabel(self.h_hdr_frame, text=txt, font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=theme.TEXT_MUTED, width=w, anchor="w").grid(row=0, column=j, padx=8, pady=12)

        self.h_body_canvas = tk.Canvas(self.h_table_outer, bg=theme.BG_CARD, highlightthickness=0,
                                       yscrollcommand=self.h_v_sb.set, xscrollcommand=self.h_h_sb.set)
        self.h_body_canvas.pack(side="left", fill="both", expand=True)
        self.h_v_sb.configure(command=self.h_body_canvas.yview)

        def _h_h_scroll(*args):
            self.h_hdr_canvas.xview(*args)
            self.h_body_canvas.xview(*args)
        self.h_h_sb.configure(command=_h_h_scroll)
        self.h_body_canvas.configure(xscrollcommand=lambda *a: (self.h_h_sb.set(*a), self.h_hdr_canvas.xview_moveto(a[0])))

        self.h_body_f = ctk.CTkFrame(self.h_body_canvas, fg_color="transparent", width=self._h_total_w, corner_radius=0)
        self.h_body_canvas.create_window((0, 0), window=self.h_body_f, anchor="nw")

        def _h_resize_ev(e):
            fh = self.h_body_f.winfo_reqheight()
            self.h_body_canvas.configure(scrollregion=(0, 0, self._h_total_w, fh))
        self.h_body_f.bind("<Configure>", _h_resize_ev)
        enable_smooth_scroll(self.h_body_canvas, self.h_table_outer)

    def refresh_list(self):
        self.controller.run_in_thread(self._fetch_loans_data, self._render_loans_callback)

    def _fetch_loans_data(self):
        sede = getattr(self.controller, "global_sede", "Todas")
        active_assets = self.asset_repo.get_active_assets(sede=sede)
        active_loans = self.loan_repo.get_active_loans(sede=sede)
        returned_loans = self.loan_repo.get_returned_loans(sede=sede)
        resp_names = self.official_repo.get_all_responsible_names()
        
        dep_set = set()
        for a in active_assets:
            d = a.get('dependency')
            if d:
                dep_set.add(d)
        dependencies = sorted(list(dep_set))
        
        return active_assets, active_loans, returned_loans, resp_names, dependencies

    def _render_loans_callback(self, data):
        active, loans, returned, resp_names, dependencies = data
        self.responsible_names = resp_names
        self.available_assets = active
        self._asset_map = {}
        
        deps = [d for d in dependencies if d]
        if not deps: deps = ["SIN SALONES"]
        
        current_dep = self.dep_combo.get()
        self.dep_combo.configure(values=deps)
        if current_dep in deps:
            self.dep_combo.set(current_dep)
        else:
            self.dep_combo.set(deps[0])
            self.on_dep_change(deps[0])
        
        for a in active: 
            key = f"[{a.get('code') or 'S/C'}] {(a.get('description') or 'Sin descripción')[:40]}"
            self._asset_map[key] = a['id']

        for w in self.body_f.winfo_children(): w.destroy()
        if not loans:
            ctk.CTkLabel(self.body_f, text="No hay equipos prestados en este momento.", text_color="#64748b").pack(pady=40)
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            for i, l in enumerate(loans):
                raw_due = str(l.get('expected_return_date') or '')
                iso_due = normalize_date_input(raw_due)
                disp_due = format_date_display(raw_due)
                is_overdue = iso_due < today

                row_bg = "#0f172a" if i % 2 == 0 else "#020617"
                row = ctk.CTkFrame(self.body_f, fg_color=row_bg, corner_radius=0)
                row.pack(fill="x")
                
                # FECHA
                ctk.CTkLabel(row, text=disp_due, width=self._W0,
                             text_color="#ef4444" if is_overdue else "#10b981", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=8, pady=10)
                
                # NOMBRE
                ctk.CTkLabel(row, text=l.get('teacher_name') or '—', font=ctk.CTkFont(size=12, weight="bold"),
                             width=self._W1, anchor="w", text_color="#f8fafc").grid(row=0, column=1, padx=8)
                
                # CÉDULA
                ctk.CTkLabel(row, text=l.get('teacher_phone') or '—', width=self._W2, anchor="w",
                             text_color="#93c5fd").grid(row=0, column=2, padx=8)
                
                # NOMBRE EQUIPO
                ctk.CTkLabel(row, text=(l.get('description') or 'S/C')[:20], width=self._W3, anchor="w",
                             text_color="#cbd5e1").grid(row=0, column=3, padx=8)

                # MARCA
                ctk.CTkLabel(row, text=(l.get('brand') or '—')[:15], width=self._W4, anchor="w",
                             text_color="#60a5fa").grid(row=0, column=4, padx=8)

                # SERIAL
                ctk.CTkLabel(row, text=(l.get('code') or '—'), width=self._W5, anchor="w",
                             text_color="#94a3b8").grid(row=0, column=5, padx=8)
                
                # CANTIDAD
                ctk.CTkLabel(row, text=str(l.get('loan_qty', 1)), width=self._W6, text_color="#94a3b8").grid(row=0, column=6, padx=8)
                
                # ACCIONES
                act_f = ctk.CTkFrame(row, fg_color="transparent", width=self._W7)
                act_f.grid(row=0, column=7, padx=6, pady=4)
                
                ctk.CTkButton(act_f, text="✔ Devolver", width=75, height=28, fg_color="#10b981", hover_color="#059669",
                              font=ctk.CTkFont(size=11, weight="bold"),
                              command=lambda item=l: self.mark_returned(item)).pack(side="left", padx=2)


                ctk.CTkButton(act_f, text="✏️ Editar", width=68, height=28, fg_color="#3b82f6", hover_color="#2563eb",
                              font=ctk.CTkFont(size=11, weight="bold"),
                              command=lambda item=l: self.open_edit_dialog(item)).pack(side="left", padx=2)

        for w in self.h_body_f.winfo_children(): w.destroy()
        if not returned:
            ctk.CTkLabel(self.h_body_f, text="No hay registros históricos de devoluciones.", text_color="#64748b").pack(pady=40)
        else:
            for i, l in enumerate(returned):
                disp_due = format_date_display(l.get('expected_return_date') or '')
                row_bg = "#0f172a" if i % 2 == 0 else "#020617"
                row = ctk.CTkFrame(self.h_body_f, fg_color=row_bg, corner_radius=0)
                row.pack(fill="x")
                
                ctk.CTkLabel(row, text=disp_due, width=self._h_W0, text_color="#10b981", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=8, pady=10)
                ctk.CTkLabel(row, text=l.get('teacher_name') or '—', font=ctk.CTkFont(size=12, weight="bold"),
                             width=self._h_W1, anchor="w", text_color="#f8fafc").grid(row=0, column=1, padx=8)
                ctk.CTkLabel(row, text=l.get('teacher_phone') or '—', width=self._h_W2, anchor="w",
                             text_color="#93c5fd").grid(row=0, column=2, padx=8)
                ctk.CTkLabel(row, text=(l.get('description') or 'S/C')[:20], width=self._h_W3, anchor="w",
                             text_color="#cbd5e1").grid(row=0, column=3, padx=8)
                ctk.CTkLabel(row, text=(l.get('brand') or '—')[:15], width=self._h_W4, anchor="w",
                             text_color="#60a5fa").grid(row=0, column=4, padx=8)
                ctk.CTkLabel(row, text=(l.get('code') or '—'), width=self._h_W5, anchor="w",
                             text_color="#94a3b8").grid(row=0, column=5, padx=8)
                ctk.CTkLabel(row, text=str(l.get('loan_qty', 1)), width=self._h_W6, text_color="#94a3b8").grid(row=0, column=6, padx=8)
                ctk.CTkLabel(row, text="✅ DEVUELTO", width=self._h_W7, text_color="#10b981", font=ctk.CTkFont(weight="bold")).grid(row=0, column=7, padx=8)

    def create_loan(self):
        from tkinter import messagebox
        asset_text = self.asset_entry.get().strip()
        asset_id = self._asset_map.get(asset_text)
        teacher = self.teacher_entry.get().strip()
        phone = self.phone_entry.get().strip()
        date_ret_raw = self.date_entry.get().strip()
        qty = self.qty_entry.get().strip()
        
        if not asset_id or not teacher:
            messagebox.showwarning("Campos Requeridos", "Debe seleccionar un activo y asignar el nombre del profesor.")
            return
            
        try:
            qty_val = int(qty)
            if qty_val <= 0:
                raise ValueError()
        except:
            messagebox.showwarning("Cantidad Inválida", "La cantidad debe ser un número entero mayor a 0.")
            return
            
        iso_date = normalize_date_input(date_ret_raw)
        try:
            datetime.strptime(iso_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Fecha Inválida", "La fecha de devolución debe tener un formato válido (DD/MM/AAAA o AAAA-MM-DD).")
            return
            
        available_qty = self.loan_repo.get_asset_available_quantity(asset_id)
        if qty_val > available_qty:
            messagebox.showwarning("Sin Existencias Disponibles", f"No se puede realizar el préstamo. El activo seleccionado tiene {available_qty} unidades físicas disponibles para prestar.")
            return
            
        start_date = datetime.now().strftime("%Y-%m-%d")
        success = self.loan_repo.create_loan(asset_id, qty_val, teacher, start_date, iso_date, teacher_phone=phone)
        if success:
            self.teacher_entry.delete(0, "end")
            self.phone_entry.delete(0, "end")
            self.qty_entry.delete(0, "end")
            self.qty_entry.insert(0, "1")
            self.refresh_list()
            if hasattr(self.controller, 'invalidate_all_pages'):
                self.controller.invalidate_all_pages()
            messagebox.showinfo("Éxito", "Préstamo registrado y guardado correctamente.")
        else:
            messagebox.showerror("Error", "No se pudo registrar el préstamo. Intente nuevamente.")

    def open_edit_dialog(self, loan_item):
        EditLoanDialog(self, loan_item, self._save_edited_loan)

    def _save_edited_loan(self, loan_id, teacher_name, teacher_phone, expected_return, qty):
        from tkinter import messagebox
        success = self.loan_repo.update_loan(loan_id, teacher_name, teacher_phone, expected_return, qty)
        if success:
            self.refresh_list()
            if hasattr(self.controller, 'invalidate_all_pages'):
                self.controller.invalidate_all_pages()
            messagebox.showinfo("Éxito", "Préstamo actualizado y guardado correctamente.")
        else:
            messagebox.showerror("Error", "No se pudieron guardar los cambios del préstamo.")

    def mark_returned(self, loan_item):
        deps = self.dep_combo.cget('values')
        if not deps or deps == ["SIN SALONES"]:
            deps = ["SIN ASIGNAR"]
        ReturnLoanDialog(self, loan_item, deps, self._save_returned_loan)

    def _save_returned_loan(self, loan_id, asset_id, new_dependency):
        from tkinter import messagebox
        try:
            # Transfer first
            transfer_ok = self.asset_repo.transfer_asset(asset_id, new_dependency)
            # Then return the loan
            return_ok = self.loan_repo.return_loan(loan_id)
            
            if not transfer_ok or not return_ok:
                messagebox.showwarning("Advertencia", "Hubo un problema interno al devolver el préstamo. Revisa la base de datos.")
            else:
                messagebox.showinfo("Éxito", f"El equipo ha sido marcado como devuelto y trasladado a {new_dependency}.")
                
            self.refresh_list()
            if hasattr(self.controller, 'invalidate_all_pages'):
                self.controller.invalidate_all_pages()
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al procesar la devolución: {str(e)}")

    def on_teacher_key_release(self, event):
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return
            
        val = self.teacher_entry.get().strip().upper()
        if not val:
            self.close_autocomplete()
            return
            
        matches = [name for name in self.responsible_names if val in name.upper()]
        if not matches:
            self.close_autocomplete()
            return
            
        self.show_autocomplete_popup(matches)

    def show_autocomplete_popup(self, matches):
        if hasattr(self, "ac_popup") and self.ac_popup.winfo_exists():
            self.ac_listbox.delete(0, "end")
            for m in matches[:10]:
                self.ac_listbox.insert("end", m)
            return
            
        x = self.teacher_entry.winfo_rootx()
        y = self.teacher_entry.winfo_rooty() + self.teacher_entry.winfo_height()
        w = self.teacher_entry.winfo_width()
        
        self.ac_popup = tk.Toplevel(self)
        self.ac_popup.wm_overrideredirect(True)
        self.ac_popup.geometry(f"{w}x180+{x}+{y}")
        self.ac_popup.configure(bg="#1e293b")
        
        self.ac_listbox = tk.Listbox(
            self.ac_popup, bg="#0f172a", fg="#f8fafc", 
            selectbackground="#3b82f6", selectforeground="white",
            font=("Arial", 11), bd=1, relief="flat", highlightthickness=0
        )
        self.ac_listbox.pack(fill="both", expand=True, padx=1, pady=1)
        
        for m in matches[:10]:
            self.ac_listbox.insert("end", m)
            
        self.ac_listbox.bind("<Double-Button-1>", self.on_select_suggestion)
        self.ac_listbox.bind("<Return>", self.on_select_suggestion)
        self.teacher_entry.bind("<Down>", self.focus_listbox)
        self.ac_listbox.bind("<Escape>", lambda e: self.close_autocomplete())
        self.ac_popup.bind("<FocusOut>", lambda e: self.after(100, self.check_focus_out))

    def focus_listbox(self, event):
        if hasattr(self, "ac_listbox") and self.ac_listbox.winfo_exists():
            self.ac_listbox.focus_set()
            self.ac_listbox.selection_set(0)
            
    def on_select_suggestion(self, event=None):
        if hasattr(self, "ac_listbox") and self.ac_listbox.winfo_exists():
            sel = self.ac_listbox.curselection()
            if sel:
                name = self.ac_listbox.get(sel[0])
                self.teacher_entry.delete(0, "end")
                self.teacher_entry.insert(0, name)
            self.close_autocomplete()
            
    def close_autocomplete(self):
        if hasattr(self, "ac_popup"):
            try:
                self.ac_popup.destroy()
            except Exception:
                pass
            delattr(self, "ac_popup")
            
    def check_focus_out(self):
        if hasattr(self, "ac_popup"):
            focus = self.focus_get()
            if focus not in (self.teacher_entry, self.ac_listbox):
                self.close_autocomplete()

    def on_dep_change(self, value):
        self.asset_entry.delete(0, "end")
        self.close_asset_autocomplete()

    def on_asset_key_release(self, event):
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return
            
        val = self.asset_entry.get().strip().upper()
        if not val:
            self.close_asset_autocomplete()
            return
            
        dep = self.dep_combo.get()
        matches = []
        for a in getattr(self, 'available_assets', []):
            a_dep = a.get('dependency') or "SIN SALONES"
            if a_dep != dep and dep != "SIN SALONES":
                continue
            
            code = (a.get('code') or '').upper()
            desc = (a.get('description') or '').upper()
            serial = (a.get('serial_number') or '').upper()
            
            if val in code or val in desc or val in serial:
                key = f"[{a.get('code') or 'S/C'}] {(a.get('description') or 'Sin descripción')[:40]}"
                matches.append(key)
                
        if not matches:
            self.close_asset_autocomplete()
            return
            
        self.show_asset_autocomplete_popup(matches)

    def show_asset_autocomplete_popup(self, matches):
        if hasattr(self, "asset_popup") and self.asset_popup.winfo_exists():
            self.asset_listbox.delete(0, "end")
            for m in matches[:15]:
                self.asset_listbox.insert("end", m)
            return
            
        x = self.asset_entry.winfo_rootx()
        y = self.asset_entry.winfo_rooty() + self.asset_entry.winfo_height()
        w = self.asset_entry.winfo_width()
        
        self.asset_popup = tk.Toplevel(self)
        self.asset_popup.wm_overrideredirect(True)
        self.asset_popup.geometry(f"{w}x200+{x}+{y}")
        self.asset_popup.configure(bg="#1e293b")
        
        self.asset_listbox = tk.Listbox(
            self.asset_popup, bg="#0f172a", fg="#f8fafc", 
            selectbackground="#10b981", selectforeground="white",
            font=("Arial", 11), bd=1, relief="flat", highlightthickness=0
        )
        self.asset_listbox.pack(fill="both", expand=True, padx=1, pady=1)
        
        for m in matches[:15]:
            self.asset_listbox.insert("end", m)
            
        self.asset_listbox.bind("<Double-Button-1>", self.on_select_asset_suggestion)
        self.asset_listbox.bind("<Return>", self.on_select_asset_suggestion)
        self.asset_entry.bind("<Down>", self.focus_asset_listbox)
        self.asset_listbox.bind("<Escape>", lambda e: self.close_asset_autocomplete())
        self.asset_popup.bind("<FocusOut>", lambda e: self.after(100, self.check_asset_focus_out))

    def focus_asset_listbox(self, event):
        if hasattr(self, "asset_listbox") and self.asset_listbox.winfo_exists():
            self.asset_listbox.focus_set()
            self.asset_listbox.selection_set(0)
            
    def on_select_asset_suggestion(self, event=None):
        if hasattr(self, "asset_listbox") and self.asset_listbox.winfo_exists():
            sel = self.asset_listbox.curselection()
            if sel:
                name = self.asset_listbox.get(sel[0])
                self.asset_entry.delete(0, "end")
                self.asset_entry.insert(0, name)
            self.close_asset_autocomplete()
            
    def close_asset_autocomplete(self):
        if hasattr(self, "asset_popup"):
            try:
                self.asset_popup.destroy()
            except Exception:
                pass
            delattr(self, "asset_popup")
            
    def check_asset_focus_out(self):
        if hasattr(self, "asset_popup"):
            focus = self.focus_get()
            if focus not in (self.asset_entry, self.asset_listbox):
                self.close_asset_autocomplete()

    def import_from_excel(self):
        import tkinter.filedialog as fd
        filepath = fd.askopenfilename(
            title="Seleccionar archivo Excel de Préstamos",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")]
        )
        if not filepath:
            return
        
        from tkinter import messagebox
        if not messagebox.askyesno("Confirmar Importación", "¿Está seguro que desea importar préstamos desde este archivo?\n\nLos equipos que no existan se crearán automáticamente en la sede y salón 'SIN ASIGNAR'."):
            return
            
        self.controller.run_in_thread(self._run_import_loans_excel, self._on_import_loans_done, filepath)

    def _run_import_loans_excel(self, filepath):
        import openpyxl
        from utils import strip_accents
        from datetime import datetime
        
        try:
            wb = openpyxl.load_workbook(filepath, data_only=True)
            sheet = wb.active
            
            NORM_KEYWORDS = {
                "code": ["CODIGO", "PLACA", "ACTIVO", "ID", "SERIAL"],
                "desc": ["DESCRIPCION", "ARTICULO", "EQUIPO", "ELEMENTO"],
                "teacher": ["PROFESOR", "DOCENTE", "TUTOR", "RESPONSABLE", "NOMBRE"],
                "phone": ["CELULAR", "TELEFONO", "CONTACTO", "MOVIL", "CEDULA"],
                "date": ["FECHA", "ENTREGA", "DEVOLUCION"],
                "qty": ["CANTIDAD", "CANT", "UNIDADES"],
                "brand": ["MARCA", "FABRICANTE"]
            }
            
            mapping = {}
            header_row_idx = 1
            for row_idx, row in enumerate(sheet.iter_rows(min_row=1, max_row=20, values_only=True), 1):
                norm = [strip_accents(str(c).upper()) if c is not None else "" for c in row]
                used = set()
                tmp = {}
                for key, kws in NORM_KEYWORDS.items():
                    for idx, cell in enumerate(norm):
                        if not cell or idx in used: continue
                        if any(kw in cell for kw in kws):
                            tmp[key] = idx
                            used.add(idx)
                            break
                if "code" in tmp and "teacher" in tmp:
                    mapping = tmp
                    header_row_idx = row_idx
                    break
                    
            if not mapping or "code" not in mapping:
                return (False, "No se detectaron columnas válidas (mínimo: Código, Profesor) en el archivo Excel.\nVerifique los encabezados.")
                
            def gx(key, default=""):
                idx = mapping.get(key)
                if idx is not None and idx < len(row) and row[idx] is not None:
                    return str(row[idx]).strip()
                return default

            def clean_num(val):
                try: return float(str(val).replace('$','').replace(',','').replace(' ',''))
                except: return 0.0

            added_loans = 0
            added_assets = 0
            now = datetime.now().strftime("%d/%m/%Y")
            now_iso = datetime.now().strftime("%Y-%m-%d")
            current_sede = getattr(self.controller, "global_sede", "Guaimaral")
            
            for row in sheet.iter_rows(min_row=header_row_idx + 1, values_only=True):
                if not any(row): continue
                
                v_code = gx("code")
                if not v_code: continue
                
                v_desc = gx("desc", "PORTÁTIL")
                v_teacher = gx("teacher", "Desconocido")
                v_phone = gx("phone", "")
                v_date = gx("date", now)
                v_qty = max(1, int(clean_num(gx("qty", 1))))
                v_brand = gx("brand", "N/A")
                
                asset_id = None
                self.asset_repo.db_manager.cursor.execute("SELECT id FROM assets WHERE CODIGO = ?", (v_code,))
                res = self.asset_repo.db_manager.cursor.fetchone()
                if res:
                    asset_id = res[0]
                else:
                    new_asset = (
                        v_code, "101", "SIN ASIGNAR", v_desc, v_brand, "N/A", "N/A",
                        "N/A", "N/A", "Creado desde importación de préstamos",
                        0.0, 1, 0.0, 0.0, 0.0, now, now, 10, "BUENO",
                        "IMPORTACIÓN", "EN SERVICIO", "SIN ASIGNAR", 0, None, None,
                        "", "", "", "", "", "", "", current_sede
                    )
                    self.asset_repo.bulk_add_assets([new_asset])
                    added_assets += 1
                    self.asset_repo.db_manager.cursor.execute("SELECT id FROM assets WHERE CODIGO = ?", (v_code,))
                    res2 = self.asset_repo.db_manager.cursor.fetchone()
                    if res2:
                        asset_id = res2[0]
                
                if asset_id:
                    self.loan_repo.create_loan(asset_id, v_qty, v_teacher, now_iso, normalize_date_input(v_date), v_phone)
                    added_loans += 1
            
            return (True, f"Importación completada con éxito.\n\nPréstamos registrados: {added_loans}\nNuevos equipos creados en salón 'SIN ASIGNAR': {added_assets}")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return (False, f"Error al procesar el archivo:\n{str(e)}")

    def _on_import_loans_done(self, result):
        from tkinter import messagebox
        success, msg = result
        if success:
            messagebox.showinfo("Importación Exitosa", msg)
            self.refresh_list()
        else:
            messagebox.showerror("Error", msg)




class OverdueLoansDialog(ctk.CTkToplevel):
    def __init__(self, parent, overdue_loans):
        super().__init__(parent)
        self.parent = parent
        self.overdue_loans = overdue_loans
        
        self.title("🚨 ALERTA: PRÉSTAMOS VENCIDOS")
        self.geometry("750x500")
        self.configure(fg_color="#0a0f1d")
        
        self.grab_set()
        self.focus()
        self.transient(parent)
        
        self.update_idletasks()
        width = 750
        height = 500
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        container = ctk.CTkFrame(self, fg_color="#180c0c", corner_radius=20, border_width=2, border_color="#ef4444")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        header_f = ctk.CTkFrame(container, fg_color="#ef4444", height=70, corner_radius=10)
        header_f.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(header_f, text="⚠️ ALERTA DE VENCIMIENTO PATRIMONIAL", font=ctk.CTkFont(size=18, weight="bold"), text_color="white").pack(pady=10)
        ctk.CTkLabel(container, text="Se han detectado los siguientes préstamos vencidos en el sistema:", font=ctk.CTkFont(size=13), text_color="#f87171").pack(anchor="w", padx=25, pady=(0, 10))
        
        scroll = ctk.CTkScrollableFrame(container, fg_color="#090505", corner_radius=15, border_width=1, border_color="#450a0a")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        hdr = ctk.CTkFrame(scroll, fg_color="#270a0a", corner_radius=5)
        hdr.pack(fill="x", pady=2)
        ctk.CTkLabel(hdr, text="RESPONSABLE", font=ctk.CTkFont(size=10, weight="bold"), text_color="#fca5a5", width=160, anchor="w", padx=10).pack(side="left")
        ctk.CTkLabel(hdr, text="ACTIVO", font=ctk.CTkFont(size=10, weight="bold"), text_color="#fca5a5", width=220, anchor="w").pack(side="left")
        ctk.CTkLabel(hdr, text="CANT.", font=ctk.CTkFont(size=10, weight="bold"), text_color="#fca5a5", width=50).pack(side="left")
        ctk.CTkLabel(hdr, text="FECHA LÍMITE", font=ctk.CTkFont(size=10, weight="bold"), text_color="#fca5a5", width=110).pack(side="left")
        ctk.CTkLabel(hdr, text="DÍAS ATRASO", font=ctk.CTkFont(size=10, weight="bold"), text_color="#fca5a5", width=90).pack(side="left")
        
        today = datetime.now().strftime("%Y-%m-%d")
        for i, l in enumerate(overdue_loans):
            bg = "#180909" if i % 2 == 0 else "#090505"
            row = ctk.CTkFrame(scroll, fg_color=bg, corner_radius=5)
            row.pack(fill="x", pady=2)
            
            try:
                d1 = datetime.strptime(today, "%Y-%m-%d")
                d2 = datetime.strptime(normalize_date_input(l['expected_return_date']), "%Y-%m-%d")
                days_overdue = (d1 - d2).days
                days_str = f"{days_overdue} días" if days_overdue > 0 else "Hoy"
            except Exception:
                days_str = "Vencido"
                
            ctk.CTkLabel(row, text=l.get('teacher_name', '—')[:22], font=ctk.CTkFont(size=11, weight="bold"), text_color="white", width=160, anchor="w", padx=10).pack(side="left")
            ctk.CTkLabel(row, text=f"[{l.get('code', '—')}] {l.get('description', '—')}"[:32], font=ctk.CTkFont(size=11), text_color="#fca5a5", width=220, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=str(l.get('loan_qty', 1)), font=ctk.CTkFont(size=11), text_color="white", width=50).pack(side="left")
            disp_date = format_date_display(l.get('expected_return_date', '—'))
            ctk.CTkLabel(row, text=disp_date, font=ctk.CTkFont(size=11, weight="bold"), text_color="#ef4444", width=110).pack(side="left")
            ctk.CTkLabel(row, text=days_str, font=ctk.CTkFont(size=11, weight="bold"), text_color="#ef4444", width=90).pack(side="left")
            
        ctk.CTkButton(container, text="ENTENDIDO", font=ctk.CTkFont(size=13, weight="bold"), height=45,
                      fg_color="#ef4444", hover_color="#dc2626", text_color="white", corner_radius=10, command=self.destroy).pack(pady=(0, 20), padx=25, fill="x")

    def destroy(self):
        try:
            self.grab_release()
        except Exception:
            pass
        super().destroy()
