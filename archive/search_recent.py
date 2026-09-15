import os
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

folders = [
    "5bb11621-e64d-4ccf-9848-ba8d0abd3a04",
    "9b39c5a4-52ca-409d-9c80-89f0fe025bf6",
    "d15d68b3-1086-46e1-9500-69018b647f5f",
    "654bf383-1ed0-4a3b-8d0f-bd625d750179"
]

brain_dir = r"C:\Users\USUARIO\.gemini\antigravity-ide\brain"
for folder in folders:
    folder_path = os.path.join(brain_dir, folder)
    log_file = os.path.join(folder_path, ".system_generated", "logs", "transcript.jsonl")
    if os.path.exists(log_file):
        print(f"=== SEARCHING FOLDER: {folder} ===")
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    obj = json.loads(line)
                    source = obj.get("source")
                    type_ = obj.get("type")
                    content = obj.get("content", "")
                    if source == "USER_EXPLICIT" and type_ == "USER_INPUT":
                        if "mejora" in content.lower() or "20" in content.lower() or "list" in content.lower():
                            print(f"User (Line {line_num}): {content.strip()}")
                            print("-" * 40)
                    elif source == "MODEL" and type_ == "PLANNER_RESPONSE":
                        if "mejora" in content.lower() or "20" in content.lower():
                            # check if it looks like a list
                            print(f"Model (Line {line_num}): {content[:1500].strip()}")
                            print("-" * 40)
                except Exception:
                    pass
        print("=" * 80)
