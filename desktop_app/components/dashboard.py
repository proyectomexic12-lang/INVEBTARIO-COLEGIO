import customtkinter as ctk
import matplotlib  # type: ignore
matplotlib.use("TkAgg")  # type: ignore
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from theme import theme

class ModernDashboard(ctk.CTkScrollableFrame):
    def __init__(self, master, controller, asset_repo):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.asset_repo = asset_repo
        
        # --- Corporate Executive Intro ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=40, pady=(35, 10))
        
        self.title_group = ctk.CTkFrame(self.header, fg_color="transparent")
        self.title_group.pack(side="left")
        
        badge_frame = ctk.CTkFrame(self.title_group, fg_color="transparent")
        badge_frame.pack(anchor="w", pady=(0, 6))
        
        badge = ctk.CTkFrame(badge_frame, fg_color=theme.BG_CARD, border_width=1, border_color=theme.BORDER, corner_radius=8)
        badge.pack(side="left")
        ctk.CTkLabel(badge, text="● SUITE EJECUTIVA INSTITUCIONAL", 
                    font=ctk.CTkFont(size=9, weight="bold"), 
                    text_color=theme.SUCCESS).pack(padx=12, pady=4)
        
        ctk.CTkLabel(self.title_group, text="Consola Ejecutiva de Control Patrimonial", 
                    font=ctk.CTkFont(size=30, weight="bold"), text_color=theme.TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(self.title_group, text="Auditoría patrimonial, alertas tempranas y métricas financieras de la entidad", 
                    font=ctk.CTkFont(size=13), text_color=theme.TEXT_MUTED).pack(anchor="w")

        # --- Statistics Grid (HD Cards) ---
        self.stats_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_grid.pack(fill="x", padx=40, pady=(20, 10))
        self.stats_grid.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

    def refresh_stats(self):
        sede = getattr(self.controller, "global_sede", "Todas")
        self.controller.run_in_thread(self.asset_repo.get_dashboard_data, self._finished_stats, sede)

    def _finished_stats(self, results):
        if len(results) == 4:
            stats, projection, dep_stats, alerts = results
        else:
            stats, projection, dep_stats = results
            alerts = []
        total_assets, total_initial_value, total_real_value, total_bajas = stats
        
        for widget in self.stats_grid.winfo_children():
            widget.destroy()

        total_depr = max(0, total_initial_value - total_real_value)

        self.create_stat_card("ACTIVOS FÍSICOS", f"{total_assets:,}", "📦", theme.PRIMARY_LIGHT, 0)
        self.create_stat_card("VALOR COMPRA", f"${total_initial_value/1e6:.2f}M", "💰", theme.SUCCESS, 1)
        self.create_stat_card("DEPRECIACIÓN", f"${total_depr/1e6:.2f}M", "🔥", theme.DANGER, 2)
        self.create_stat_card("VALOR REAL", f"${total_real_value/1e6:.2f}M", "🛡️", theme.WARNING, 3)
        self.create_stat_card("BAJAS", f"{total_bajas:,}", "📉", theme.TEXT_MUTED, 4)

        self.setup_analysis_section(projection, dep_stats, alerts)

    def setup_analysis_section(self, projection, dep_stats, active_alerts=None):
        if active_alerts is None:
            active_alerts = []

        if hasattr(self, 'analysis_frame'):
            self.analysis_frame.destroy()

        self.analysis_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.analysis_frame.pack(fill="both", expand=True, padx=40, pady=(15, 30))

        self.left_col = ctk.CTkFrame(self.analysis_frame, fg_color="transparent")
        self.left_col.pack(side="left", fill="both", expand=True, padx=(0, 15))
        
        self.right_col = ctk.CTkFrame(self.analysis_frame, fg_color="transparent", width=420)
        self.right_col.pack(side="right", fill="both", padx=(15, 0))

        # --- Smart Alerts Panel ---
        alerts_card = ctk.CTkFrame(self.left_col, corner_radius=20, border_width=1, border_color=theme.BORDER, fg_color=theme.BG_CARD)
        alerts_card.pack(fill="x", expand=False)
        
        a_header = ctk.CTkFrame(alerts_card, fg_color="transparent")
        a_header.pack(fill="x", padx=25, pady=(20, 8))
        ctk.CTkLabel(a_header, text="Panel de Alertas y Notificaciones", font=ctk.CTkFont(size=18, weight="bold"), text_color=theme.TEXT_MAIN).pack(side="left")
        
        ctk.CTkLabel(alerts_card, text="Monitoreo preventivo de depreciación, garantías y préstamos", 
                    font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED).pack(padx=25, anchor="w", pady=(0, 12))

        if not active_alerts:
            ctk.CTkLabel(alerts_card, text="✔ No hay alertas críticas pendientes en el sistema.", font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED).pack(padx=25, pady=(10, 20), anchor="w")
        else:
            for alert in active_alerts:
                a_f = ctk.CTkFrame(alerts_card, fg_color=theme.BG_SIDEBAR, corner_radius=12, border_width=1, border_color=theme.BORDER)
                a_f.pack(fill="x", padx=20, pady=6)
                
                icon_lbl = ctk.CTkLabel(a_f, text=alert['icon'], font=ctk.CTkFont(size=22))
                icon_lbl.pack(side="left", padx=(14, 8), pady=12)
                
                text_f = ctk.CTkFrame(a_f, fg_color="transparent")
                text_f.pack(side="left", fill="both", expand=True, pady=10)
                
                ctk.CTkLabel(text_f, text=alert['title'], font=ctk.CTkFont(size=13, weight="bold"), text_color=alert['color']).pack(anchor="w")
                ctk.CTkLabel(text_f, text=alert['description'], font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(anchor="w")
                
                if alert['count'] > 0:
                    count_badge = ctk.CTkFrame(a_f, fg_color=alert['color'], corner_radius=8, width=32, height=32)
                    count_badge.pack(side="right", padx=14)
                    count_badge.pack_propagate(False)
                    ctk.CTkLabel(count_badge, text=str(alert['count']), font=ctk.CTkFont(size=11, weight="bold"), text_color="white").pack(expand=True)
            ctk.CTkFrame(alerts_card, fg_color="transparent", height=8).pack()

        # --- Pie Chart Card ---
        pie_card = ctk.CTkFrame(self.left_col, corner_radius=20, border_width=1, border_color=theme.BORDER, fg_color=theme.BG_CARD)
        pie_card.pack(fill="both", expand=True, pady=(15, 0))

        ctk.CTkLabel(pie_card, text="Distribución de Valor Patrimonial", font=ctk.CTkFont(size=18, weight="bold"), text_color=theme.TEXT_MAIN).pack(pady=(20, 4), padx=25, anchor="w")
        ctk.CTkLabel(pie_card, text="Concentración de valor en libros según dependencia o área", font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED).pack(padx=25, anchor="w", pady=(0, 10))

        # Process dep_stats for pie chart
        sorted_deps = sorted(dep_stats.items(), key=lambda item: item[1][3], reverse=True)
        sorted_deps = [x for x in sorted_deps if x[1][3] > 0]
        
        labels = []
        sizes = []
        total_val = sum(x[1][3] for x in sorted_deps)
        
        if total_val > 0:
            top_n = sorted_deps[:5]
            for dep, (rows, units, init, real) in top_n:
                labels.append(dep.title() if dep else "Sin Asignar")
                sizes.append(real)
                
            if len(sorted_deps) > 5:
                other_val = sum(x[1][3] for x in sorted_deps[5:])
                labels.append("Otros")
                sizes.append(other_val)

            fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
            fig.patch.set_facecolor(theme.BG_CARD)
            ax.set_facecolor(theme.BG_CARD)
            
            # Cohesive executive palette for the pie chart
            colors = ['#2563eb', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#475569']
            
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, autopct='%1.1f%%',
                startangle=140, colors=colors[:len(labels)],
                textprops=dict(color=theme.TEXT_MUTED, fontsize=8),
                wedgeprops=dict(width=0.45, edgecolor=theme.BORDER, linewidth=1)
            )
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(8)
                autotext.set_weight('bold')
                
            ax.axis('equal')
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, master=pie_card)
            canvas.draw_idle()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=(0, 15))
            plt.close(fig)
        else:
            ctk.CTkLabel(pie_card, text="No hay activos con valor neto positivo para graficar.", font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED).pack(pady=40)

        # --- Executive Action Center ---
        tools_card = ctk.CTkFrame(self.right_col, corner_radius=20, border_width=1, border_color=theme.BORDER, fg_color=theme.BG_CARD)
        tools_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(tools_card, text="Acciones Rápidas", font=ctk.CTkFont(size=18, weight="bold"), text_color=theme.TEXT_MAIN).pack(pady=(20, 12), padx=25, anchor="w")
        
        actions = [
            ("REGISTRO INMEDIATO", "Cargar nuevo activo con cálculo automático", lambda: self.controller.select_page("ModernRegistry", "Unidad de Registro")),
            ("EXPORTAR DATA MAESTRA", "Generar informe financiero en Excel", lambda: self.controller.export_excel()),
            ("GESTIÓN GLOBAL", "Consultar, filtrar y auditar inventario", lambda: self.controller.select_page("ModernInventory", "Gestión Global"))
        ]
        
        for t, s, cmd in actions:
            btn = ctk.CTkButton(tools_card, text=f"{t}\n{s}", height=75, 
                               fg_color=theme.BG_SIDEBAR, hover_color=theme.PRIMARY_HOVER, 
                               border_width=1, border_color=theme.BORDER,
                               anchor="w", text_color=theme.TEXT_MAIN, corner_radius=12,
                               command=cmd)
            btn.pack(fill="x", padx=18, pady=6)

        # --- PREDICTIVE PROJECTION CARD (Obsidian Theme) ---
        analysis_card = ctk.CTkFrame(self.right_col, corner_radius=20, border_width=1, border_color=theme.BORDER, fg_color=theme.BG_CARD)
        analysis_card.pack(fill="both", expand=True, pady=(15, 0))
        
        ctk.CTkLabel(analysis_card, text="PROYECCIÓN PATRIMONIAL", font=ctk.CTkFont(size=14, weight="bold"), text_color=theme.PRIMARY_LIGHT).pack(pady=(18, 2), padx=25, anchor="w")
        ctk.CTkLabel(analysis_card, text="Estimación de valor contable a 5 años (Depreciación)", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(padx=25, anchor="w")
        
        # Real Matplotlib chart visualization matching Executive Palette
        fig, ax = plt.subplots(figsize=(4, 2.5), dpi=100)
        fig.patch.set_facecolor(theme.BG_CARD)
        ax.set_facecolor(theme.BG_CARD)
        
        years = ['Hoy', 'Año 1', 'Año 2', 'Año 3', 'Año 4', 'Año 5']
        values_in_m = [v / 1e6 for v in projection]
        
        # Draw line with markers
        ax.plot(years, values_in_m, marker='o', color='#3b82f6', linewidth=2.2, markersize=5.5, markerfacecolor='white', markeredgecolor='#3b82f6')
        ax.fill_between(years, values_in_m, color='#3b82f6', alpha=0.12)
        
        ax.tick_params(colors=theme.TEXT_MUTED, labelsize=8)
        ax.spines['bottom'].set_color(theme.BORDER)
        ax.spines['left'].set_color(theme.BORDER)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        for idx, val in enumerate(values_in_m):
            ax.annotate(f"${val:.2f}M", 
                        (idx, val), 
                        textcoords="offset points", 
                        xytext=(0, 7), 
                        ha='center', 
                        color='white', 
                        fontsize=7.5,
                        fontweight='bold')
            
        ax.grid(True, linestyle='--', alpha=0.12, color=theme.BORDER_HOVER)
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=analysis_card)
        canvas.draw_idle()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=(8, 15))
        plt.close(fig)

    def create_stat_card(self, title, value, icon, color, col):
        card = ctk.CTkFrame(self.stats_grid, corner_radius=20, border_width=1, border_color=theme.BORDER, fg_color=theme.BG_CARD, height=135)
        card.grid(row=0, column=col, padx=8, pady=8, sticky="nsew")
        card.pack_propagate(False)
        
        top_f = ctk.CTkFrame(card, fg_color="transparent")
        top_f.pack(fill="x", padx=18, pady=(16, 0))
        
        icon_lbl = ctk.CTkLabel(top_f, text=icon, font=ctk.CTkFont(size=24))
        icon_lbl.pack(side="left")
        
        title_lbl = ctk.CTkLabel(top_f, text=title, font=ctk.CTkFont(size=10, weight="bold"), text_color=color)
        title_lbl.pack(side="right")
        
        val_lbl = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=26, weight="bold"), text_color=theme.TEXT_MAIN)
        val_lbl.pack(anchor="w", padx=18, pady=(12, 0))
        
        sub_lbl = ctk.CTkLabel(card, text="En tiempo real", font=ctk.CTkFont(size=10), text_color=theme.TEXT_FAINT)
        sub_lbl.pack(anchor="w", padx=18)

