@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
set ORT_DISABLE_TELEMETRY=1
if not exist ".venv\Scripts\python.exe" goto missing
".venv\Scripts\python.exe" leitor_pdf.py
if errorlevel 1 pause
exit /b
:missing
echo Execute primeiro 4_ATUALIZAR_LEITOR.bat.
pause
