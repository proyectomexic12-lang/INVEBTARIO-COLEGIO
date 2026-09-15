@echo off
echo Compilando Control de Inventario I.E. Guaimaral...
.\venv\Scripts\pyinstaller.exe --noconfirm --onedir --windowed --add-data "C:\Users\Janus\Desktop\inventario\desktop_app\venv\Lib\site-packages\customtkinter;customtkinter/" --add-data "components;components/" --name "Control_Inventario_IE_Guaimaral" main.py
echo Compilacion terminada. El ejecutable esta en la carpeta 'dist'.
pause
