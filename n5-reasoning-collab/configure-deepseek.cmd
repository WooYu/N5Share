@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
if exist "%~dp0.venv\Scripts\python.exe" goto local_python
python "%~dp0server\configure_key.py"
goto finished
:local_python
"%~dp0.venv\Scripts\python.exe" "%~dp0server\configure_key.py"
:finished
set "N5_CONFIG_EXIT=%ERRORLEVEL%"
if not "%N5_CONFIG_EXIT%"=="0" echo 配置未完成，可检查提示后重新运行。
pause
exit /b %N5_CONFIG_EXIT%
