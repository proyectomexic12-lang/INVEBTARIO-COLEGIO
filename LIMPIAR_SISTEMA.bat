@echo off
color 0c
echo =======================================================
echo    ADVERTENCIA: MODO PRUEBAS
echo =======================================================
echo.
echo Esto va a BORRAR TODOS LOS INVENTARIOS (Guaimaral, Cuatro Bocas, etc).
echo Asegurate de que el programa de inventario este CERRADO.
echo.
pause
echo.
echo Borrando base de datos...
cd /d "%~dp0desktop_app"
.\venv\Scripts\python.exe borrar_todo_modo_pruebas.py
echo.
pause
