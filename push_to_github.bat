@echo off
setlocal

cd /d "%~dp0"

set "GIT_EXE=C:\Program Files\Git\mingw64\bin\git.exe"
if not exist "%GIT_EXE%" (
  echo Git for Windows was not found at:
  echo %GIT_EXE%
  echo.
  echo Please install Git for Windows, then run this file again.
  pause
  exit /b 1
)

"%GIT_EXE%" status --short
echo.
echo Pushing this project to:
"%GIT_EXE%" remote -v
echo.

"%GIT_EXE%" push -u origin main
if errorlevel 1 (
  echo.
  echo Push failed. If GitHub login appears, finish the login and run this file again.
  pause
  exit /b 1
)

echo.
echo Done. The project was pushed to GitHub.
pause

