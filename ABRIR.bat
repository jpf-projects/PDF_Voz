@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
set ORT_DISABLE_TELEMETRY=1
if not exist ".venv\Scripts\python.exe" goto missing
".venv\Scripts\python.exe" leitor_pdf.py
set "result=%errorlevel%"
if not "%result%"=="0" pause
exit /b %result%
:missing
echo Execute primeiro INSTALAR.bat.
pause
exit /b 1
