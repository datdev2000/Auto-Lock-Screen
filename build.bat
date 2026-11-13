@echo off
cd /d "%~dp0"
python -m PyInstaller --noconfirm --clean --onefile --windowed --name AutoLockScreen main.py
if errorlevel 1 (
  echo Build that bai.
  pause
  exit /b 1
)
echo.
echo Da tao: dist\AutoLockScreen.exe
echo Double-click file do de chay — khong can CMD, khong hien console.
pause
