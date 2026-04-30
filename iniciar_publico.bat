@echo off
chcp 65001 >nul
cd /d "%~dp0"
title SGC Laboratorio - Acceso Publico

echo ================================================
echo   SGC Laboratorio Clinico - Acceso Publico
echo ================================================
echo.
echo Iniciando sistema...

set PYTHON="C:\Users\Jordán\AppData\Local\Programs\Python\Python312\python.exe"
set NGROK="C:\Users\Jordán\AppData\Local\ngrok\ngrok.exe"

:: Iniciar Streamlit en segundo plano
start /B %PYTHON% -m streamlit run app.py --server.port 8501 --server.headless true

echo Esperando que el sistema arranque...
timeout /t 8 /nobreak >nul

:: Iniciar ngrok con dominio permanente
start /B %NGROK% http 8501 --domain=fever-angriness-kilogram.ngrok-free.dev

timeout /t 4 /nobreak >nul

echo.
echo ================================================
echo   SISTEMA LISTO - Enlace publico permanente:
echo.
echo   https://fever-angriness-kilogram.ngrok-free.dev
echo.
echo   Accesible desde cualquier WiFi o celular
echo ================================================
echo.
echo IMPORTANTE: No cierre esta ventana mientras use el sistema.
echo Para detener el acceso publico: cierre esta ventana.
echo.
pause
