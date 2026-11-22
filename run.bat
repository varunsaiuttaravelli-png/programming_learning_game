@echo off
setlocal

cd /d "%~dp0"

echo ========================================================
echo    CodeQuest - Programming Learning Game Launcher
echo ========================================================
echo.

set "PYTHON="
if exist "%LocalAppData%\Programs\Python\Launcher\py.exe" (
    set "PYTHON=%LocalAppData%\Programs\Python\Launcher\py.exe -3.12"
)

if not defined PYTHON (
    if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
        set "PYTHON="%LocalAppData%\Programs\Python\Python312\python.exe""
    )
)

if not defined PYTHON (
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PYTHON=py -3.12"
)
)

if not defined PYTHON (
    where python >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set "PYTHON=python"
    )
)

if not defined PYTHON (
    echo [ERROR] Python was not found.
    echo Install Python 3.12 from https://www.python.org/downloads/
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Creating virtual environment...
    %PYTHON% -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Could not create the virtual environment.
        pause
        exit /b 1
    )
)

echo [INFO] Installing dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
)

echo [INFO] Starting CodeQuest...
".venv\Scripts\python.exe" app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] The application stopped with an error.
    pause
)
