@echo off
if "%~1"=="" (
    python "%~dp0canvas.py"
    goto :eof
)

if /I "%~1"=="-scwd" goto :switch_cwd
if /I "%~1"=="--switch-current-working-directory" goto :switch_cwd

:run_command
python "%~dp0canvas.py" %*
goto :eof

:switch_cwd
for /f "usebackq delims=" %%i in (`python "%~dp0canvas.py" --switch-current-working-directory`) do set "CANVAS_SYNC_DIR=%%i"
if not defined CANVAS_SYNC_DIR goto :eof
if not exist "%CANVAS_SYNC_DIR%" mkdir "%CANVAS_SYNC_DIR%"
cd /d "%CANVAS_SYNC_DIR%"
goto :eof
