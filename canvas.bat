@echo off
if not "%~1"=="" goto run_command

set "CANVAS_DIR="
for /f "usebackq delims=" %%D in (`python "%~dp0canvas.py" --print-canvas-dir`) do set "CANVAS_DIR=%%D"

if not defined CANVAS_DIR (
    echo set your sync folder
    goto :eof
)

cd /d "%CANVAS_DIR%" 2>nul
if errorlevel 1 (
    echo set your sync folder
    goto :eof
)

echo moved cwd to Canvas/ directory

goto :eof

:run_command
python "%~dp0canvas.py" %*
