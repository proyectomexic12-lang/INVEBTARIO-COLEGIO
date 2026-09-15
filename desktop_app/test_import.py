
import sys
import os
import traceback

try:
    import openpyxl
    wb = openpyxl.Workbook()
    wb.active.append(['CODIGO', 'DESCRIPCION', 'SEDE', 'DEP', 'VALOR', 'CANTIDAD'])
    wb.active.append(['1', 'Silla', 'Guaimaral', 'GRUPO 1', '100', '1'])
    wb.save('test.xlsx')

    class DummyController:
        def __init__(self):
            self.global_sede = 'Guaimaral'
        def run_in_thread(self, *args):
            pass

    import sqlite3
    class DummyRepo:
        def __init__(self):
            pass
        def generate_next_code(self, sede): return '123'
        def add_dependency(self, *args, **kwargs): pass
        def bulk_add_assets(self, *args, **kwargs): pass
        def sync_accounting_integrity(self): pass

    from main import App
    app = App()
    
    # Mock repos
    app.asset_repo = DummyRepo()
    app.dep_repo = DummyRepo()

    res = app.run_intelligent_import('test.xlsx')
    print('RESULT:', res)
except Exception as e:
    traceback.print_exc()
