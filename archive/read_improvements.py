import os
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

log_file = r"C:\Users\USUARIO\.gemini\antigravity-ide\brain\5bb11621-e64d-4ccf-9848-ba8d0abd3a04\.system_generated\logs\transcript.jsonl"
with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
    for line_num, line in enumerate(f, 1):
        try:
            obj = json.loads(line)
            if obj.get("source") == "MODEL":
                content = obj.get("content", "")
                if "1." in content and "20." in content or "mejoras" in content.lower():
                    # Check if it has a list of improvements
                    print(f"=== Model Match (Line {line_num}) ===")
                    print(content)
                    print("=" * 80)
        except Exception:
            pass
