import openpyxl
wb = openpyxl.load_workbook('Inventario_RECTORIA.xlsx', data_only=True)
sheet = wb.active
headers = [str(c.value).upper().strip() if c.value else "" for c in sheet[1]]
for i, h in enumerate(headers):
    print(f"Col {i+1}: {h}")
