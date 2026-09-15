import os
import json

msg_dir = r"C:\Users\USUARIO\.gemini\antigravity-ide\brain\5bb11621-e64d-4ccf-9848-ba8d0abd3a04\.system_generated\messages"
if os.path.exists(msg_dir):
    for f in os.listdir(msg_dir):
        if f.endswith(".json"):
            path = os.path.join(msg_dir, f)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as file:
                    data = json.load(file)
                    # convert data to string and search
                    data_str = json.dumps(data)
                    if "mejoras" in data_str.lower() or "gráficos estadísticos" in data_str.lower():
                        print(f"Found match in message file: {f}")
                        # let's look closer at the file
                        # if it's a list, print keys or part of it
                        if isinstance(data, dict):
                            for k, v in data.items():
                                val_str = str(v)
                                if "mejoras" in val_str.lower() or "gráficos estadísticos" in val_str.lower():
                                    print(f"Key: {k}, Value length: {len(val_str)}")
                                    # Write this value to improvements_full.txt
                                    with open(r"c:\Users\USUARIO\Desktop\inventario\archive\mejoras_full.txt", "w", encoding="utf-8") as out:
                                        out.write(val_str)
                                    print("Wrote to archive/mejoras_full.txt")
            except Exception as e:
                print(f"Error reading {f}: {e}")
else:
    print("Messages directory not found.")
