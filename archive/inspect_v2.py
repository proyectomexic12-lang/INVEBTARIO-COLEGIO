import openpyxl
import os

files = ['PlantillaConsultaInventarioGeneral1.xlsx', 'Inventario_RECTORIA.xlsx']
for filename in files:
    if not os.path.exists(filename):
        print(f"--- File not found: {filename} ---")
        continue
    print(f"\n--- Inspecting: {filename} ---")
    wb = openpyxl.load_workbook(filename, data_only=True)
    sheet = wb.active
    print(f"Active Sheet: {sheet.title}")
    
    for r in range(1, 21):
        row_data = [str(sheet.cell(row=r, column=c).value) for c in range(1, 20)]
        print(f"Row {r:02d}: {' | '.join(row_data)}")
