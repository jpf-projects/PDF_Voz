@echo off
setlocal
cd /d "%~dp0.."
chcp 65001 >nul
set PYTHONUTF8=1
if not exist ".venv\Scripts\python.exe" goto missing
".venv\Scripts\python.exe" -c "import pypdf" >nul 2>nul
if not errorlevel 1 goto run
echo Ferramenta opcional: execute INSTALAR.bat --ferramentas e tente novamente.
pause
exit /b 1
:run
".venv\Scripts\python.exe" -m ferramentas.testar_voz %*
set "result=%errorlevel%"
pause
exit /b %result%
:missing
echo Execute primeiro INSTALAR.bat.
pause
exit /b 1
