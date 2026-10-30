@echo off
rem Cria o atalho "AutoReda" (duplo clique abre o menu). O atalho aponta para esta pasta,
rem entao pode ficar na Area de Trabalho ou em qualquer outra pasta.
rem   Duplo clique                          -> cria na Area de Trabalho
rem   Criar atalho AutoReda.bat "C:\pasta"  -> cria na pasta indicada
rem Se mover a pasta do projeto, rode de novo para refazer o atalho.
set "PASTA_DESTINO=%~1"
set "AUTOREDA_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$d=$env:PASTA_DESTINO; if(-not $d){$d=[Environment]::GetFolderPath('Desktop')}; if(-not (Test-Path -LiteralPath $d -PathType Container)){Write-Host ('Pasta nao existe: '+$d); exit 1}; $p=$env:AUTOREDA_DIR.TrimEnd('\'); $s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $d 'AutoReda.lnk')); $s.TargetPath=(Join-Path $p 'AutoReda.bat'); $s.WorkingDirectory=$p; $s.IconLocation=$env:SystemRoot+'\System32\shell32.dll,13'; $s.Description='Abre a automacao de redacoes'; $s.Save(); Write-Host ('Atalho criado: '+(Join-Path $d 'AutoReda.lnk'))"
echo.
pause
