import codecs
import os

main_path = os.path.join(os.path.dirname(__file__), "main.py")
with codecs.open(main_path, 'r', 'utf-8') as f:
    text = f.read()

# 1. Remove ModernReports
start_idx = text.find("class ModernReports(ctk.CTkScrollableFrame):")
end_idx = text.find("class ModernProfile(ctk.CTkScrollableFrame):")
if start_idx != -1 and end_idx != -1:
    text = text[:start_idx] + "\n" + text[end_idx:]

# 2. Add reports to ModernSettings
target2 = """        self.create_tool_card(
            "Exportador Avanzado Consolidado", 
            "Selecciona salones específicos para generar un Excel único con totalización patrimonial.", 
            "🚀", self.open_advanced_export_tool, "#10b981"
        )"""

replacement2 = target2 + """

        self.create_report_module("REPORTES FISCALES Y DE LEY", "⚖️", [
            ("Inventario General Consolidado", "Generar el reporte oficial para la Secretaría de Educación conforme a la ley 130.", self.controller.export_excel),
            ("Balance de Activos por Rubro", "Análisis de depreciación y valoración contable por grupo presupuestal.", None),
            ("Certificado de Existencia Física", "Acta formal de validación de activos vigentes.", None)
        ])

        self.create_report_module("REPORTES OPERATIVOS", "⚙️", [
            ("Listado por Dependencia", "Desglose técnico de activos ubicados en salones y áreas administrativas.", None),
            ("Reporte de Mantenimiento Crítico", "Identificación de bienes en estado Regular/Malo para reposición.", None)
        ])

        self.create_report_module("HISTÓRICOS Y BAJAS", "📉", [
            ("Libro Maestro de Bajas", "Registro cronológico de desincorporación de activos y motivos legales.", None),
            ("Acta de Eliminación Masiva", "Documento para el comité de bajas y remates electrónicos.", None)
        ])"""

text = text.replace(target2, replacement2)

# 3. Add create_report_module to ModernSettings
target3 = """        ctk.CTkButton(inner, text="EJECUTAR HERRAMIENTA", width=180, height=45, corner_radius=12,
                      fg_color=color, hover_color="#0f766e", command=cmd).pack(side="right")

    def open_advanced_export_tool(self):"""

replacement3 = """        ctk.CTkButton(inner, text="EJECUTAR HERRAMIENTA", width=180, height=45, corner_radius=12,
                      fg_color=color, hover_color="#0f766e", command=cmd).pack(side="right")

    def create_report_module(self, section_title, icon, reports):
        sec_f = ctk.CTkFrame(self.body, fg_color="transparent")
        sec_f.pack(fill="x", pady=(10, 20))
        
        title_f = ctk.CTkFrame(sec_f, fg_color="transparent")
        title_f.pack(fill="x", pady=5)
        ctk.CTkLabel(title_f, text=f"{icon} {section_title}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#94a3b8").pack(side="left")
        
        for name, desc, cmd in reports:
            card = ctk.CTkFrame(sec_f, fg_color="#0f172a", corner_radius=20, border_width=1, border_color="#1e293b")
            card.pack(fill="x", pady=8)
            
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(padx=25, pady=20, fill="x")
            
            info = ctk.CTkFrame(inner, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(info, text=name, font=ctk.CTkFont(size=18, weight="bold"), text_color="#f8fafc", anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=desc, font=ctk.CTkFont(size=12), text_color="#64748b", anchor="w").pack(fill="x", pady=(2,0))
            
            btn_color = "#10b981" if cmd else "#1e293b"
            btn_txt = "GENERAR EXCEL" if cmd else "PROXIMAMENTE"
            ctk.CTkButton(inner, text=btn_txt, width=180, height=45, corner_radius=12,
                          fg_color=btn_color, hover_color="#059669", 
                          state="normal" if cmd else "disabled",
                          command=cmd).pack(side="right", padx=(20, 0))

    def open_advanced_export_tool(self):"""

text = text.replace(target3, replacement3)

# 4. Remove sidebar item
target4 = '            ("Centro de Reportes", "📈", "ModernReports"),\n'
text = text.replace(target4, "")

# 5. Remove ModernReports from pages dict
target5 = '            "ModernReports": ModernReports(self.workspace, self),\n'
text = text.replace(target5, "")

with codecs.open(main_path, 'w', 'utf-8') as f:
    f.write(text)

print("Migration complete.")
