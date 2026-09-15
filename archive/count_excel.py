import openpyxl
wb = openpyxl.load_workbook('Inventario_RECTORIA.xlsx', data_only=True)
sheet = wb.active
rows = list(sheet.iter_rows(values_only=True))
print(f"Total Rows in Excel: {len(rows)}")
valid_data_rows = 0
for r in rows:
    # Check if this row has something in description (column 3 typically)
    if r[2] and str(r[2]).strip() and str(r[2]).upper() not in ["DESCRIPCIÓN", "ARTÍCULO", "NONE"]:
        valid_data_rows += 1
print(f"Valid Data Rows: {valid_data_rows}")
