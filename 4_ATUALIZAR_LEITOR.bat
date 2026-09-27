@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
where py >nul 2>nul
if errorlevel 1 goto python
py instalar_leitor.py
goto end
:python
python instalar_leitor.py
:end
pause
