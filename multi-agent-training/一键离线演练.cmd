@echo off
chcp 65001 >nul
cd /d "%~dp0"
node -e "process.exit(Number(process.versions.node.split('.')[0]) >= 22 ? 0 : 1)" >nul 2>nul
if errorlevel 1 (
  echo ERROR: Node.js 22 or newer is required.
  pause
  exit /b 1
)
for %%M in (sequential supervisor hierarchical swarm network devteam security) do (
  node run.mjs --mode %%M
  if errorlevel 1 goto failed
)
node --test tests.mjs
if errorlevel 1 goto failed
echo Completed. Reports are in the outputs folder. Devteam is paused before tester.
pause
exit /b 0
:failed
echo ERROR: A lab or test failed. See the message above.
pause
exit /b 1
