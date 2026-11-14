@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt -q
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name AutoLockScreen ^
  --icon assets\lock.ico ^
  --add-data "assets\lock.ico;assets" ^
  --add-data "assets\lock.png;assets" ^
  --hidden-import=pystray._win32 ^
  --hidden-import=autolock.app ^
  --hidden-import=autolock.config ^
  --hidden-import=autolock.idle ^
  --hidden-import=autolock.startup ^
  --hidden-import=autolock.icons ^
  --hidden-import=autolock.warning ^
  --hidden-import=autolock.paths ^
  --hidden-import=autolock.instance ^
  --hidden-import=autolock.power ^
  --collect-all pystray ^
  main.py
if errorlevel 1 (
  echo Build that bai.
  pause
  exit /b 1
)
echo.
echo Da tao: dist\AutoLockScreen.exe
echo Icon: assets\lock.ico ^| Data: %%ProgramData%%\AutoLockScreen\
pause
