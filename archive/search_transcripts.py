import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

brain_dir = r"C:\Users\USUARIO\.gemini\antigravity-ide\brain"
for root, dirs, files in os.walk(brain_dir):
    for file in files:
        if file.endswith(".md"):
            full_path = os.path.join(root, file)
            print(f"File: {full_path} (size: {os.path.getsize(full_path)} bytes)")
            # Print first 20 lines of the file to see the content
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [f.readline().strip() for _ in range(30)]
                    print("--- First lines ---")
                    for l in lines:
                        if l:
                            print("  ", l[:120])
                    print("=" * 60)
            except Exception as e:
                print(f"Error reading {full_path}: {e}")
