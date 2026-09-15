import os
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

log_file = r"C:\Users\USUARIO\.gemini\antigravity-ide\brain\fc7898c0-30db-4939-9433-6602f78e5630\.system_generated\logs\transcript.jsonl"
if os.path.exists(log_file):
    print("Found log file!")
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        for line_num, line in enumerate(f, 1):
            try:
                obj = json.loads(line)
                if obj.get("source") == "USER_EXPLICIT" and obj.get("type") == "USER_INPUT":
                    print(f"=== User Request {line_num} ===")
                    print(obj.get("content"))
                    print("-" * 50)
            except Exception as e:
                pass
else:
    print("Log file not found.")
