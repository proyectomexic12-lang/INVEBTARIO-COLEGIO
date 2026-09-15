import openpyxl
filename = 'PlantillaConsultaInventarioGeneral1.xlsx'
wb = openpyxl.load_workbook(filename, data_only=True)
sheet = wb.active
for r in range(1, 25):
    row_data = [str(sheet.cell(row=r, column=c).value) for c in range(1, 20)]
    print(f"Row {r:02d}: {' | '.join(row_data)}")
