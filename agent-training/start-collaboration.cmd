@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  set "demoPython=.venv\Scripts\python.exe"
  goto ready
)
echo 请先创建虚拟环境并安装依赖：
echo py -3 -m venv .venv
echo .venv\Scripts\python.exe -m pip install -r requirements.txt
exit /b 1
:ready
"%demoPython%" -c "import langgraph, httpx" >nul 2>nul
if errorlevel 1 (
  echo 缺少依赖，请执行 .venv\Scripts\python.exe -m pip install -r requirements.txt
  exit /b 1
)
"%demoPython%" demo\run_collaboration.py %*
exit /b %errorlevel%
