import openpyxl
wb = openpyxl.load_workbook('PlantillaConsultaInventarioGeneral1.xlsx', data_only=True)
sheet = wb.active
for r in range(1, 40):
    row_data = [str(c.value).strip() if c.value else "NONE" for c in sheet[r]]
    # Look for common header keywords anywhere in the row
    if any(k in " ".join(row_data).upper() for k in ["DESCRIPCIÓN", "CÓDIGO ARTÍCULO", "RUBRO CONTABLE"]):
        print(f"Header at Row {r}: {row_data[:10]}...")
        break
