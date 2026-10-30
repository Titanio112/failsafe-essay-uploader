@echo off
rem AutoReda: duplo clique abre o menu da automacao. Roda de qualquer pasta
rem (entra na pasta deste arquivo). NAO copie este arquivo para outro lugar:
rem para ter na Area de Trabalho use "Criar atalho AutoReda.bat".
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist "main.py" (
  echo Este arquivo foi copiado para fora da pasta do projeto.
  echo Apague a copia e use o atalho: duplo clique em "Criar atalho AutoReda.bat".
  goto fim
)
where python >nul 2>nul
if %errorlevel%==0 (
  python main.py %*
  goto fim
)
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 main.py %*
  goto fim
)
echo Python nao encontrado. Instale em python.org e marque "Add python.exe to PATH".
:fim
echo.
pause
