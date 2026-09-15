import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from theme import theme
from scroll_helper import enable_smooth_scroll
try:
    from components.inventory import EditAssetDialog, TransferAssetDialog, DisposeAssetDialog
except (ImportError, ModuleNotFoundError):
    from inventory import EditAssetDialog, TransferAssetDialog, DisposeAssetDialog  # type: ignore

class ModernDependencies(ctk.CTkFrame):
    def __init__(self, master, controller, dep_repo, asset_repo, setting_repo):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.dep_repo = dep_repo
        self.asset_repo = asset_repo
        self.setting_repo = setting_repo
        self.selected_dep = None
        self.current_page = 1
        self.items_per_page = 50
        self.render_main_grid()

    def render_main_grid(self):
        self.selected_dep = None
        for w in self.winfo_children(): w.destroy()
        
        # --- Header ---
        self.header = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=18, border_width=1, border_color=theme.BORDER)
        self.header.pack(fill="x", padx=40, pady=(35, 15))
        h_content = ctk.CTkFrame(self.header, fg_color="transparent")
        h_content.pack(padx=30, pady=20, fill="x")
        
        title_f = ctk.CTkFrame(h_content, fg_color="transparent")
        title_f.pack(side="left")
        
        tag_f = ctk.CTkFrame(title_f, fg_color=theme.BG_SIDEBAR, border_width=1, border_color=theme.BORDER, corner_radius=6)
        tag_f.pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(tag_f, text="● CONTROL DE UNIDADES FÍSICAS", font=ctk.CTkFont(size=9, weight="bold"), text_color=theme.PRIMARY_LIGHT).pack(padx=10, pady=2)
        
        ctk.CTkLabel(title_f, text="Salones y Dependencias", font=ctk.CTkFont(size=28, weight="bold"), text_color=theme.TEXT_MAIN).pack(anchor="w")

        # Quick Add Bar
        add_f = ctk.CTkFrame(h_content, fg_color=theme.BG_SIDEBAR, corner_radius=10, border_width=1, border_color=theme.BORDER)
        add_f.pack(side="right")
        self.dep_name_entry = ctk.CTkEntry(add_f, placeholder_text="Nombre del salón...", height=36, width=190, corner_radius=8, 
                                           fg_color=theme.BG_INPUT, border_color=theme.BORDER, text_color=theme.TEXT_MAIN, font=ctk.CTkFont(size=12))
        self.dep_name_entry.pack(side="left", padx=8, pady=6)
        ctk.CTkButton(add_f, text="＋ Crear Salón", width=115, height=36, corner_radius=8, 
                      fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER, font=ctk.CTkFont(size=12, weight="bold"), text_color="white",
                      command=self.add_dep).pack(side="left", padx=(0, 8))

        # --- Grid with Scrollable Container ---
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=30, pady=(0, 10))
        
        self.grid_container = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.grid_container.pack(fill="both", expand=True)
        self.grid_container.grid_columnconfigure((0,1,2), weight=1)

        self.refresh_grid()

    def add_dep(self):
        name = self.dep_name_entry.get().strip().upper()
        if name:
            sede = getattr(self.controller, "global_sede", "Guaimaral")
            if not sede or sede == "Todas":
                sede = "Guaimaral"
            if self.dep_repo.add_dependency(name, "AULA", sede=sede):
                self.dep_name_entry.delete(0, 'end')
                self.refresh_grid()

    def confirm_delete_dependency(self, dep_name, total_items=0):
        sede = getattr(self.controller, "global_sede", "Todas")
        sede_display = f"la sede '{sede}'" if sede and sede != "Todas" else "todas las sedes"
        if total_items > 0:
            msg = f"¿Está seguro de que desea eliminar el salón '{dep_name}' de {sede_display}?\n\n⚠️ ADVERTENCIA: Este salón registra {total_items} activos físicos.\nSi continúa, el salón se eliminará y sus activos pasarán al estado 'SIN ASIGNAR'."
        else:
            msg = f"¿Está seguro de que desea eliminar el salón '{dep_name}' de {sede_display}?\n\nEsta acción no se puede deshacer."
            
        if messagebox.askyesno("Confirmar Eliminación de Salón", msg):
            success = self.dep_repo.delete_dependency(dep_name, sede)
            if success:
                messagebox.showinfo("Salón Eliminado", f"El salón '{dep_name}' ha sido eliminado exitosamente.")
                self.controller.invalidate_all_pages()
                self.render_main_grid()
            else:
                messagebox.showerror("Error", f"No se pudo eliminar el salón '{dep_name}'.")

    def refresh_data(self):
        if getattr(self, "selected_dep", None):
            self.refresh_dep_detail()
        else:
            self.refresh_grid()

    def refresh_grid(self):
        self.controller.run_in_thread(self._fetch_dep_data, self._render_dep_grid_callback)

    def _fetch_dep_data(self):
        sede = getattr(self.controller, "global_sede", "Todas")
        all_stats = self.asset_repo.get_all_dep_stats(sede=sede)
        breakdown = self.asset_repo.get_dep_states_breakdown(sede=sede)
        raw_deps = self.dep_repo.get_dependencies(sede=sede)
        deps_names = [d for d in raw_deps if str(d).strip().upper() not in ('SIN ASIGNAR', 'GENERAL', 'SIN DEPENDENCIAS', 'NONE', 'NULL', '')]
        deps_data = []
        gv, gu = 0.0, 0
        for d in deps_names:
            rows, units, init_val, real_val = all_stats.get(d.upper(), (0, 0, 0.0, 0.0))
            states = breakdown.get(d.upper(), {"BUENO": 0, "REGULAR": 0, "MALO": 0})
            deps_data.append((d, rows, units, init_val, real_val, states))
            gv += init_val
            gu += units
            
        import re
        deps_data.sort(key=lambda x: [int(c) if c.isdigit() else c.lower() for c in re.split('([0-9]+)', x[0])])
        return deps_data, gv, gu, sede

    def _render_dep_grid_callback(self, results):
        deps_data, gv, gu, *rest = results
        sede = rest[0] if rest else getattr(self.controller, "global_sede", "Todas")
        for w in self.grid_container.winfo_children(): w.destroy()

        if not deps_data:
            empty_card = ctk.CTkFrame(self.grid_container, fg_color=theme.BG_CARD, corner_radius=14, border_width=1, border_color=theme.BORDER)
            empty_card.grid(row=0, column=0, columnspan=3, padx=20, pady=40, sticky="nsew")
            ctk.CTkLabel(empty_card, text="🏢", font=ctk.CTkFont(size=40)).pack(pady=(30, 8))
            sede_txt = f" en la sede '{sede}'" if sede != "Todas" else ""
            ctk.CTkLabel(empty_card, text=f"No hay dependencias registradas{sede_txt}", font=ctk.CTkFont(size=16, weight="bold"), text_color=theme.TEXT_MAIN).pack(pady=4)
            ctk.CTkLabel(empty_card, text="Escriba el nombre en el campo superior y presione '＋ Crear Salón' para añadir una dependencia.", font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED).pack(pady=(0, 30))

        for i, (dep, r, u, init_v, real_v, states) in enumerate(deps_data):
            card = ctk.CTkFrame(self.grid_container, fg_color=theme.BG_CARD, corner_radius=14, border_width=1, border_color=theme.BORDER)
            card.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="nsew")
            
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=20, pady=18)
            
            # 1. Card Header: Title + Unit Count Chip
            hdr_f = ctk.CTkFrame(inner, fg_color="transparent")
            hdr_f.pack(fill="x", pady=(0, 10))
            
            ctk.CTkLabel(hdr_f, text=dep.upper(), font=ctk.CTkFont(size=14, weight="bold"), text_color=theme.TEXT_MAIN, anchor="w").pack(side="left")
            
            unit_chip = ctk.CTkFrame(hdr_f, fg_color=theme.BG_SIDEBAR, corner_radius=6, border_width=1, border_color=theme.BORDER)
            unit_chip.pack(side="right")
            ctk.CTkLabel(unit_chip, text=f"{u} uds", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED).pack(padx=8, pady=3)
            
            # Subtle divider
            ctk.CTkFrame(inner, fg_color=theme.BORDER, height=1).pack(fill="x", pady=(0, 12))
            
            # 2. Executive Metrics (2 columns: Valor Compra vs Valor Neto)
            metrics_f = ctk.CTkFrame(inner, fg_color="transparent")
            metrics_f.pack(fill="x", pady=(0, 12))
            metrics_f.columnconfigure(0, weight=1)
            metrics_f.columnconfigure(1, weight=1)
            
            m1 = ctk.CTkFrame(metrics_f, fg_color="transparent")
            m1.grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(m1, text="VALOR HISTÓRICO", font=ctk.CTkFont(size=9, weight="bold"), text_color=theme.TEXT_FAINT).pack(anchor="w")
            ctk.CTkLabel(m1, text=f"${init_v:,.0f}", font=ctk.CTkFont(size=13, weight="bold"), text_color=theme.TEXT_MAIN).pack(anchor="w", pady=(1, 0))
            
            m2 = ctk.CTkFrame(metrics_f, fg_color="transparent")
            m2.grid(row=0, column=1, sticky="w")
            ctk.CTkLabel(m2, text="VALOR EN LIBROS", font=ctk.CTkFont(size=9, weight="bold"), text_color=theme.TEXT_FAINT).pack(anchor="w")
            ctk.CTkLabel(m2, text=f"${real_v:,.0f}", font=ctk.CTkFont(size=13, weight="bold"), text_color=theme.SUCCESS if real_v > 0 else theme.TEXT_MUTED).pack(anchor="w", pady=(1, 0))

            # 3. Clean Executive Status Indicator (No toy blocks)
            b_cnt = states.get("BUENO", 0)
            r_cnt = states.get("REGULAR", 0)
            m_cnt = states.get("MALO", 0)
            
            status_bar = ctk.CTkFrame(inner, fg_color=theme.BG_SIDEBAR, corner_radius=8, border_width=1, border_color=theme.BORDER, height=28)
            status_bar.pack(fill="x", pady=(0, 14))
            status_bar.pack_propagate(False)
            
            sb_inner = ctk.CTkFrame(status_bar, fg_color="transparent")
            sb_inner.pack(expand=True)
            
            ctk.CTkLabel(sb_inner, text="●", font=ctk.CTkFont(size=9), text_color=theme.SUCCESS).pack(side="left", padx=(0, 2))
            ctk.CTkLabel(sb_inner, text=f"{b_cnt} Bueno", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED).pack(side="left", padx=(0, 10))
            
            ctk.CTkLabel(sb_inner, text="●", font=ctk.CTkFont(size=9), text_color=theme.WARNING).pack(side="left", padx=(0, 2))
            ctk.CTkLabel(sb_inner, text=f"{r_cnt} Reg.", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED).pack(side="left", padx=(0, 10))
            
            ctk.CTkLabel(sb_inner, text="●", font=ctk.CTkFont(size=9), text_color=theme.DANGER).pack(side="left", padx=(0, 2))
            ctk.CTkLabel(sb_inner, text=f"{m_cnt} Malo", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED).pack(side="left")
            
            # 4. Sleek Button Row (Gestionar + Eliminar)
            btn_row = ctk.CTkFrame(inner, fg_color="transparent")
            btn_row.pack(fill="x")

            btn = ctk.CTkButton(
                btn_row, 
                text="Gestionar Salón  →", 
                fg_color=theme.BG_SIDEBAR, 
                hover_color=theme.PRIMARY_HOVER, 
                height=34, 
                corner_radius=8, 
                border_width=1, 
                border_color=theme.BORDER,
                text_color=theme.TEXT_MAIN, 
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda d=dep: self.view_dep_detail(d)
            )
            btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

            del_btn = ctk.CTkButton(
                btn_row,
                text="🗑️",
                width=34,
                height=34,
                corner_radius=8,
                fg_color="#1e1e2d",
                hover_color="#7f1d1d",
                border_width=1,
                border_color=theme.BORDER,
                text_color="#f87171",
                font=ctk.CTkFont(size=12),
                command=lambda d=dep, cnt=r: self.confirm_delete_dependency(d, cnt)
            )
            del_btn.pack(side="right")

        # Grand Total Summary Bar
        grand_card = ctk.CTkFrame(self.grid_container, fg_color=theme.BG_CARD, corner_radius=14, border_width=1, border_color=theme.BORDER)
        grand_card.grid(row=(len(deps_data)) // 3 + 1, column=0, columnspan=3, padx=10, pady=(10, 25), sticky="ew")
        
        gc_inner = ctk.CTkFrame(grand_card, fg_color="transparent")
        gc_inner.pack(fill="x", padx=30, pady=16)
        gc_inner.columnconfigure((0, 1, 2), weight=1)
        
        # Stat 1
        s1 = ctk.CTkFrame(gc_inner, fg_color="transparent")
        s1.grid(row=0, column=0)
        ctk.CTkLabel(s1, text="TOTAL SALONES / DEPENDENCIAS", font=ctk.CTkFont(size=9, weight="bold"), text_color=theme.TEXT_FAINT).pack()
        ctk.CTkLabel(s1, text=f"{len(deps_data)} Unidades", font=ctk.CTkFont(size=16, weight="bold"), text_color=theme.TEXT_MAIN).pack(pady=(2, 0))
        
        # Stat 2
        s2 = ctk.CTkFrame(gc_inner, fg_color="transparent")
        s2.grid(row=0, column=1)
        ctk.CTkLabel(s2, text="ACTIVOS FÍSICOS REGISTRADOS", font=ctk.CTkFont(size=9, weight="bold"), text_color=theme.TEXT_FAINT).pack()
        ctk.CTkLabel(s2, text=f"{gu:,} Unidades", font=ctk.CTkFont(size=16, weight="bold"), text_color=theme.PRIMARY_LIGHT).pack(pady=(2, 0))
        
        # Stat 3
        s3 = ctk.CTkFrame(gc_inner, fg_color="transparent")
        s3.grid(row=0, column=2)
        ctk.CTkLabel(s3, text="PATRIMONIO TOTAL ASIGNADO", font=ctk.CTkFont(size=9, weight="bold"), text_color=theme.TEXT_FAINT).pack()
        ctk.CTkLabel(s3, text=f"${gv:,.0f} COP", font=ctk.CTkFont(size=16, weight="bold"), text_color=theme.SUCCESS).pack(pady=(2, 0))

    def view_dep_detail(self, dep_name):
        self.selected_dep = dep_name
        self.current_page = 1
        self.dep_search_query = ""
        self.dep_state_filter = "Todos los Estados"
        for w in self.winfo_children(): w.destroy()

        # Retrieve room stats
        sede = getattr(self.controller, "global_sede", "Todas")
        all_raw = self.asset_repo.get_assets_by_dependency(dep_name, sede=sede)
        total_items = len(all_raw)
        total_units = sum(int(a.get('quantity') or a.get('EXISTENCIAINICIAL') or 1) for a in all_raw)
        total_acq = sum(float(a.get('initial_unit_value') or a.get('VALOR') or 0.0) * int(a.get('quantity') or a.get('EXISTENCIAINICIAL') or 1) for a in all_raw)
        total_net = sum(float(a.get('current_value') or 0.0) for a in all_raw)
        total_depr = total_acq - total_net

        # --- DETAIL HEADER ---
        dh = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=14, border_width=1, border_color=theme.BORDER)
        dh.pack(fill="x", padx=30, pady=(15, 8))

        inner_dh = ctk.CTkFrame(dh, fg_color="transparent")
        inner_dh.pack(padx=20, pady=12, fill="x")

        # Left: Back button + Title & Room stats
        left_f = ctk.CTkFrame(inner_dh, fg_color="transparent")
        left_f.pack(side="left")

        top_row = ctk.CTkFrame(left_f, fg_color="transparent")
        top_row.pack(anchor="w")

        ctk.CTkButton(top_row, text="← Volver", width=90, height=30, corner_radius=7,
                      fg_color=theme.BG_SIDEBAR, border_width=1, border_color=theme.BORDER,
                      text_color=theme.TEXT_MAIN, hover_color=theme.PRIMARY_HOVER,
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=self.render_main_grid).pack(side="left", padx=(0, 12))

        tag_f = ctk.CTkFrame(top_row, fg_color=theme.BG_SIDEBAR, corner_radius=6, border_width=1, border_color=theme.BORDER)
        tag_f.pack(side="left")
        ctk.CTkLabel(tag_f, text="● EXPEDIENTE DE SALÓN", font=ctk.CTkFont(size=9, weight="bold"), text_color=theme.PRIMARY_LIGHT).pack(padx=8, pady=2)

        ctk.CTkLabel(left_f, text=dep_name.upper(), font=ctk.CTkFont(size=22, weight="bold"), text_color=theme.TEXT_MAIN).pack(anchor="w", pady=(2, 4))

        # Room KPI chips
        chips_f = ctk.CTkFrame(left_f, fg_color="transparent")
        chips_f.pack(anchor="w")

        for label_t, val_t, color_t in [
            ("Activos:", f"{total_items} ({total_units} uds)", theme.TEXT_MAIN),
            ("Inversión Histórica:", f"${total_acq:,.0f} COP", theme.PRIMARY_LIGHT),
            ("Depreciación:", f"${total_depr:,.0f} COP", theme.DANGER if total_depr > 0 else theme.TEXT_MUTED),
            ("Valor en Libros:", f"${total_net:,.0f} COP", theme.SUCCESS if total_net > 0 else theme.TEXT_MUTED)
        ]:
            chip = ctk.CTkFrame(chips_f, fg_color=theme.BG_SIDEBAR, corner_radius=6, border_width=1, border_color=theme.BORDER)
            chip.pack(side="left", padx=(0, 8))
            ctk.CTkLabel(chip, text=f"{label_t} {val_t}", font=ctk.CTkFont(size=10, weight="bold"), text_color=color_t).pack(padx=8, pady=2)

        # Right: Action buttons
        act_f = ctk.CTkFrame(inner_dh, fg_color="transparent")
        act_f.pack(side="right")

        ctk.CTkButton(act_f, text="➕ Añadir Artículo", height=32, corner_radius=7,
                      fg_color=theme.SUCCESS, hover_color="#059669",
                      font=ctk.CTkFont(size=11, weight="bold"), text_color="white",
                      command=lambda: self.go_to_registry_for_dep(dep_name)).pack(side="left", padx=3)

        ctk.CTkButton(act_f, text="📊 Consolidado", height=32, corner_radius=7,
                      fg_color=theme.BG_SIDEBAR, border_width=1, border_color=theme.BORDER,
                      hover_color=theme.PRIMARY_HOVER, font=ctk.CTkFont(size=11, weight="bold"),
                      text_color=theme.TEXT_MAIN, command=lambda: self.show_asset_summary(dep_name)).pack(side="left", padx=3)

        ctk.CTkButton(act_f, text="📉 Bitácora Bajas", height=32, corner_radius=7,
                      fg_color=theme.BG_SIDEBAR, border_width=1, border_color=theme.BORDER,
                      hover_color="#3d1414", font=ctk.CTkFont(size=11, weight="bold"),
                      text_color=theme.DANGER, command=lambda: self.show_dep_disposals(dep_name)).pack(side="left", padx=3)

        ctk.CTkButton(act_f, text="📄 Descargar PDF", height=32, corner_radius=7,
                      fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
                      font=ctk.CTkFont(size=11, weight="bold"), text_color="white",
                      command=lambda: self.export_dep_pdf(dep_name)).pack(side="left", padx=3)

        ctk.CTkButton(act_f, text="🗑️ Eliminar Salón", height=32, corner_radius=7,
                      fg_color="#450a0a", border_width=1, border_color="#7f1d1d",
                      hover_color="#991b1b", font=ctk.CTkFont(size=11, weight="bold"),
                      text_color="#fca5a5",
                      command=lambda: self.confirm_delete_dependency(dep_name, total_items)).pack(side="left", padx=3)

        # --- Filter & Search Bar in Room ---
        bar_f = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=10, border_width=1, border_color=theme.BORDER)
        bar_f.pack(fill="x", padx=30, pady=(0, 6))

        bar_inner = ctk.CTkFrame(bar_f, fg_color="transparent")
        bar_inner.pack(fill="x", padx=14, pady=8)

        ctk.CTkLabel(bar_inner, text="🔍", font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 6))

        self.dep_search_entry = ctk.CTkEntry(
            bar_inner,
            placeholder_text="Buscar por código, descripción, marca o serial en este salón...",
            height=32,
            corner_radius=7,
            fg_color=theme.BG_INPUT,
            border_color=theme.BORDER,
            text_color=theme.TEXT_MAIN,
            font=ctk.CTkFont(size=11)
        )
        self.dep_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.dep_search_entry.bind("<KeyRelease>", lambda e: self._on_dep_search())

        self.dep_state_combo = ctk.CTkComboBox(
            bar_inner,
            values=["Todos los Estados", "Bueno", "Regular", "Malo"],
            height=32,
            width=150,
            corner_radius=7,
            fg_color=theme.BG_INPUT,
            border_color=theme.BORDER,
            command=lambda v: self._on_dep_state_filter(v)
        )
        self.dep_state_combo.pack(side="left")

        # --- Pagination Control Bar ---
        pag_f = ctk.CTkFrame(self, fg_color="transparent")
        pag_f.pack(fill="x", padx=30, pady=(0, 6))

        self.prev_btn = ctk.CTkButton(
            pag_f, text="◀ Anterior", width=95, height=30, corner_radius=7,
            fg_color=theme.BG_CARD, hover_color=theme.PRIMARY_HOVER, border_width=1, border_color=theme.BORDER,
            text_color=theme.TEXT_MAIN, font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self.change_page(-1)
        )
        self.prev_btn.pack(side="left")

        self.page_label = ctk.CTkLabel(pag_f, text="Página 1", font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.TEXT_MUTED)
        self.page_label.pack(side="left", expand=True)

        self.next_btn = ctk.CTkButton(
            pag_f, text="Siguiente ▶", width=95, height=30, corner_radius=7,
            fg_color=theme.BG_CARD, hover_color=theme.PRIMARY_HOVER, border_width=1, border_color=theme.BORDER,
            text_color=theme.TEXT_MAIN, font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self.change_page(1)
        )
        self.next_btn.pack(side="right")

        # --- Table Container (Scrollable 2D: Horizontal + Vertical) ---
        self.table_frame = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=12, border_width=1, border_color=theme.BORDER)
        self.table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 14))

        self.canvas = tk.Canvas(self.table_frame, bg=theme.BG_CARD, highlightthickness=0)
        self.h_scroll = ctk.CTkScrollbar(self.table_frame, orientation="horizontal", height=14, command=self.canvas.xview)
        self.v_scroll = ctk.CTkScrollbar(self.table_frame, orientation="vertical", width=14, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)

        self.v_scroll.pack(side="right", fill="y", padx=(2, 4), pady=(4, 4))
        self.h_scroll.pack(side="bottom", fill="x", padx=(4, 4), pady=(2, 4))
        self.canvas.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=(4, 0))

        self.table_content = ctk.CTkFrame(self.canvas, fg_color=theme.BG_CARD, corner_radius=0)
        self.canvas_win = self.canvas.create_window((0, 0), window=self.table_content, anchor="nw")

        def _update_scrollregion(event=None):
            bbox = self.canvas.bbox("all")
            if bbox:
                canv_w = self.canvas.winfo_width()
                canv_h = self.canvas.winfo_height()
                w = max(bbox[2], canv_w)
                h = max(bbox[3], canv_h)
                self.canvas.configure(scrollregion=(0, 0, w, h))

        def _on_canvas_configure(event):
            req_w = self.table_content.winfo_reqwidth()
            target_w = max(event.width, req_w)
            self.canvas.itemconfig(self.canvas_win, width=target_w)
            _update_scrollregion()

        self.table_content.bind("<Configure>", _update_scrollregion)
        self.canvas.bind("<Configure>", _on_canvas_configure)

        # Multi-axis mousewheel scrolling (Universal & SOLID)
        enable_smooth_scroll(self.canvas, self.table_frame)

        self.render_paginated_grid()

    def _on_dep_search(self):
        self.dep_search_query = self.dep_search_entry.get().strip().lower()
        self.current_page = 1
        self.render_paginated_grid()

    def _on_dep_state_filter(self, val):
        self.dep_state_filter = val
        self.current_page = 1
        self.render_paginated_grid()

    def change_page(self, delta):
        self.current_page += delta
        self.render_paginated_grid()

    def render_paginated_grid(self):
        sede = getattr(self.controller, "global_sede", "Todas")
        all_raw = self.asset_repo.get_assets_by_dependency(self.selected_dep, sede=sede)
        
        # Apply local search and state filtering
        filtered = []
        for a in all_raw:
            a_dict = dict(a)
            # Text query check
            if self.dep_search_query:
                code_s = str(a_dict.get('code') or a_dict.get('CODIGO') or '').lower()
                desc_s = str(a_dict.get('description') or a_dict.get('DESCRIPCION') or '').lower()
                brand_s = str(a_dict.get('brand') or a_dict.get('MARCA') or '').lower()
                serial_s = str(a_dict.get('serial') or a_dict.get('SERIAL') or '').lower()
                resp_s = str(a_dict.get('responsible') or a_dict.get('FUNCIONARIO') or '').lower()
                if not (self.dep_search_query in code_s or self.dep_search_query in desc_s or 
                        self.dep_search_query in brand_s or self.dep_search_query in serial_s or
                        self.dep_search_query in resp_s):
                    continue
            # State filter check
            if self.dep_state_filter and self.dep_state_filter != "Todos los Estados":
                st_s = str(a_dict.get('conservation_state') or a_dict.get('ESTADOCONSERVACION') or 'BUENO').upper()
                if self.dep_state_filter.upper() not in st_s:
                    continue
            filtered.append(a_dict)

        total_count = len(filtered)
        max_p = max(1, (total_count - 1) // self.items_per_page + 1)
        self.current_page = max(1, min(self.current_page, max_p))

        self.page_label.configure(text=f"Página {self.current_page} de {max_p} ({total_count} Activos)")
        self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < max_p else "disabled")

        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_assets = filtered[start_idx:end_idx]

        for w in self.table_content.winfo_children(): w.destroy()

        if not page_assets:
            ctk.CTkLabel(
                self.table_content,
                text="No se encontraron activos registrados en este salón.",
                font=ctk.CTkFont(size=13),
                text_color=theme.TEXT_MUTED
            ).pack(pady=50)
            return

        # Executive Table Headers
        headers = [
            ("CÓDIGO", 130),
            ("DESCRIPCIÓN DEL ACTIVO", 350),
            ("ESTADO", 100),
            ("CANT.", 60),
            ("VAL. COMPRA", 125),
            ("DEPRECIACIÓN", 125),
            ("VAL. LIBROS", 125),
            ("MARCA", 120),
            ("SERIAL", 120),
            ("RESPONSABLE", 160),
            ("ACCIONES", 240)
        ]

        h_row = ctk.CTkFrame(self.table_content, fg_color=theme.BG_SIDEBAR, height=42, corner_radius=0)
        h_row.pack(fill="x")

        for j, (txt, w) in enumerate(headers):
            ctk.CTkLabel(
                h_row,
                text=txt,
                width=w,
                height=42,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=theme.TEXT_MUTED,
                anchor="w",
                padx=10
            ).grid(row=0, column=j, sticky="w")

        # Table Rows
        for i, a in enumerate(page_assets):
            code_v = str(a.get('code') or a.get('CODIGO') or '—')
            desc_v = str(a.get('description') or a.get('DESCRIPCION') or '—')
            qty_v = str(a.get('quantity') or a.get('EXISTENCIAINICIAL') or 1)
            init_v = float(a.get('initial_unit_value') or a.get('VALOR') or 0.0)
            cur_v = float(a.get('current_value') or 0.0)
            depr_v = float(a.get('DEPRECIACUMULADA') or a.get('depreciation_rate') or max(0.0, init_v * int(qty_v) - cur_v))
            brand_v = str(a.get('brand') or a.get('MARCA') or '—')
            serial_v = str(a.get('serial') or a.get('SERIAL') or '—')
            resp_v = str(a.get('responsible') or a.get('FUNCIONARIO') or '—')
            st_raw = str(a.get('conservation_state') or a.get('ESTADOCONSERVACION') or 'BUENO').upper()

            # State badge setup
            if "MAL" in st_raw:
                st_color = theme.DANGER
                st_txt = "● Malo"
            elif "REG" in st_raw:
                st_color = theme.WARNING
                st_txt = "● Regular"
            else:
                st_color = theme.SUCCESS
                st_txt = "● Bueno"

            row_bg = theme.BG_CARD if i % 2 == 0 else theme.BG_APP
            r_row = ctk.CTkFrame(self.table_content, fg_color=row_bg, height=48, corner_radius=0)
            r_row.pack(fill="x")

            # 0: Code
            ctk.CTkLabel(r_row, text=code_v, width=130, height=48, anchor="w", padx=10,
                         font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_MAIN).grid(row=0, column=0, sticky="w")

            # 1: Description
            ctk.CTkLabel(r_row, text=desc_v[:55], width=350, height=48, anchor="w", padx=10,
                         font=ctk.CTkFont(size=11), text_color=theme.TEXT_MAIN).grid(row=0, column=1, sticky="w")

            # 2: State Badge
            st_cell = ctk.CTkFrame(r_row, fg_color="transparent", width=100, height=48)
            st_cell.grid(row=0, column=2, sticky="w", padx=10)
            st_cell.pack_propagate(False)
            badge = ctk.CTkFrame(st_cell, fg_color=theme.BG_SIDEBAR, corner_radius=6, border_width=1, border_color=theme.BORDER)
            badge.pack(side="left", pady=10)
            ctk.CTkLabel(badge, text=st_txt, font=ctk.CTkFont(size=10, weight="bold"), text_color=st_color).pack(padx=8, pady=3)

            # 3: Quantity
            ctk.CTkLabel(r_row, text=qty_v, width=60, height=48, anchor="w", padx=10,
                         font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).grid(row=0, column=3, sticky="w")

            # 4: Purchase Value
            ctk.CTkLabel(r_row, text=f"${init_v:,.0f}", width=125, height=48, anchor="w", padx=10,
                         font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_MAIN).grid(row=0, column=4, sticky="w")

            # 5: Depreciation
            ctk.CTkLabel(r_row, text=f"${depr_v:,.0f}", width=125, height=48, anchor="w", padx=10,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=theme.DANGER if depr_v > 0 else theme.TEXT_MUTED).grid(row=0, column=5, sticky="w")

            # 6: Net Value
            ctk.CTkLabel(r_row, text=f"${cur_v:,.0f}", width=125, height=48, anchor="w", padx=10,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=theme.SUCCESS if cur_v > 0 else theme.TEXT_MUTED).grid(row=0, column=6, sticky="w")

            # 7: Brand
            ctk.CTkLabel(r_row, text=brand_v[:18], width=120, height=48, anchor="w", padx=10,
                         font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).grid(row=0, column=7, sticky="w")

            # 8: Serial
            ctk.CTkLabel(r_row, text=serial_v[:18], width=120, height=48, anchor="w", padx=10,
                         font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).grid(row=0, column=8, sticky="w")

            # 9: Responsible
            ctk.CTkLabel(r_row, text=resp_v[:24], width=160, height=48, anchor="w", padx=10,
                         font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).grid(row=0, column=9, sticky="w")

            # 10: Actions Frame
            actions_frame = ctk.CTkFrame(r_row, fg_color="transparent", width=240, height=48)
            actions_frame.grid(row=0, column=10, sticky="w", padx=10)
            actions_frame.pack_propagate(False)

            ctk.CTkButton(
                actions_frame, text="Editar", width=68, height=28, corner_radius=6,
                fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
                font=ctk.CTkFont(size=11, weight="bold"), text_color="white",
                command=lambda asset=a: self.open_edit(asset)
            ).pack(side="left", padx=3, pady=10)

            ctk.CTkButton(
                actions_frame, text="Traslado", width=68, height=28, corner_radius=6,
                fg_color=theme.WARNING, hover_color="#d97706",
                font=ctk.CTkFont(size=11, weight="bold"), text_color="white",
                command=lambda asset=a: self.open_transfer(asset)
            ).pack(side="left", padx=3, pady=10)

            ctk.CTkButton(
                actions_frame, text="Baja", width=68, height=28, corner_radius=6,
                fg_color=theme.DANGER, hover_color="#dc2626",
                font=ctk.CTkFont(size=11, weight="bold"), text_color="white",
                command=lambda asset=a: self.open_dispose(asset)
            ).pack(side="left", padx=3, pady=10)

        self.table_content.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def open_edit(self, asset):
        def on_success():
            self.view_dep_detail(self.selected_dep)
            self.controller.invalidate_all_pages()
        EditAssetDialog(self, asset, on_success)

    def open_transfer(self, asset):
        def on_success():
            self.view_dep_detail(self.selected_dep)
            self.controller.invalidate_all_pages()
        TransferAssetDialog(self, asset, on_success)

    def open_dispose(self, asset):
        def on_success():
            self.view_dep_detail(self.selected_dep)
            self.controller.invalidate_all_pages()
        DisposeAssetDialog(self, asset, on_success)

    def export_dep_pdf(self, dep_name):
        from tkinter import filedialog, messagebox
        from datetime import datetime

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"Inventario_{dep_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
            title="Guardar Inventario de Salón en PDF"
        )
        if not path: return

        sede = getattr(self.controller, "global_sede", "Todas")
        assets = self.asset_repo.get_assets_by_dependency(dep_name, sede=sede)
        if not assets:
            messagebox.showinfo("Exportar PDF", "No hay activos asignados a este salón para exportar.")
            return

        def _do_pdf():
            from fpdf import FPDF

            class InventoryPDF(FPDF):
                def header(self):
                    self.set_font('Arial', 'B', 15)
                    self.cell(0, 10, 'INSTITUCION EDUCATIVA GUAIMARAL', ln=True, align='C')
                    self.set_font('Arial', '', 10)
                    self.cell(0, 6, 'SISTEMA DE CONTROL DE INVENTARIO INSTITUCIONAL', ln=True, align='C')
                    self.set_font('Arial', 'B', 11)
                    self.cell(0, 8, f'ACTA DE INVENTARIO Y CONTROL FISICO - {dep_name.upper()}', ln=True, align='C')
                    self.ln(5)

                def footer(self):
                    self.set_y(-15)
                    self.set_font('Arial', 'I', 8)
                    self.cell(0, 10, f'Pagina {self.page_no()}/{{nb}}', align='C')

            pdf = InventoryPDF()
            pdf.alias_nb_pages()
            pdf.add_page()
            pdf.set_font('Arial', '', 10)

            today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            total_qty = sum(int(a.get('quantity') or a.get('EXISTENCIAINICIAL') or 1) for a in assets)
            total_val = sum(float(a.get('initial_unit_value') or a.get('VALOR') or 0.0) * int(a.get('quantity') or a.get('EXISTENCIAINICIAL') or 1) for a in assets)

            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 6, f" AREA / SALON:  {dep_name.upper()}", ln=True, fill=True)
            pdf.cell(0, 6, f" FECHA REPORTE: {today_str}", ln=True)
            pdf.cell(0, 6, f" TOTAL ACTIVOS: {len(assets)} items ({total_qty} unidades fisicas)", ln=True)
            pdf.cell(0, 6, f" VALOR TOTAL ADQUISICION: ${total_val:,.0f} COP", ln=True)
            pdf.ln(8)

            # Table Header
            pdf.set_fill_color(30, 41, 59)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('Arial', 'B', 9)

            widths = [25, 80, 25, 25, 15, 20]
            headers = ["CODIGO", "DESCRIPCION", "MARCA", "SERIAL", "CANT", "ESTADO"]

            for w, h in zip(widths, headers):
                pdf.cell(w, 8, h, 1, 0, 'C', True)
            pdf.ln()

            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Arial', '', 8)

            for a in assets:
                a_dict = dict(a)
                c_code = str(a_dict.get('code') or a_dict.get('CODIGO') or '—')[:12]
                c_desc = str(a_dict.get('description') or a_dict.get('DESCRIPCION') or '—')[:40]
                c_brand = str(a_dict.get('brand') or a_dict.get('MARCA') or '—')[:12]
                c_serial = str(a_dict.get('serial') or a_dict.get('SERIAL') or '—')[:12]
                c_qty = str(a_dict.get('quantity') or a_dict.get('EXISTENCIAINICIAL') or 1)
                c_state = str(a_dict.get('conservation_state') or a_dict.get('ESTADOCONSERVACION') or 'BUENO')[:10]

                pdf.cell(widths[0], 7, c_code, 1)
                pdf.cell(widths[1], 7, c_desc, 1)
                pdf.cell(widths[2], 7, c_brand, 1)
                pdf.cell(widths[3], 7, c_serial, 1)
                pdf.cell(widths[4], 7, c_qty, 1, 0, 'C')
                pdf.cell(widths[5], 7, c_state, 1, 0, 'C')
                pdf.ln()

            # Signatures
            pdf.ln(15)
            y_sig = pdf.get_y()
            if y_sig > 230:
                pdf.add_page()
                y_sig = 40

            pdf.line(15, y_sig, 85, y_sig)
            pdf.line(115, y_sig, 185, y_sig)

            pdf.set_xy(15, y_sig + 1)
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(70, 5, "RESPONSABLE DE AREA / SALON", ln=True)
            pdf.set_font('Arial', '', 8)
            pdf.text(15, y_sig + 9, "Nombre:")
            pdf.text(15, y_sig + 13, "C.C.:")
            pdf.text(15, y_sig + 17, "Cargo:")

            pdf.set_font('Arial', 'B', 9)
            pdf.text(115, y_sig + 5, "ENTREGA CONFORME")
            pdf.set_font('Arial', '', 8)
            pdf.text(115, y_sig + 9, "Nombre:")
            pdf.text(115, y_sig + 13, "C.C.:")
            pdf.text(115, y_sig + 17, "Cargo:")

            pdf.output(path)
            return path

        def _done(p):
            messagebox.showinfo("Exito", f"Reporte PDF generado correctamente en:\n{p}")

        self.controller.run_in_thread(_do_pdf, _done)

    def open_edit(self, asset):
        def on_success():
            self.render_paginated_grid()
            self.controller.invalidate_all_pages()
        EditAssetDialog(self, asset, on_success)

    def open_transfer(self, asset):
        def on_success():
            self.render_paginated_grid()
            self.controller.invalidate_all_pages()
        TransferAssetDialog(self, asset, on_success)

    def open_dispose(self, asset):
        def on_success():
            self.render_paginated_grid()
            self.controller.invalidate_all_pages()
        DisposeAssetDialog(self, asset, on_success)

    def show_asset_summary(self, dep):
        AssetSummaryDialog(self, dep)

    def show_dep_disposals(self, dep):
        DepDisposalsDialog(self, dep)

    def go_to_registry_for_dep(self, dep_name):
        def on_success():
            self.render_paginated_grid()
            self.controller.invalidate_all_pages()
        QuickAddAssetDialog(self, dep_name, on_success)


class QuickAddAssetDialog(ctk.CTkToplevel):
    def __init__(self, parent, dep_name, on_success):
        super().__init__(parent)
        self.parent = parent
        self.dep_name = dep_name
        self.on_success = on_success
        
        self.title(f"AÑADIR ACTIVO A: {dep_name}")
        self.geometry("500x550")
        self.configure(fg_color=theme.BG_APP)
        self.grab_set()
        self.focus()
        self.transient(parent)
        
        container = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=15, border_width=1, border_color=theme.BORDER)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(container, text=f"Registrar Nuevo Activo", font=ctk.CTkFont(size=20, weight="bold"), text_color=theme.TEXT_MAIN).pack(pady=(20, 5))
        ctk.CTkLabel(container, text=f"Se asignará automáticamente a: {dep_name}", font=ctk.CTkFont(size=11), text_color=theme.PRIMARY).pack(pady=(0, 20))
        
        self.entries = {}
        fields = [
            ("Código", "code"),
            ("Descripción", "desc"),
            ("Marca", "brand"),
            ("Serial", "serial"),
            ("Valor Unitario", "val"),
            ("Cantidad", "qty")
        ]
        
        for label, key in fields:
            f = ctk.CTkFrame(container, fg_color="transparent")
            f.pack(fill="x", padx=30, pady=5)
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_FAINT, width=100, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(f, height=35, corner_radius=8, fg_color=theme.BG_INPUT, border_color=theme.BORDER)
            entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
            self.entries[key] = entry
            
        btn_f = ctk.CTkFrame(container, fg_color="transparent")
        btn_f.pack(fill="x", padx=30, pady=25)
        
        ctk.CTkButton(btn_f, text="Guardar", font=ctk.CTkFont(weight="bold"), height=40, fg_color=theme.SUCCESS, hover_color="#059669", corner_radius=8, command=self.save).pack(side="right", fill="x", expand=True, padx=(5, 0))
        ctk.CTkButton(btn_f, text="Cancelar", font=ctk.CTkFont(weight="bold"), height=40, fg_color=theme.BG_SIDEBAR, border_color=theme.BORDER, border_width=1, hover_color=theme.DANGER, corner_radius=8, command=self.destroy).pack(side="left", padx=(0, 5))
        
    def save(self):
        from tkinter import messagebox
        from datetime import datetime
        code = self.entries["code"].get().strip() or "NX-SYS"
        desc = self.entries["desc"].get().strip()
        brand = self.entries["brand"].get().strip() or "N/A"
        serial = self.entries["serial"].get().strip() or "N/A"
        
        if not desc:
            messagebox.showwarning("Error", "La descripción es obligatoria.")
            return
            
        try: qty = int(self.entries["qty"].get().strip() or "1")
        except: qty = 1
        
        try: val = float(self.entries["val"].get().strip() or "0.0")
        except: val = 0.0
        
        data = (
            code, "101", "General", desc, brand, "N/A", serial, "N/A", "N/A", "N/A",
            val, qty, val*qty, 0.0, val*qty,
            datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%Y-%m-%d"), 10,
            "Bueno", "Propio", "En Uso", self.dep_name,
            "", "", "", "", "", "", "", "Guaimaral"
        )
        if self.parent.asset_repo.add_asset(data):
            self.on_success()
            messagebox.showinfo("Éxito", "Activo registrado correctamente en el salón.")
            self.destroy()
        else:
            messagebox.showerror("Error", "No se pudo guardar el activo.")

class DepDisposalsDialog(ctk.CTkToplevel):
    def __init__(self, parent, dep_name):
        super().__init__(parent)
        self.parent = parent
        self.dep_name = dep_name
        
        self.title(f"HISTORIAL DE BAJAS: {dep_name}")
        self.geometry("700x500")
        self.configure(fg_color=theme.BG_APP)
        
        self.grab_set()
        self.focus()
        self.transient(parent)
        
        container = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=20, border_width=1, border_color=theme.BORDER)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(container, text="HISTORIAL DE BAJAS Y DESINCORPORACIONES", font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.DANGER).pack(anchor="w", padx=25, pady=(20, 2))
        ctk.CTkLabel(container, text=f"{dep_name}", font=ctk.CTkFont(size=24, weight="bold"), text_color=theme.TEXT_MAIN).pack(anchor="w", padx=25, pady=(0, 15))
        
        # List Container
        self.scroll = ctk.CTkScrollableFrame(container, fg_color=theme.BG_INPUT, corner_radius=15, border_width=1, border_color=theme.BORDER)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        sede = getattr(self.parent.controller, "global_sede", "Todas")
        bajas = self.parent.asset_repo.get_disposed_assets_by_dependency(dep_name, sede=sede)
        if not bajas:
            ctk.CTkLabel(self.scroll, text="No hay registros de bajas para esta dependencia.", text_color=theme.TEXT_MUTED, font=ctk.CTkFont(size=13)).pack(pady=40)
        else:
            # Table Headers
            hdr = ctk.CTkFrame(self.scroll, fg_color=theme.BORDER, corner_radius=5)
            hdr.pack(fill="x", pady=2)
            ctk.CTkLabel(hdr, text="CÓDIGO", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED, width=100, anchor="w", padx=10).pack(side="left")
            ctk.CTkLabel(hdr, text="DESCRIPCIÓN", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED, width=250, anchor="w").pack(side="left")
            ctk.CTkLabel(hdr, text="CANT", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED, width=50).pack(side="left")
            ctk.CTkLabel(hdr, text="FECHA BAJA", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED, width=100).pack(side="left")
            ctk.CTkLabel(hdr, text="MOTIVO", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED, width=120, anchor="w").pack(side="left")
            
            for i, b in enumerate(bajas):
                b_dict = dict(b)
                bg = theme.BG_CARD if i % 2 == 0 else theme.BG_INPUT
                row = ctk.CTkFrame(self.scroll, fg_color=bg, corner_radius=5)
                row.pack(fill="x", pady=2)
                
                ctk.CTkLabel(row, text=b_dict.get('code', '—'), font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_MAIN, width=100, anchor="w", padx=10).pack(side="left")
                ctk.CTkLabel(row, text=b_dict.get('description', '—')[:30], font=ctk.CTkFont(size=11), text_color=theme.TEXT_MAIN, width=250, anchor="w").pack(side="left")
                ctk.CTkLabel(row, text=str(b_dict.get('quantity', 1)), font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED, width=50).pack(side="left")
                ctk.CTkLabel(row, text=b_dict.get('disposal_date', '—'), font=ctk.CTkFont(size=11), text_color=theme.DANGER, width=100).pack(side="left")
                ctk.CTkLabel(row, text=b_dict.get('disposal_reason', '—')[:20], font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED, width=120, anchor="w").pack(side="left")


class AssetSummaryDialog(ctk.CTkToplevel):
    def __init__(self, parent, dep_name):
        super().__init__(parent)
        self.parent = parent
        self.dep_name = dep_name
        
        self.title(f"CONSOLIDADO PATRIMONIAL: {dep_name}")
        self.geometry("800x600")
        self.configure(fg_color=theme.BG_APP)
        
        self.grab_set()
        self.focus()
        self.transient(parent)
        
        container = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=20, border_width=1, border_color=theme.BORDER)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(container, text="CONSOLIDADO DE ACTIVOS POR SALÓN", font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.SUCCESS).pack(anchor="w", padx=25, pady=(20, 2))
        ctk.CTkLabel(container, text=f"{dep_name}", font=ctk.CTkFont(size=24, weight="bold"), text_color=theme.TEXT_MAIN).pack(anchor="w", padx=25, pady=(0, 15))
        
        self.scroll = ctk.CTkScrollableFrame(container, fg_color=theme.BG_INPUT, corner_radius=15, border_width=1, border_color=theme.BORDER)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        sede = getattr(self.parent.controller, "global_sede", "Todas")
        summary = self.parent.asset_repo.get_asset_summary_stats(dep_name, sede=sede)
        
        # 1. Categories Breakdown
        ctk.CTkLabel(self.scroll, text="Resumen de Rubros Contables", font=ctk.CTkFont(size=13, weight="bold"), text_color=theme.PRIMARY, anchor="w").pack(fill="x", padx=10, pady=(10, 5))
        
        cat_frame = ctk.CTkFrame(self.scroll, fg_color=theme.BG_CARD, corner_radius=10, border_width=1, border_color=theme.BORDER)
        cat_frame.pack(fill="x", padx=10, pady=5)
        
        # Headers for categories
        hdr = ctk.CTkFrame(cat_frame, fg_color=theme.BORDER, height=30)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="RUBRO", font=ctk.CTkFont(size=9, weight="bold"), text_color=theme.TEXT_MUTED, width=200, anchor="w", padx=10).pack(side="left")
        ctk.CTkLabel(hdr, text="CANTIDAD", font=ctk.CTkFont(size=9, weight="bold"), text_color=theme.TEXT_MUTED, width=80).pack(side="left")
        ctk.CTkLabel(hdr, text="V. TOTAL INICIAL", font=ctk.CTkFont(size=9, weight="bold"), text_color=theme.TEXT_MUTED, width=120).pack(side="left")
        ctk.CTkLabel(hdr, text="DEPRECIACIÓN", font=ctk.CTkFont(size=9, weight="bold"), text_color=theme.TEXT_MUTED, width=120).pack(side="left")
        ctk.CTkLabel(hdr, text="V. ACTUAL NETO", font=ctk.CTkFont(size=9, weight="bold"), text_color=theme.TEXT_MUTED, width=120).pack(side="left")
        
        for name, stats in summary.get('categories', {}).items():
            row = ctk.CTkFrame(cat_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=name, font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_MAIN, width=200, anchor="w", padx=10).pack(side="left")
            ctk.CTkLabel(row, text=str(stats['qty']), font=ctk.CTkFont(size=11), text_color=theme.TEXT_MAIN, width=80).pack(side="left")
            ctk.CTkLabel(row, text=f"${stats['val_tot']:,.0f}", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MAIN, width=120).pack(side="left")
            ctk.CTkLabel(row, text=f"${stats['depr']:,.0f}", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MAIN, width=120).pack(side="left")
            ctk.CTkLabel(row, text=f"${stats['val_cur']:,.0f}", font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.SUCCESS, width=120).pack(side="left")
            
        # 2. Grouped Items List
        ctk.CTkLabel(self.scroll, text="Detalle de Artículos", font=ctk.CTkFont(size=13, weight="bold"), text_color=theme.PRIMARY, anchor="w").pack(fill="x", padx=10, pady=(20, 5))
        
        items_frame = ctk.CTkFrame(self.scroll, fg_color=theme.BG_CARD, corner_radius=10, border_width=1, border_color=theme.BORDER)
        items_frame.pack(fill="x", padx=10, pady=5)
        
        hdr_i = ctk.CTkFrame(items_frame, fg_color=theme.BORDER, height=30)
        hdr_i.pack(fill="x")
        ctk.CTkLabel(hdr_i, text="DESCRIPCIÓN", font=ctk.CTkFont(size=9, weight="bold"), text_color=theme.TEXT_MUTED, width=200, anchor="w", padx=10).pack(side="left")
        ctk.CTkLabel(hdr_i, text="MARCA / MODELO", font=ctk.CTkFont(size=9, weight="bold"), text_color=theme.TEXT_MUTED, width=150, anchor="w").pack(side="left")
        ctk.CTkLabel(hdr_i, text="CANT", font=ctk.CTkFont(size=9, weight="bold"), text_color=theme.TEXT_MUTED, width=50).pack(side="left")
        ctk.CTkLabel(hdr_i, text="ESTADO", font=ctk.CTkFont(size=9, weight="bold"), text_color=theme.TEXT_MUTED, width=80).pack(side="left")
        ctk.CTkLabel(hdr_i, text="VALOR ACTUAL", font=ctk.CTkFont(size=9, weight="bold"), text_color=theme.TEXT_MUTED, width=120).pack(side="left")
        
        for i, item in enumerate(summary.get('items', [])):
            bg = theme.BORDER if i % 2 == 0 else "transparent"
            row = ctk.CTkFrame(items_frame, fg_color=bg)
            row.pack(fill="x", pady=1)
            
            ctk.CTkLabel(row, text=item['desc'][:30], font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_MAIN, width=200, anchor="w", padx=10).pack(side="left")
            ctk.CTkLabel(row, text=f"{item['brand']}/{item['model']}"[:25], font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED, width=150, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=str(item['qty']), font=ctk.CTkFont(size=11), text_color=theme.TEXT_MAIN, width=50).pack(side="left")
            ctk.CTkLabel(row, text=item['state'], font=ctk.CTkFont(size=11), text_color=theme.WARNING if item['state'] in ['REGULAR', 'MALO'] else theme.SUCCESS, width=80).pack(side="left")
            ctk.CTkLabel(row, text=f"${item['val_cur']:,.0f}", font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.SUCCESS, width=120).pack(side="left")
