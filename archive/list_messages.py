import os
path = r"C:\Users\USUARIO\.gemini\antigravity-ide\brain\5bb11621-e64d-4ccf-9848-ba8d0abd3a04\.system_generated\messages"
if os.path.exists(path):
    print("Files in messages:")
    for f in os.listdir(path):
        print(f" - {f} (size: {os.path.getsize(os.path.join(path, f))} bytes)")
else:
    print("Directory does not exist:", path)
