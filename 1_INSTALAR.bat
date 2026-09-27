@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
where py >nul 2>nul
if errorlevel 1 goto usepython
py bootstrap.py
goto finish
:usepython
python bootstrap.py
:finish
if errorlevel 1 echo A instalacao nao terminou. Leia a mensagem acima.
pause
