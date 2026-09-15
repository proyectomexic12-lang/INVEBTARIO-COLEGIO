@echo off
title Sistema de Inventario - Nexus
cd /d "%~dp0desktop_app"
echo Iniciando aplicacion de inventario...
venv\Scripts\python.exe main.py
if errorlevel 1 (
    echo.
    echo Ocurrio un error al ejecutar la aplicacion.
    pause
)
