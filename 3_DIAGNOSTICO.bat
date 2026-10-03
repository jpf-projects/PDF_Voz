@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
if not exist ".venv\Scripts\python.exe" goto missing
".venv\Scripts\python.exe" -m leitor.diagnostics
goto finish
:missing
echo Execute primeiro 1_INSTALAR.bat.
:finish
pause
