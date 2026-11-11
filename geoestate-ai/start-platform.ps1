$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPython = Join-Path (Split-Path -Parent $projectRoot) '.venv\Scripts\python.exe'
$frontendDirectory = Join-Path $projectRoot 'frontend'
$logsDirectory = Join-Path $projectRoot 'logs'

if (-not (Test-Path $backendPython)) {
  $backendPython = Join-Path $projectRoot 'venv\Scripts\python.exe'
}
if (-not (Test-Path $backendPython)) {
  throw "Python environment not found at $backendPython. Install the project requirements first."
}
if (-not (Test-Path (Join-Path $frontendDirectory 'node_modules'))) {
  throw "Frontend packages are missing from $frontendDirectory. Run npm install there first."
}

New-Item -ItemType Directory -Path $logsDirectory -Force | Out-Null

function Test-LocalEndpoint {
  param([string]$Uri)
  try {
    $null = Invoke-WebRequest -Uri $Uri -TimeoutSec 2 -UseBasicParsing
    return $true
  } catch {
    return $false
  }
}

if (-not (Test-LocalEndpoint 'http://127.0.0.1:8000/api/health')) {
  # Prevent BLAS from creating one worker per reported CPU core. On memory-
  # constrained Windows machines this can fail the API during NumPy startup.
  $previousBlasThreads = $env:OPENBLAS_NUM_THREADS
  $previousOmpThreads = $env:OMP_NUM_THREADS
  $previousMklThreads = $env:MKL_NUM_THREADS
  $env:OPENBLAS_NUM_THREADS = '1'
  $env:OMP_NUM_THREADS = '1'
  $env:MKL_NUM_THREADS = '1'
  Start-Process -FilePath $backendPython `
    -ArgumentList '-m uvicorn backend.main:app --host 0.0.0.0 --port 8000' `
    -WorkingDirectory $projectRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $logsDirectory 'backend.log') `
    -RedirectStandardError (Join-Path $logsDirectory 'backend-error.log')
  $env:OPENBLAS_NUM_THREADS = $previousBlasThreads
  $env:OMP_NUM_THREADS = $previousOmpThreads
  $env:MKL_NUM_THREADS = $previousMklThreads

  # Ensure Backend API is ready before starting Frontend so proxy never gets ECONNREFUSED
  for ($attempt = 0; $attempt -lt 40; $attempt++) {
    if (Test-LocalEndpoint 'http://127.0.0.1:8000/api/health') {
      break
    }
    Start-Sleep -Milliseconds 500
  }
}

if (-not (Test-LocalEndpoint 'http://127.0.0.1:5175/')) {
  Start-Process -FilePath 'cmd.exe' `
    -ArgumentList '/c npm run dev -- --host 0.0.0.0 --port 5175' `
    -WorkingDirectory $frontendDirectory `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $logsDirectory 'frontend.log') `
    -RedirectStandardError (Join-Path $logsDirectory 'frontend-error.log')
}

foreach ($check in @(
  @{ Name = 'Backend API'; Uri = 'http://127.0.0.1:8000/api/health' },
  @{ Name = 'Frontend'; Uri = 'http://127.0.0.1:5175/' }
)) {
  $ready = $false
  for ($attempt = 0; $attempt -lt 30; $attempt++) {
    if (Test-LocalEndpoint $check.Uri) {
      $ready = $true
      break
    }
    Start-Sleep -Seconds 1
  }
  if (-not $ready) {
    throw "$($check.Name) did not start. Check the logs in $logsDirectory."
  }
  Write-Output "$($check.Name) is ready: $($check.Uri)"
}

Write-Output 'Open http://127.0.0.1:5175/ to use MakaanX.'
