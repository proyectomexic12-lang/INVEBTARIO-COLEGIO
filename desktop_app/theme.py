import colorsys

class Theme:
    # Color Tokens
    BG_APP: str = "#090d16"
    BG_SIDEBAR: str = "#0c1220"
    BG_CARD: str = "#111a2e"
    BG_CARD_LIGHT: str = "#16223b"
    BG_INPUT: str = "#070a12"
    BORDER: str = "#1e2c4a"
    BORDER_HOVER: str = "#2d4370"
    PRIMARY: str = "#2563eb"
    PRIMARY_HOVER: str = "#1d4ed8"
    PRIMARY_LIGHT: str = "#3b82f6"
    ACCENT_CYAN: str = "#06b6d4"
    TEXT_MAIN: str = "#f8fafc"
    TEXT_MUTED: str = "#94a3b8"
    TEXT_FAINT: str = "#64748b"
    SUCCESS: str = "#10b981"
    SUCCESS_BG: str = "#06281e"
    DANGER: str = "#f43f5e"
    DANGER_BG: str = "#2c0e15"
    ERROR: str = "#f43f5e"
    WARNING: str = "#f59e0b"
    WARNING_BG: str = "#2a1c06"
    INFO: str = "#38bdf8"

    def __init__(self, hue=222, saturation=47):
        self.hue = hue          # 0 - 360
        self.saturation = saturation  # 0 - 100
        self.current_theme_name = "Obsidian Executive"
        
        # Predefined theme choices
        self.THEMES = {
            "Obsidian Executive": (222, 47),  # Ultra premium Deep Midnight & Sapphire
            "Slate Blue": (220, 70),
            "Emerald Green": (155, 65),       # Luxury Emerald Banking
            "Titanium Dark": (210, 15),       # Minimalist corporate dark grey/monochrome
            "Amber Gold": (38, 85),           # Executive Swiss Gold
            "Crimson Red": (350, 65),
            "Purple Velvet": (265, 65)
        }
        
        self.refresh()

    def set_theme_by_name(self, name):
        if name in self.THEMES:
            h, s = self.THEMES[name]
            self.hue = h
            self.saturation = s
            self.current_theme_name = name
            self.refresh()
            return True
        return False

    def refresh(self):
        h = self.hue / 360.0
        s = self.saturation / 100.0
        
        def hsl_to_hex(h_val, s_val, l_val):
            r, g, b = colorsys.hls_to_rgb(h_val, l_val, s_val)
            return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

        # Executive dark backgrounds
        self.BG_APP = "#090d16"                    # Very deep rich midnight
        self.BG_SIDEBAR = "#0c1220"                # Solid executive sidebar
        self.BG_CARD = "#111a2e"                   # Sleek card container
        self.BG_CARD_LIGHT = "#16223b"             # Elevated card highlight
        self.BG_INPUT = "#070a12"                  # Recessed crisp input field
        
        # Borders with subtle executive luminescence
        self.BORDER = "#1e2c4a"                    # Clean defined border
        self.BORDER_HOVER = "#2d4370"              # Active hover border
        
        # Accents
        self.PRIMARY = "#2563eb"                   # Royal Executive Blue
        self.PRIMARY_HOVER = "#1d4ed8"             # Deep Royal Hover
        self.PRIMARY_LIGHT = "#3b82f6"             # Vibrant Accent
        self.ACCENT_CYAN = "#06b6d4"              # Tech highlight
        
        # Typography
        self.TEXT_MAIN = "#f8fafc"                 # Crisp pure white
        self.TEXT_MUTED = "#94a3b8"                # Slate-400 high readability
        self.TEXT_FAINT = "#64748b"                # Subtitles and micro labels
        
        # Semantic alert colors
        self.SUCCESS = "#10b981"                   # Emerald
        self.SUCCESS_BG = "#06281e"
        self.DANGER = "#f43f5e"                    # Rose/Crimson
        self.DANGER_BG = "#2c0e15"
        self.ERROR = self.DANGER
        self.WARNING = "#f59e0b"                   # Amber
        self.WARNING_BG = "#2a1c06"
        self.INFO = "#38bdf8"

# Global theme instance
theme = Theme(hue=222, saturation=47)

