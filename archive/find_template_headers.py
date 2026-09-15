import openpyxl
wb = openpyxl.load_workbook('PlantillaConsultaInventarioGeneral1.xlsx', data_only=True)
sheet = wb.active
for r in range(1, 40):
    row_data = [str(c.value).strip() if c.value else "NONE" for c in sheet[r][:10]]
    if any(k in row_data[0] or k in row_data[1] or k in row_data[2] or k in row_data[3] for k in ["DESCRIPCIÓN", "CÓDIGO", "RUBRO"]):
        print(f"Header found at Row {r}: {row_data}")
        break
