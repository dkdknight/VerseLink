@echo off
REM Lancer le backend dans une nouvelle fenêtre
start cmd /k "cd /d backend && python server.py"
echo Backend lancé.
timeout /t 3 /nobreak >nul

REM Lancer le frontend (build) dans une nouvelle fenêtre
start cmd /k "cd /d frontend && npm run build"
echo Frontend lancé.

REM Lancer le bot Discord dans une nouvelle fenêtre
start cmd /k "cd /d discord_bot && python bot.py"
echo Bot Discord lancé.

echo Tous les services sont démarrés !
pause
