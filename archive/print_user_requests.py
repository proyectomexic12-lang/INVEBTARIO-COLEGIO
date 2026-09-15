import os
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

folders = [
    "5bb11621-e64d-4ccf-9848-ba8d0abd3a04",
    "9b39c5a4-52ca-409d-9c80-89f0fe025bf6",
    "d15d68b3-1086-46e1-9500-69018b647f5f"
]

brain_dir = r"C:\Users\USUARIO\.gemini\antigravity-ide\brain"
for folder in folders:
    folder_path = os.path.join(brain_dir, folder)
    log_file = os.path.join(folder_path, ".system_generated", "logs", "transcript.jsonl")
    if os.path.exists(log_file):
        print(f"\n=======================================================")
        print(f"FOLDER: {folder}")
        print(f"=======================================================")
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            count = 1
            for line in f:
                try:
                    obj = json.loads(line)
                    if obj.get("source") == "USER_EXPLICIT" and obj.get("type") == "USER_INPUT":
                        content = obj.get("content", "")
                        # strip additional metadata to make it compact
                        if "<USER_REQUEST>" in content:
                            req = content.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0].strip()
                        else:
                            req = content.strip()
                        print(f"Request {count}: {req}")
                        count += 1
                except Exception:
                    pass
