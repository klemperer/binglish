@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] venv not found. Run: py -3 -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt pyinstaller
  exit /b 1
)

rem Warn if project path contains non-ASCII (PyInstaller may fail with WinError 5)
.venv\Scripts\python.exe -c "import sys; p=sys.argv[1]; bad=any(ord(c)>127 for c in p); print('PATH='+p); sys.exit(2 if bad else 0)" "%cd%" 2>nul
if errorlevel 2 (
  echo [WARN] Project path contains non-ASCII characters.
  echo        PyInstaller may fail with PermissionError WinError 5.
  echo        Prefer copying the repo to e.g. C:\binglish-build and build there.
)

.venv\Scripts\python.exe -c "import tkinter, sys; print('build with', sys.version.split()[0], 'tk', tkinter.TkVersion)"
if errorlevel 1 (
  echo [ERROR] This venv Python has no tkinter. Recreate: py -3 -m venv .venv
  exit /b 1
)

echo Building binglish.exe ...
if exist ".venv\Scripts\pyinstaller.exe" (
  .venv\Scripts\pyinstaller.exe --noconfirm --onefile --windowed ^
    --name binglish ^
    --icon assets\binglish.ico ^
    --add-data "assets\binglish.ico;." ^
    --paths . ^
    --hidden-import "pystray._win32" ^
    binglish\app.py
) else (
  .venv\Scripts\python.exe -m PyInstaller --noconfirm --onefile --windowed ^
    --name binglish ^
    --icon assets\binglish.ico ^
    --add-data "assets\binglish.ico;." ^
    --paths . ^
    --hidden-import "pystray._win32" ^
    binglish\app.py
)

if errorlevel 1 (
  echo Build FAILED
  echo If you see PermissionError WinError 5, rebuild from a pure-ASCII path. See README.
  exit /b 1
)

echo.
echo Output: %~dp0dist\binglish.exe
powershell -NoProfile -Command "Get-FileHash '%~dp0dist\binglish.exe' -Algorithm SHA256 | Format-List"
endlocal
