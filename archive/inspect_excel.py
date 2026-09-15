import openpyxl
import os

template_path = r"c:\Users\USUARIO\Desktop\inventario\PlantillaConsultaInventarioGeneral1.xlsx"

if not os.path.exists(template_path):
    print(f"Error: File not found at {template_path}")
else:
    wb = openpyxl.load_workbook(template_path, data_only=True)
    sheet = wb.active
    print(f"Sheet Name: {sheet.title}")
    
    # Read headers (usually first 2 or 3 rows might be info, then headers)
    # Let's read first 10 rows to be safe
    for r in range(1, 15):
        row_data = [str(sheet.cell(row=r, column=c).value) for c in range(1, 20)]
        print(f"Row {r}: {' | '.join(row_data)}")
