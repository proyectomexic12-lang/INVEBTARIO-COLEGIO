import os

target = r"C:\Users\USUARIO\.gemini\antigravity-ide\brain\5bb11621-e64d-4ccf-9848-ba8d0abd3a04"
for root, dirs, files in os.walk(target):
    for f in files:
        print(os.path.join(root, f))
