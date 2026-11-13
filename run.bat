@echo off
cd /d "%~dp0"
if exist "dist\AutoLockScreen.exe" (
  start "" "dist\AutoLockScreen.exe"
  exit /b 0
)
where pythonw >nul 2>&1
if %ERRORLEVEL%==0 (
  start "" pythonw main.py
  exit /b 0
)
where python >nul 2>&1
if %ERRORLEVEL%==0 (
  start "" pythonw main.py 2>nul || start "" python main.py
  exit /b 0
)
echo Chua co AutoLockScreen.exe. Chay build.bat truoc, hoac cai Python.
pause
exit /b 1
