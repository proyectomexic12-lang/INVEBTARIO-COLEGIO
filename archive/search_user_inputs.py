import os
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

brain_dir = r"C:\Users\USUARIO\.gemini\antigravity-ide\brain"
for folder in os.listdir(brain_dir):
    folder_path = os.path.join(brain_dir, folder)
    if not os.path.isdir(folder_path):
        continue
    log_file = os.path.join(folder_path, ".system_generated", "logs", "transcript.jsonl")
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        obj = json.loads(line)
                        if obj.get("source") == "USER_EXPLICIT" and obj.get("type") == "USER_INPUT":
                            content = obj.get("content", "")
                            content_lower = content.lower()
                            if "mejora" in content_lower or "20" in content_lower or "list" in content_lower or "tarea" in content_lower:
                                print(f"=== USER INPUT in {folder} (Line {line_num}) ===")
                                print(content.strip())
                                print("-" * 60)
                        elif obj.get("source") == "MODEL" and obj.get("type") == "PLANNER_RESPONSE":
                            # check if model prints a list of improvements
                            content = obj.get("content", "")
                            content_lower = content.lower()
                            if "mejoras" in content_lower and "20" in content_lower:
                                print(f"=== MODEL RESPONSE in {folder} (Line {line_num}) ===")
                                print(content[:1000].strip())
                                print("-" * 60)
                    except Exception:
                        pass
        except Exception as e:
            print(f"Error reading {log_file}: {e}")
