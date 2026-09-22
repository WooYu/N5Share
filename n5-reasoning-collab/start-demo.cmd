@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-demo.ps1" %*
if errorlevel 1 (
  echo.
  echo N5 could not start. Follow the diagnostic above, then run start-demo.cmd again.
  pause
  exit /b 1
)
exit /b 0
