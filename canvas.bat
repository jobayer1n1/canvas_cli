@echo off
if "%~1"=="" (
    python "%~dp0canvas.py"
    goto :eof
)

:run_command
python "%~dp0canvas.py" %*
