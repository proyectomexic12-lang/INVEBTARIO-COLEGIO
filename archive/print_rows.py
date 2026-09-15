import openpyxl

template_path = r"c:\Users\USUARIO\Desktop\inventario\PlantillaConsultaInventarioGeneral1.xlsx"
wb = openpyxl.load_workbook(template_path, data_only=True)
sheet = wb.active

for r in range(1, 25):
    row_values = [str(sheet.cell(row=r, column=c).value) for c in range(1, 15)]
    print(f"Row {r:02d}: {row_values}")
