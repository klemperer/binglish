@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] venv not found. Run: python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt pyinstaller
  exit /b 1
)

echo Building binglish.exe ...
.venv\Scripts\pyinstaller.exe --noconfirm --onefile --windowed ^
  --name binglish ^
  --icon assets\binglish.ico ^
  --add-data "assets\binglish.ico;." ^
  --paths . ^
  --hidden-import "pystray._win32" ^
  binglish\app.py

if errorlevel 1 (
  echo Build FAILED
  exit /b 1
)

echo.
echo Output: %~dp0dist\binglish.exe
powershell -NoProfile -Command "Get-FileHash '%~dp0dist\binglish.exe' -Algorithm SHA256 | Format-List"
endlocal
