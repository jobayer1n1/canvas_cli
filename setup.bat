@echo off
setlocal

cd /d "%~dp0"
set "CANVAS_CLI_DIR=%~dp0"

echo.
echo ============================================================
echo [1/3] Checking Python
echo ============================================================
where python >nul 2>&1
if errorlevel 1 (
    echo Python was not found on PATH.
    echo Install Python from https://www.python.org/downloads/
    echo Make sure ^"Add Python to PATH^" is selected during installation.
    echo.
    pause
    exit /b 1
)
for /f "delims=" %%V in ('python --version 2^>^&1') do echo %%V

echo.
echo ============================================================
echo [2/3] Installing Python packages
echo ============================================================
python -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo Failed to install Python packages.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [3/3] Adding canvas-cli to the user PATH
echo ============================================================
powershell -NoProfile -ExecutionPolicy Bypass -Command "$dir = [IO.Path]::GetFullPath($env:CANVAS_CLI_DIR); $userPath = [Environment]::GetEnvironmentVariable('Path', 'User'); $entries = @($userPath -split ';' | Where-Object { $_ -and $_.Trim() }); if (-not ($entries | Where-Object { [IO.Path]::GetFullPath($_.TrimEnd('\')) -ieq $dir.TrimEnd('\') })) { [Environment]::SetEnvironmentVariable('Path', (($entries + $dir) -join ';'), 'User'); Write-Host ('Added: ' + $dir) } else { Write-Host ('Already present: ' + $dir) }"
if errorlevel 1 (
    echo Failed to update the user PATH.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Setup complete!
echo ============================================================
echo Open a new terminal, then run: canvas --help
echo ============================================================
pause
endlocal
