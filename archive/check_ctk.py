import customtkinter as ctk
try:
    print(f"Orientation support: {hasattr(ctk.CTkScrollableFrame, 'orientation') or 'Maybe'}")
    # ctk.CTk(None) isn't right, just check the help
    print(ctk.CTkScrollableFrame.__doc__)
except Exception as e:
    print(f"Error: {e}")
