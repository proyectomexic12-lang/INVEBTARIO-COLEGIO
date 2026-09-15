import openpyxl
wb = openpyxl.load_workbook('Inventario_RECTORIA.xlsx', data_only=True)
sheet = wb.active
headers = [str(c.value).strip() if c.value else "NONE" for c in sheet[1]]
data_row = [str(c.value).strip() if c.value else "NONE" for c in sheet[2]]
for i, (h, d) in enumerate(zip(headers, data_row)):
    print(f"Col {i+1}: Header='{h}', Data='{d}'")
