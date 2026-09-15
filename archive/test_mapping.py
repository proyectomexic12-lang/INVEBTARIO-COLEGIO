import openpyxl
wb = openpyxl.load_workbook('Inventario_RECTORIA.xlsx', data_only=True)
sheet = wb.active
# Mimic current intelligent mapping
keywords = {
    "qty": ["CANTIDAD", "CANT", "UNIDADES"],
}
headers = [str(c.value).upper().strip() if c.value else "" for c in sheet[1]]
print(f"Headers: {headers}")
for k, v in keywords.items():
    for i, h in enumerate(headers):
        if any(kw in h for kw in v):
            print(f"Mapped {k} to Col {i+1}")
