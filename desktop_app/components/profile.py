import customtkinter as ctk
from tkinter import messagebox
from theme import theme

class ModernProfile(ctk.CTkScrollableFrame):
    def __init__(self, master, controller, setting_repo):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.setting_repo = setting_repo
        self.refresh_form()

    def refresh_form(self):
        for w in self.winfo_children(): w.destroy()

        # Header
        h = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=20, border_width=1, border_color=theme.BORDER)
        h.pack(fill="x", padx=40, pady=(35, 20))
        ctk.CTkLabel(h, text="🏫 Perfil Institucional",
                     font=ctk.CTkFont(size=28, weight="bold"), text_color=theme.TEXT_MAIN).pack(pady=22, anchor="w", padx=35)

        # Datos institucionales desde DB
        settings = {
            "entidad": self.setting_repo.get_setting("entidad", "N/A"),
            "nit": self.setting_repo.get_setting("nit", "N/A"),
            "dane": self.setting_repo.get_setting("dane", "N/A"),
            "representante": self.setting_repo.get_setting("representante", "N/A"),
            "direccion": self.setting_repo.get_setting("direccion", "N/A"),
            "telefono": self.setting_repo.get_setting("telefono", "N/A"),
            "ciudad": self.setting_repo.get_setting("ciudad", "N/A"),
            "año_trabajo": self.setting_repo.get_setting("año_trabajo", "N/A"),
        }

        card = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=18,
                            border_width=1, border_color=theme.BORDER)
        card.pack(fill="x", padx=40, pady=(0, 20))

        fields = [
            ("ENTIDAD",         "entidad"),
            ("NIT",             "nit"),
            ("CÓDIGO DANE",     "dane"),
            ("REPRESENTANTE",   "representante"),
            ("DIRECCIÓN",       "direccion"),
            ("TELÉFONO",        "telefono"),
            ("CIUDAD",          "ciudad"),
            ("AÑO DE TRABAJO",  "año_trabajo"),
        ]

        for i, (lbl, key) in enumerate(fields):
            row_bg = theme.BG_SIDEBAR if i % 2 == 0 else "transparent"
            f = ctk.CTkFrame(card, fg_color=row_bg, height=50, corner_radius=8)
            f.pack(fill="x", padx=15, pady=3)
            f.pack_propagate(False)
            ctk.CTkLabel(f, text=lbl, font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=theme.PRIMARY_LIGHT, width=200, anchor="w").pack(side="left", padx=15)
            ctk.CTkLabel(f, text=settings.get(key, "N/A"),
                         font=ctk.CTkFont(size=13), text_color=theme.TEXT_MAIN,
                         anchor="w").pack(side="left", fill="x", expand=True)

        # Botón para ir a Configuración
        ctk.CTkButton(self, text="✏️ Editar Datos en Configuración",
                      height=46, fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
                      font=ctk.CTkFont(size=13, weight="bold"), corner_radius=12,
                      command=lambda: self.controller.select_page("ModernSettings", "Gestión del Sistema")).pack(fill="x", padx=40, pady=(10, 40))
