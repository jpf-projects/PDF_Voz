@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
where py >nul 2>nul
if errorlevel 1 goto usepython
py instalar.py %*
goto finish
:usepython
python instalar.py %*
:finish
set "result=%errorlevel%"
if not "%result%"=="0" echo A instalacao nao terminou. Leia a mensagem acima.
pause
exit /b %result%
