@echo off
chcp 65001 >nul
title SGC Laboratorio Clinico
echo ============================================
echo  Sistema de Gestion de Calidad - Lab. Clinico
echo ============================================
echo.
echo Iniciando la aplicacion...
echo Se abrira en: http://localhost:8501
echo Para detener: presione Ctrl+C en esta ventana.
echo.
cd /d "%~dp0"
"C:\Users\Jordán\AppData\Local\Programs\Python\Python312\python.exe" -m streamlit run app.py
pause
