import openpyxl

template_path = r"c:\Users\USUARIO\Desktop\inventario\PlantillaConsultaInventarioGeneral1.xlsx"
wb = openpyxl.load_workbook(template_path, data_only=True)
sheet = wb.active

# Let's find the row that looks like a header (contains 'Descripción' or similar)
for r in range(1, 20):
    row_values = [sheet.cell(row=r, column=c).value for c in range(1, 30)]
    if any(v and isinstance(v, str) and ("DESCRIPCION" in v.upper() or "EQUIPO" in v.upper()) for v in row_values):
        print(f"Header Row found at Row {r}")
        print(f"Values: {row_values}")
        break
else:
    print("No obvious header row found in first 20 rows.")
