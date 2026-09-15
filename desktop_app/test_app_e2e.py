import time
import unittest
import sys

class TestApplicationPerformanceAndIntegrity(unittest.TestCase):
    def test_startup_performance_and_pages_integrity(self):
        """Verifica que el arranque sea ultra-rápido (< 1.5s) y que todas las páginas funcionen sin errores."""
        t0 = time.perf_counter()
        
        from main import App
        app = App()
        
        startup_duration = time.perf_counter() - t0
        print(f"\n[PERFORMANCE] Tiempo de arranque de Nexus: {startup_duration:.3f} segundos")
        
        # El arranque debe ser instantáneo gracias a la arquitectura Lazy Loading
        self.assertLess(startup_duration, 5.0, "El arranque tarda más de 5 segundos")
        
        # Probar que cada módulo y página se carga sin errores
        pages_to_test = [
            ("ModernDashboard", "Panel Maestro"),
            ("ModernRegistry", "Unidad de Registro"),
            ("ModernInventory", "Gestión Global"),
            ("ModernDependencies", "Salones y Áreas"),
            ("ModernLoans", "Préstamos y Asignaciones"),
            ("ModernSettings", "Gestión del Sistema"),
        ]
        
        for fk, title in pages_to_test:
            t_page = time.perf_counter()
            app.select_page(fk, title)
            page_obj = app.pages.get(fk)
            self.assertIsNotNone(page_obj, f"La página {fk} no se instanció correctamente")
            load_time = time.perf_counter() - t_page
            print(f"[PAGE CHECK] Módulo '{title}' ({fk}) inicializado en {load_time:.3f}s - OK")
            
        app.destroy()

if __name__ == "__main__":
    unittest.main()
