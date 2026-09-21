@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
set LANGSMITH_TRACING=false
set LANGCHAIN_TRACING_V2=false
set LANGGRAPH_CLI_NO_ANALYTICS=1
if exist "..\.venv\Scripts\langgraph.exe" (
  "..\.venv\Scripts\langgraph.exe" dev --no-reload --host 127.0.0.1 --port 2024 --n-jobs-per-worker 1
) else if exist ".venv\Scripts\langgraph.exe" (
  ".venv\Scripts\langgraph.exe" dev --no-reload --host 127.0.0.1 --port 2024 --n-jobs-per-worker 1
) else (
  echo Install Studio dependencies first:
  echo python -m pip install -r requirements-studio.txt
)
pause
