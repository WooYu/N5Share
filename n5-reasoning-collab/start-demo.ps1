param([switch]$CheckOnly)

$ErrorActionPreference = 'Stop'
$courseRoot = $PSScriptRoot
$courseUrl = 'http://127.0.0.1:8775'

function Get-CourseHealth {
    try {
        $response = Invoke-WebRequest -Uri ($courseUrl + '/api/health') -UseBasicParsing -TimeoutSec 2
        $health = $response.Content | ConvertFrom-Json
        if ($response.Headers['Server'] -like 'N5Local/*' -and $health.model -eq 'deepseek-flash') {
            return $health
        }
    } catch { }
    return $null
}

function Test-CoursePort {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $connect = $client.BeginConnect('127.0.0.1', 8775, $null, $null)
        if ($connect.AsyncWaitHandle.WaitOne(300)) {
            $client.EndConnect($connect)
            return $true
        }
        return $false
    } catch { return $false } finally { $client.Dispose() }
}

function Find-CoursePython {
    $localPython = Join-Path $courseRoot '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $localPython -PathType Leaf) { return $localPython }

    $candidates = @()
    if ($env:N5_PYTHON) { $candidates += $env:N5_PYTHON }
    foreach ($name in @('python.exe', 'python3.exe')) {
        $command = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue
        if ($command) { $candidates += $command.Source }
    }
    $launcher = Get-Command py.exe -CommandType Application -ErrorAction SilentlyContinue
    if ($launcher) {
        try {
            $resolved = & $launcher.Source -3 -c 'import sys; print(sys.executable)' 2>$null
            if ($LASTEXITCODE -eq 0) { $candidates += [string]$resolved }
        } catch { }
    }
    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if (!(Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
        try {
            & $candidate -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>$null
            if ($LASTEXITCODE -eq 0) { return $candidate }
        } catch { }
    }
    throw 'Python 3.11+ was not found. Install Python, or set N5_PYTHON to its full python.exe path.'
}

function Open-Course($health) {
    Write-Host ('N5: ' + $courseUrl)
    if (!$health.available) {
        Write-Host 'The course is available. Live model mode is disabled; see the reason shown in the browser.'
    }
    if (!$CheckOnly) { Start-Process -FilePath $courseUrl }
}

$startupLock = $null
$lockHeld = $false
try {
    # Serialize double-clicks: a second launcher reuses the first service.
    $startupLock = New-Object System.Threading.Mutex($false, 'Local\N5ReasoningCollab8775Startup')
    $lockHeld = $startupLock.WaitOne(15000)
    if (!$lockHeld) { throw 'Another N5 launcher is still starting. Wait a moment, then try again.' }

    $health = Get-CourseHealth
    if ($null -ne $health) {
        Write-Host 'Reusing the running N5 service.'
        Open-Course $health
        exit 0
    }
    if (Test-CoursePort) {
        throw 'Port 8775 is in use by a different or unresponsive service. Close that service before starting N5; no duplicate service was started.'
    }

    $coursePython = Find-CoursePython
    & $coursePython -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'
    if ($LASTEXITCODE -ne 0) { throw ('Python 3.11+ is required: ' + $coursePython) }
    & $coursePython -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('httpx') else 1)"
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Install the missing dependency with this exact PowerShell command:'
        Write-Host ('& "' + $coursePython + '" -m pip install -r "' + (Join-Path $courseRoot 'server\requirements.txt') + '"')
        throw 'httpx is missing. Nothing was installed automatically.'
    }
    Write-Host ('Python ready: ' + $coursePython)
    if ($CheckOnly) {
        Write-Host 'Startup checks passed. No service or browser was started.'
        exit 0
    }

    $logDir = Join-Path ([System.IO.Path]::GetTempPath()) 'N5-reasoning-collab'
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    $logTag = [System.Guid]::NewGuid().ToString('N')
    $stderrLog = Join-Path $logDir ($logTag + '.stderr.log')
    $stdoutLog = Join-Path $logDir ($logTag + '.stdout.log')
    $serverScript = Join-Path $courseRoot 'server\app.py'
    $service = Start-Process -FilePath $coursePython -ArgumentList @('-u', ('"' + $serverScript + '"'), '--port', '8775') -WorkingDirectory $courseRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog

    $readyBy = [DateTime]::UtcNow.AddSeconds(15)
    do {
        $health = Get-CourseHealth
        if ($null -ne $health) {
            Write-Host ('Service started. Logs: ' + $logDir)
            Open-Course $health
            exit 0
        }
        if ($service.HasExited) { throw ('N5 service exited before becoming ready. Diagnostic log: ' + $stderrLog) }
        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $readyBy)
    if (!$service.HasExited) { Stop-Process -Id $service.Id -ErrorAction SilentlyContinue }
    throw ('N5 did not become ready within 15 seconds. Diagnostic log: ' + $stderrLog)
} catch {
    Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
} finally {
    if ($lockHeld) { $startupLock.ReleaseMutex() }
    if ($startupLock) { $startupLock.Dispose() }
}
