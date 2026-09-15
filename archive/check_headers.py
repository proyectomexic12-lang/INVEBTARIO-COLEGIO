import openpyxl
wb = openpyxl.load_workbook('Inventario_RECTORIA.xlsx', data_only=True)
sheet = wb.active
for r in range(1, 5):
    row_data = [str(c.value).strip() if c.value else "NONE" for c in sheet[r]]
    print(f"Row {r}: {row_data}")
