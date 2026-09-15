"""
Módulo de Utilidad de Desplazamiento Fluido (SOLID Architecture)
Proporciona soporte universal para desplazamiento con rueda del ratón (vertical y horizontal con Shift).
"""
import sys

def enable_smooth_scroll(canvas, container=None):
    """
    Habilita desplazamiento bidireccional suave con la rueda del ratón para un tk.Canvas.
    - Rueda normal: Desplazamiento vertical (arriba / abajo).
    - Shift + Rueda: Desplazamiento horizontal (izquierda / derecha).
    - Compatible con cualquier widget hijo (etiquetas, celdas, botones, marcos).
    """
    target = container if container is not None else canvas

    def _is_over_target(widget):
        curr = widget
        while curr is not None:
            if curr == target or curr == canvas:
                return True
            curr = getattr(curr, 'master', None)
        return False

    def _on_mousewheel(event):
        try:
            if not canvas.winfo_exists():
                return
            if not _is_over_target(event.widget):
                return
            
            # Tkinter state bit 0x0001 representa la tecla Shift presionada
            is_shift = bool(event.state & 0x0001)
            delta = event.delta
            if delta == 0:
                return
                
            steps = int(-1 * (delta / 40))
            if steps == 0:
                steps = -1 if delta > 0 else 1

            if is_shift:
                canvas.xview_scroll(steps, "units")
            else:
                canvas.yview_scroll(steps, "units")
        except Exception:
            pass

    def _on_linux_scroll_up(event):
        try:
            if not canvas.winfo_exists() or not _is_over_target(event.widget):
                return
            is_shift = bool(event.state & 0x0001)
            if is_shift:
                canvas.xview_scroll(-2, "units")
            else:
                canvas.yview_scroll(-2, "units")
        except Exception:
            pass

    def _on_linux_scroll_down(event):
        try:
            if not canvas.winfo_exists() or not _is_over_target(event.widget):
                return
            is_shift = bool(event.state & 0x0001)
            if is_shift:
                canvas.xview_scroll(2, "units")
            else:
                canvas.yview_scroll(2, "units")
        except Exception:
            pass

    if sys.platform.startswith("linux"):
        canvas.bind_all("<Button-4>", _on_linux_scroll_up, add=True)
        canvas.bind_all("<Button-5>", _on_linux_scroll_down, add=True)
    else:
        canvas.bind_all("<MouseWheel>", _on_mousewheel, add=True)
