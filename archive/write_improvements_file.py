import os
import json

log_file = r"C:\Users\USUARIO\.gemini\antigravity-ide\brain\5bb11621-e64d-4ccf-9848-ba8d0abd3a04\.system_generated\logs\transcript.jsonl"
out_file = r"c:\Users\USUARIO\Desktop\inventario\archive\mejoras_originales.txt"

with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
    for line_num, line in enumerate(f, 1):
        if line_num == 133:
            try:
                obj = json.loads(line)
                content = obj.get("content", "")
                with open(out_file, "w", encoding="utf-8") as out:
                    out.write(content)
                print("Successfully wrote improvements to file!")
            except Exception as e:
                print("Error parsing:", e)
