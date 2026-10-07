# Run from PowerShell with uv installed. Uses a temporary drive to keep old SDK builds under Windows path limits.
param([string]$UvCommand = 'uv')
$ErrorActionPreference = 'Stop'
$devWorkspace = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$devUv = (Get-Command $UvCommand -ErrorAction Stop).Source
$devDrive = @('R', 'S', 'T', 'U', 'V', 'W') | Where-Object { -not (Get-PSDrive -Name $_ -ErrorAction SilentlyContinue) } | Select-Object -First 1
if (-not $devDrive) { throw 'No free temporary drive letter is available.' }
& subst.exe "${devDrive}:" $devWorkspace
if ($LASTEXITCODE -ne 0) { throw 'Could not create the temporary project path mapping.' }
try {
    $devShortRoot = "${devDrive}:/"
    $devPython = "${devShortRoot}.venv-metagpt/Scripts/python.exe"
    $devCache = "${devShortRoot}test-results/uv-cache"
    if (-not (Test-Path -LiteralPath $devPython)) {
        & $devUv --cache-dir $devCache venv "${devShortRoot}.venv-metagpt" --python 3.11
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python 3.11 environment.' }
    }
    & $devUv --cache-dir $devCache pip install --python $devPython --no-deps metagpt==0.8.2
    if ($LASTEXITCODE -ne 0) { throw 'Could not install the MetaGPT package.' }
    & $devUv --cache-dir $devCache pip install --python $devPython -r "${devShortRoot}demo/dev_team/requirements-core.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Could not install the case-study dependencies.' }
    Write-Host 'Environment ready. In VS Code, select the development-team Review launch configuration and press F5.'
} finally {
    & subst.exe "${devDrive}:" /d
}
